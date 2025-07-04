"""Nodes for the product retrieval agent."""

import os
from typing import Literal, TypedDict
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState
from langchain_core.runnables.config import RunnableConfig
from .tools import AVAILABLE_TOOLS
from .whatsapp_formatter import format_response_for_platform

# Maximum number of retries before giving up
MAX_RETRIES = 3

# Initialize the chat model
response_model = init_chat_model("openai:gpt-4o-mini", temperature=0)


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


def generate_answer(state: EnhancedMessagesState, config: RunnableConfig = None):
    """Generate an answer based on the product information."""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    
    try:
        response = response_model.invoke([{"role": "user", "content": prompt}])
        
        # Apply WhatsApp formatting if source is WhatsApp
        if config:
            source = config.get("configurable", {}).get("source", "general")
            if source == "whatsapp" and hasattr(response, 'content') and response.content:
                formatted_content = format_response_for_platform(response.content, "whatsapp")
                # Create a new message with formatted content
                from langchain_core.messages import AIMessage
                response = AIMessage(content=formatted_content)
        
        return {
            "messages": [response],
            "retry_count": 0  # Reset retry count on successful completion
        }
    except Exception as e:
        print(f"Error in generate_answer: {e}")
        fallback_response = "I apologize, but I encountered an error while generating a response. Please try asking your question again."
        return {
            "messages": [{"role": "assistant", "content": fallback_response}],
            "retry_count": 0
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


def generate_fallback(state: EnhancedMessagesState, config: RunnableConfig = None):
    """Generate a fallback response when retrieval consistently fails."""
    question = state["messages"][0].content
    fallback_content = FALLBACK_PROMPT.format(question=question)
    
    # Apply WhatsApp formatting if source is WhatsApp
    if config:
        source = config.get("configurable", {}).get("source", "general")
        if source == "whatsapp":
            fallback_content = format_response_for_platform(fallback_content, "whatsapp")
    
    return {
        "messages": [{"role": "assistant", "content": fallback_content}],
        "retry_count": 0  # Reset retry count for future queries
    } 