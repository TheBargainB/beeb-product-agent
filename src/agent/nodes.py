"""Nodes for the product retrieval agent."""

import os
from typing import Literal, TypedDict
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState
from langchain_core.runnables.config import RunnableConfig
from .tools import AVAILABLE_TOOLS
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List, Optional, Union
import json
import logging
from datetime import datetime
from langgraph.prebuilt import ToolNode

from .memory_tools import (
    SupabaseMemoryManager
)
from .guard_rails import GuardRails
from .config import AgentConfig
from .memory_schemas import (
    AssistantLanguageConfig,
    LANGUAGE_CONFIGS,
    get_language_instructions
)

# Define ConversationState type for enhanced memory functions
class ConversationState(MessagesState):
    """Extended MessagesState with additional fields for conversation management."""
    tool_calls: List[Any] = []
    last_response: str = ""
    conversation_complete: bool = False

# Maximum number of retries before giving up
MAX_RETRIES = 3

# Initialize the chat model
response_model = init_chat_model("openai:gpt-4o-mini", temperature=0)

logger = logging.getLogger(__name__)

# Enhanced system message with memory context and flexible language configuration
ENHANCED_SYSTEM_MESSAGE = """{platform_formatting_instructions}

You are a helpful assistant named {instance_name} for {customer_name}.

{language_instructions}

🎯 **Your Role:**
You are a personalized assistant that remembers information about users and provides helpful, contextual responses.

🛠️ **Your Capabilities:**
1. **Memory Management**: Remember user information, preferences, and past conversations
2. **Personalized Responses**: Use stored memories to provide relevant, personalized assistance
3. **Language Flexibility**: Adapt to user's language preferences and cultural context
4. **Contextual Awareness**: Consider past interactions and user preferences

📊 **Current User Context:**
{user_context}

📝 **Memory Context:**
{memory_context}

🎯 **Instructions:**
1. **Be Personal**: Use the user's memory context to provide personalized responses
2. **Remember Information**: When users share personal info, preferences, or important details, consider updating memory
3. **Be Contextual**: Reference past conversations and user preferences when relevant
4. **Adapt Communication**: Match the user's preferred communication style and language preferences
5. **Offer Continuity**: Build on previous conversations and remember ongoing topics

**Memory Update Decision Rules:**
- 🧑‍💼 Personal information (name, location, job, family) → update profile
- 💭 Preferences, interests, experiences, goals → save as user memory
- 💬 Important conversation topics or requests → save as conversation memory
- ⚙️ User instructions for how I should behave → update assistant instructions

**Response Style:**
- Be friendly and conversational
- Use the user's preferred communication style
- Reference relevant memories when helpful
- Keep responses concise but informative (max {max_response_length} chars)
- Respect cultural and language preferences"""

def get_platform_formatting_instructions(source: str) -> str:
    """Get platform-specific formatting instructions."""
    if source == "whatsapp":
        return """
🚨 **CRITICAL WHATSAPP FORMATTING - MUST FOLLOW EXACTLY:**

❌ **ABSOLUTELY FORBIDDEN - DO NOT USE:**
- ## Headers or ### Subheaders 
- **Double asterisk bold**
- __Double underscore__
- `Code blocks`
- [Links](url)
- > Blockquotes
- --- Dividers

✅ **REQUIRED WHATSAPP FORMAT:**
- Headers: Use emojis + *single asterisk bold*
- Bold text: *text* (single asterisks only)
- Lists: • bullet points (never use - or *)
- Line breaks: Use normal line breaks

✅ **EXACT EXAMPLES TO FOLLOW:**
❌ Wrong: "## Healthy Pasta Recipe"
✅ Correct: "🍝 *Healthy Pasta Recipe*"

❌ Wrong: "### Ingredients:"
✅ Correct: "🥘 *Ingredients*:"

❌ Wrong: "**200g pasta**"
✅ Correct: "*200g pasta*"

❌ Wrong: "- 2 cups flour"
✅ Correct: "• 2 cups flour"

❌ Wrong: "### Instructions:"
✅ Correct: "👨‍🍳 *Instructions*:"

🎯 **EMOJI GUIDE FOR HEADERS:**
- 🍽️ Recipe names
- 🥘 Ingredients sections  
- 👨‍🍳 Instructions/Steps
- 🛒 Shopping/Grocery lists
- 💰 Prices/Budget info
- 📅 Meal planning
- 💡 Tips/Suggestions

⚠️ **THIS IS MANDATORY - NO EXCEPTIONS. ANY MARKDOWN USAGE WILL BREAK WHATSAPP DISPLAY.**"""
    elif source == "telegram":
        return """
💬 **TELEGRAM FORMATTING:**
- You can use full markdown formatting (Telegram supports it)
- Use **bold**, *italic*, `code`, [links](url), etc. freely"""
    else:
        return """
🌐 **GENERAL FORMATTING:**
- Use standard markdown formatting
- **Bold text**, *italic text*, # Headers, ## Subheaders are all fine"""

def load_assistant_language_config(config: RunnableConfig) -> AssistantLanguageConfig:
    """Load assistant language configuration from config."""
    configurable = config.get("configurable", {})
    
    # Check if language config is provided
    language_config = configurable.get("language_config")
    if language_config:
        return AssistantLanguageConfig(**language_config)
    
    # Check for individual language settings
    target_language = configurable.get("target_language", "english")
    enforcement_mode = configurable.get("enforcement_mode", "flexible")
    
    # Use predefined config if available
    if target_language in LANGUAGE_CONFIGS:
        base_config = LANGUAGE_CONFIGS[target_language]
        return AssistantLanguageConfig(
            primary_language=target_language,
            language_enforcement=enforcement_mode,
            **base_config
        )
    
    # Default fallback
    return AssistantLanguageConfig(
        primary_language=target_language,
        language_enforcement=enforcement_mode,
        fallback_language="english",
        cultural_context=f"Communicate in {target_language} with appropriate cultural context."
    )

# Enhanced state with retry tracking
class EnhancedMessagesState(MessagesState):
    """Extended MessagesState with retry tracking to prevent infinite loops."""
    retry_count: int = 0


def generate_query_or_respond(state: EnhancedMessagesState):
    """
    Call the model to generate a response based on the current state. 
    Given the question, it will decide to retrieve using the product tools, 
    or simply respond to the user.
    """
    response = (
        response_model
        .bind_tools(AVAILABLE_TOOLS)
        .invoke(state["messages"])
    )
    return {"messages": [response]}


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")


def grade_documents(
    state: EnhancedMessagesState,
) -> Literal["generate_answer", "rewrite_question", "generate_fallback"]:
    """
    Determines whether the retrieved documents are relevant to the question.
    If any document is not relevant, we will set a flag to run web search.
    """
    print("📊 Checking document relevance...")
    
    # Get current retry count
    retry_count = state.get('retry_count', 0)
    
    # Check if we've exceeded max retries
    if retry_count >= MAX_RETRIES:
        print(f"⚠️  Max retries ({MAX_RETRIES}) exceeded. Generating fallback response.")
        return "generate_fallback"
    
    # Get question and documents
    question = state["messages"][0].content
    documents = state["messages"][-1].content
    
    # Grade documents
    GRADE_PROMPT = (
        "You are a grader assessing the relevance of a retrieved document to a user question. "
        "Here is the retrieved document: \n\n {document} \n\n"
        "Here is the user question: {question} \n"
        "If the document contains keywords related to the user question, grade it as relevant. "
        "It does not need to be a stringent test. The goal is to filter out erroneous retrievals. "
        "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."
    )
    
    grader_model = response_model.with_structured_output(GradeDocuments)
    
    try:
        prompt = GRADE_PROMPT.format(document=documents, question=question)
        response = (
            grader_model
            .with_structured_output(GradeDocuments)
            .invoke([{"role": "user", "content": prompt}])
        )
        score = response.binary_score

        if score == "yes":
            # Reset retry count on successful retrieval
            return "generate_answer"
        else:
            # Increment retry count for irrelevant results
            new_retry_count = retry_count + 1
            
            if new_retry_count >= MAX_RETRIES:
                return "generate_fallback"
            else:
                return "rewrite_question"
                
    except Exception as e:
        print(f"Error in grade_documents: {e}")
        new_retry_count = retry_count + 1
        
        if new_retry_count >= MAX_RETRIES:
            return "generate_fallback"
        else:
            return "rewrite_question"


REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "The user is asking about products, brands, categories, prices, or specifications.\n"
    "\n⚠️ IMPORTANT: The product database contains items in Dutch, so if the user searches in English, try Dutch terms:\n"
    "- 'dairy' → try 'zuivel' \n"
    "- 'milk' → try 'melk'\n"
    "- 'cheese' → try 'kaas'\n"
    "- 'bread' → try 'brood'\n"
    "- 'meat' → try 'vlees'\n"
    "- 'drinks/beverages' → try 'dranken'\n"
    "- 'chocolate' → try 'chocolade'\n"
    "- 'cookies' → try 'koekjes'\n"
    "- 'organic' → try 'biologisch'\n"
    "- 'baby food' → try 'babyvoeding'\n"
    "\nHere is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question using Dutch product terms if the original was in English, or try more specific product names:"
)


def rewrite_question(state: EnhancedMessagesState):
    """Rewrite the original user question to better match product data."""
    messages = state["messages"]
    question = messages[0].content
    retry_count = state.get('retry_count', 0)
    
    # Increment retry count
    new_retry_count = retry_count + 1
    
    prompt = REWRITE_PROMPT.format(question=question)
    
    try:
        response = response_model.invoke([{"role": "user", "content": prompt}])
        return {
            "messages": [{"role": "user", "content": response.content}],
            "retry_count": new_retry_count
        }
    except Exception as e:
        print(f"Error in rewrite_question: {e}")
        # Return original question if rewrite fails
        return {
            "messages": [{"role": "user", "content": question}],
            "retry_count": new_retry_count
        }


GENERATE_PROMPT = (
    "You are an assistant for product-related questions. "
    "Use the following retrieved product information to answer the question. "
    "If you don't know the answer based on the product information provided, just say that you don't know. "
    "Be helpful and provide specific details about products, prices, brands, categories, and specifications when available. "
    "Keep the answer clear and concise.\n"
    "Question: {question} \n"
    "Product Information: {context}"
)


def generate_answer(state: ConversationState, config: RunnableConfig) -> Dict[str, Any]:
    """Generate a response using the chat model with tools, memory, and language configuration."""
    try:
        # Get the enhanced model with tools
        enhanced_model = response_model.bind_tools(AVAILABLE_TOOLS, parallel_tool_calls=False)
        
        # Get agent configuration
        agent_config = AgentConfig.from_config(config)
        
        # Get user information
        user_id = agent_config.get_user_id()
        instance_name = agent_config.get_instance_name()
        customer_name = agent_config.get_customer_name()
        max_response_length = agent_config.get_max_response_length()
        
        # Simplified context - for now just use basic information
        user_context = f"User ID: {user_id}"
        memory_context = "No specific memory context available"
        
        # Load language configuration
        language_config = load_assistant_language_config(config)
        language_instructions = get_language_instructions(language_config)
        
        # Get platform formatting instructions
        source = config.get("configurable", {}).get("source", "general")
        platform_formatting_instructions = get_platform_formatting_instructions(source)
        
        # Generate system message with all context
        system_message = ENHANCED_SYSTEM_MESSAGE.format(
            instance_name=instance_name,
            customer_name=customer_name,
            language_instructions=language_instructions,
            user_context=user_context,
            memory_context=memory_context,
            platform_formatting_instructions=platform_formatting_instructions,
            max_response_length=max_response_length
        )
        
        # Create the message chain
        messages = [SystemMessage(content=system_message)] + state["messages"]
        
        # Make the LLM call
        response = enhanced_model.invoke(messages)
        
        # Process any tool calls
        if response.tool_calls:
            return {
                "messages": [response],
                "tool_calls": response.tool_calls,
                "last_response": response.content if response.content else "",
                "conversation_complete": False
            }
        
        # No tool calls, conversation is complete
        return {
            "messages": [response],
            "tool_calls": [],
            "last_response": response.content,
            "conversation_complete": True
        }
        
    except Exception as e:
        logger.error(f"Error in generate_answer: {str(e)}")
        return {
            "messages": [],
            "tool_calls": [],
            "last_response": f"I apologize, but I encountered an error: {str(e)}",
            "conversation_complete": True
        }


FALLBACK_PROMPT = (
    "I apologize, but I was unable to find relevant product information for your question. "
    "This could be because:\n"
    "- The specific products you're asking about are not in our database\n"
    "- The search terms might need to be more specific\n"
    "- There might be a temporary issue with the product database\n\n"
    "Here's your original question: {question}\n\n"
    "💡 **Search Tips** - Our database contains Dutch products, so try:\n"
    "🇬🇧 **English** → 🇳🇱 **Dutch** translations:\n"
    "- 'dairy products' → 'zuivel producten'\n"
    "- 'milk' → 'melk'\n"
    "- 'beverages/drinks' → 'dranken'\n"
    "- 'chocolate' → 'chocolade'\n"
    "- 'bread' → 'brood'\n"
    "- 'meat' → 'vlees'\n"
    "- 'organic' → 'biologisch'\n\n"
    "Or try searching by:\n"
    "- Specific brand names (like 'AH', 'Mona', 'Nivea')\n"
    "- Product categories in Dutch\n"
    "- More general terms\n\n"
    "Is there anything else I can help you with?"
)


def generate_fallback(state: ConversationState, config: RunnableConfig) -> Dict[str, Any]:
    """Generate a fallback response when search fails."""
    try:
        # Get agent configuration
        agent_config = AgentConfig.from_config(config)
        
        # Get user information
        user_id = agent_config.get_user_id()
        instance_name = agent_config.get_instance_name()
        customer_name = agent_config.get_customer_name()
        max_response_length = agent_config.get_max_response_length()
        
        # Simplified context - for now just use basic information
        user_context = f"User ID: {user_id}"
        memory_context = "No specific memory context available"
        
        # Load language configuration
        language_config = load_assistant_language_config(config)
        language_instructions = get_language_instructions(language_config)
        
        # Get platform formatting instructions
        source = config.get("configurable", {}).get("source", "general")
        platform_formatting_instructions = get_platform_formatting_instructions(source)
        
        # Generate system message with all context
        system_message = ENHANCED_SYSTEM_MESSAGE.format(
            instance_name=instance_name,
            customer_name=customer_name,
            language_instructions=language_instructions,
            user_context=user_context,
            memory_context=memory_context,
            platform_formatting_instructions=platform_formatting_instructions,
            max_response_length=max_response_length
        )
        
        # Create the message chain
        messages = [SystemMessage(content=system_message)] + state["messages"]
        
        # Make the LLM call
        response = response_model.invoke(messages)
        
        return {
            "messages": [response],
            "tool_calls": [],
            "last_response": response.content,
            "conversation_complete": True
        }
        
    except Exception as e:
        logger.error(f"Error in generate_fallback: {str(e)}")
        return {
            "messages": [],
            "tool_calls": [],
            "last_response": "I apologize, but I'm having trouble processing your request right now. Please try again later.",
            "conversation_complete": True
        } 