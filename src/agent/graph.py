"""Main graph definition for the product retrieval agent with enhanced memory capabilities and flexible language configuration."""

import os
import time
import uuid
from typing import Literal, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from trustcall import create_extractor
from pydantic import BaseModel, Field

from .nodes import (
    generate_query_or_respond,
    grade_documents,
    rewrite_question,
    generate_answer,
    generate_fallback,
    EnhancedMessagesState,
    get_platform_formatting_instructions,
    load_assistant_language_config,
    ENHANCED_SYSTEM_MESSAGE
)
from .tools import AVAILABLE_TOOLS, get_tools
from .memory_tools import SupabaseMemoryManager, UpdateMemory, get_memory_manager
from .memory_schemas import (
    UserMemory, 
    UserProfile, 
    ConversationMemory, 
    AssistantInstructions,
    AssistantLanguageConfig,
    MemoryCollection,
    LANGUAGE_CONFIGS,
    get_language_instructions
)
from .config import get_config
from .guard_rails import (
    get_guard_rails, 
    RateLimitExceeded, 
    ContentSafetyViolation, 
    CostLimitExceeded
)


# Import the LLM
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage


def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = [
        "OPENAI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    print("✅ Environment validation passed")


class EnhancedMemoryManager:
    """Enhanced memory manager that combines Supabase storage with in-memory LangGraph store for comprehensive memory management."""
    
    def __init__(self, model, supabase_client, memory_store, customer_profile_id=None):
        self.model = model
        self.supabase_client = supabase_client
        self.memory_store = memory_store
        self.customer_profile_id = customer_profile_id
        
        # Create Trustcall extractors for different memory types
        self.user_memory_extractor = create_extractor(
            model,
            tools=[UserMemory],
            tool_choice="UserMemory",
            enable_inserts=True
        )
        
        self.profile_extractor = create_extractor(
            model,
            tools=[UserProfile],
            tool_choice="UserProfile"
        )
        
        self.conversation_extractor = create_extractor(
            model,
            tools=[ConversationMemory],
            tool_choice="ConversationMemory",
            enable_inserts=True
        )
        
        self.instructions_extractor = create_extractor(
            model,
            tools=[AssistantInstructions],
            tool_choice="AssistantInstructions"
        )
    
    def get_user_memories(self, user_id: str, limit: int = 10) -> List[UserMemory]:
        """Get user memories from the store."""
        namespace = ("user_memories", user_id)
        memories = self.memory_store.search(namespace)
        
        # Sort by importance and last referenced
        sorted_memories = sorted(memories, 
                               key=lambda m: (m.value.get('importance', 'medium'), 
                                            m.value.get('last_referenced', '')), 
                               reverse=True)
        
        return [UserMemory(**mem.value) for mem in sorted_memories[:limit]]
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from the store."""
        namespace = ("user_profile", user_id)
        profile = self.memory_store.get(namespace, "profile")
        
        if profile:
            return UserProfile(**profile.value)
        return None
    
    def get_conversation_memories(self, user_id: str, limit: int = 5) -> List[ConversationMemory]:
        """Get recent conversation memories."""
        namespace = ("conversation_memories", user_id)
        memories = self.memory_store.search(namespace)
        
        # Sort by date
        sorted_memories = sorted(memories, 
                               key=lambda m: m.value.get('date', ''), 
                               reverse=True)
        
        return [ConversationMemory(**mem.value) for mem in sorted_memories[:limit]]
    
    def get_assistant_instructions(self, user_id: str) -> Optional[AssistantInstructions]:
        """Get assistant instructions for this user."""
        namespace = ("assistant_instructions", user_id)
        instructions = self.memory_store.get(namespace, "instructions")
        
        if instructions:
            return AssistantInstructions(**instructions.value)
        return None
    
    def save_user_memory(self, user_id: str, memory: UserMemory):
        """Save a user memory to the store."""
        namespace = ("user_memories", user_id)
        key = str(uuid.uuid4())
        self.memory_store.put(namespace, key, memory.model_dump())
    
    def save_user_profile(self, user_id: str, profile: UserProfile):
        """Save user profile to the store."""
        namespace = ("user_profile", user_id)
        self.memory_store.put(namespace, "profile", profile.model_dump())
    
    def save_conversation_memory(self, user_id: str, memory: ConversationMemory):
        """Save conversation memory to the store."""
        namespace = ("conversation_memories", user_id)
        key = str(uuid.uuid4())
        self.memory_store.put(namespace, key, memory.model_dump())
    
    def save_assistant_instructions(self, user_id: str, instructions: AssistantInstructions):
        """Save assistant instructions to the store."""
        namespace = ("assistant_instructions", user_id)
        self.memory_store.put(namespace, "instructions", instructions.model_dump())
    
    def format_memory_context(self, user_id: str) -> str:
        """Format all memory context for the model."""
        context_parts = []
        
        # Get user profile
        profile = self.get_user_profile(user_id)
        if profile:
            context_parts.append("**USER PROFILE:**")
            if profile.name:
                context_parts.append(f"• Name: {profile.name}")
            if profile.location:
                context_parts.append(f"• Location: {profile.location}")
            if profile.occupation:
                context_parts.append(f"• Occupation: {profile.occupation}")
            if profile.family_status:
                context_parts.append(f"• Family: {profile.family_status}")
            if profile.interests:
                context_parts.append(f"• Interests: {', '.join(profile.interests)}")
            if profile.communication_style:
                context_parts.append(f"• Communication Style: {profile.communication_style}")
            context_parts.append("")
        
        # Get user memories
        memories = self.get_user_memories(user_id)
        if memories:
            context_parts.append("**KEY MEMORIES:**")
            for memory in memories:
                importance_indicator = "🔥" if memory.importance == "high" else "📌" if memory.importance == "medium" else "💡"
                context_parts.append(f"• {importance_indicator} {memory.content}")
            context_parts.append("")
        
        # Get recent conversations
        conversations = self.get_conversation_memories(user_id)
        if conversations:
            context_parts.append("**RECENT CONVERSATIONS:**")
            for conv in conversations:
                context_parts.append(f"• {conv.topic}: {', '.join(conv.key_points[:2])}")
            context_parts.append("")
        
        return "\n".join(context_parts) if context_parts else "No memory context available."


def create_enhanced_agent_graph():
    """Create the enhanced agent graph with comprehensive memory capabilities and flexible language configuration."""
    # Validate environment
    validate_environment()
    
    # Get configuration
    config = get_config()
    print(config.get_config_summary())
    
    # Import here to avoid circular imports
    from langchain_openai import ChatOpenAI
    from .supabase_client import SupabaseClient
    
    # Initialize the model and supabase client
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    supabase_client = SupabaseClient()
    
    # Create memory store for enhanced memory management
    memory_store = InMemoryStore()
    
    def get_memory_manager(config: RunnableConfig) -> SupabaseMemoryManager:
        """Get memory manager with customer profile ID from runtime config."""
        # Extract customer profile ID from configurable parameters
        customer_profile_id = config.get("configurable", {}).get("customer_profile_id")
        return SupabaseMemoryManager(model, supabase_client, customer_profile_id)
    
    def get_enhanced_memory_manager(config: RunnableConfig) -> EnhancedMemoryManager:
        """Get enhanced memory manager with comprehensive memory capabilities."""
        customer_profile_id = config.get("configurable", {}).get("customer_profile_id")
        return EnhancedMemoryManager(model, supabase_client, memory_store, customer_profile_id)
    
    # Enhanced system message with memory context and flexible language configuration
    ENHANCED_SYSTEM_MESSAGE = """You are a helpful assistant named {instance_name} for {customer_name}.

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

{platform_formatting_instructions}

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



    def enhanced_generate_query_or_respond(state: EnhancedMessagesState, config: RunnableConfig):
        """Enhanced query generation with comprehensive memory context and flexible language configuration."""
        start_time = time.time()
        guard_rails = get_guard_rails()
        
        try:
            # Extract user ID from config
            user_id = config.get("configurable", {}).get("user_id", "anonymous")
            
            # Get the last user message for guard rails validation
            last_user_message = None
            for msg in reversed(state["messages"]):
                if hasattr(msg, 'type') and msg.type == 'human':
                    last_user_message = msg.content
                    break
            
            # Apply guard rails if we have a user message
            if last_user_message:
                # Check rate limits
                guard_rails.check_rate_limits(user_id)
                
                # Validate and sanitize input content
                sanitized_message = guard_rails.validate_input_content(last_user_message, user_id)
                
                # Update the message in state if it was sanitized
                if sanitized_message != last_user_message:
                    # Replace the last human message with sanitized version
                    for i, msg in enumerate(state["messages"]):
                        if hasattr(msg, 'type') and msg.type == 'human' and msg.content == last_user_message:
                            state["messages"][i] = HumanMessage(content=sanitized_message)
                            break
            
            # Get user context from traditional memory manager
            memory_manager = get_memory_manager(config)
            user_context = memory_manager.format_user_context()
            
            # Get enhanced memory context
            enhanced_memory_manager = get_enhanced_memory_manager(config)
            memory_context = enhanced_memory_manager.format_memory_context(user_id)
            
            # Get the agent config
            agent_config = get_config()
            
            # Load language configuration
            language_config = load_assistant_language_config(config)
            language_instructions = get_language_instructions(language_config)
            
            # Get platform formatting instructions
            source = config.get("configurable", {}).get("source", "general")
            platform_formatting_instructions = get_platform_formatting_instructions(source)
            
            # Generate system message with all context
            system_message = ENHANCED_SYSTEM_MESSAGE.format(
                instance_name=agent_config.get_instance_name(),
                customer_name=agent_config.get_customer_name(),
                language_instructions=language_instructions,
                user_context=user_context,
                memory_context=memory_context,
                platform_formatting_instructions=platform_formatting_instructions,
                max_response_length=agent_config.get_max_response_length()
            )
            
            # Decision tool for memory updates
            class UpdateMemoryDecision(BaseModel):
                """Decision on what type of memory to update."""
                should_update: bool = Field(description="Whether any memory should be updated")
                update_type: Literal["profile", "user_memory", "conversation", "instructions"] = Field(
                    description="Type of memory to update"
                )
                reason: str = Field(description="Reason for the update decision")
            
            # Bind tools including memory update decision
            all_tools = AVAILABLE_TOOLS + [UpdateMemoryDecision]
            enhanced_model = model.bind_tools(all_tools, parallel_tool_calls=False)
            
            # Make the LLM call
            response = enhanced_model.invoke([SystemMessage(content=system_message)] + state["messages"])
            
            # Check cost limits based on token usage
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens_used = response.usage_metadata.get('total_tokens', 0)
                guard_rails.check_cost_limits(user_id, tokens_used=tokens_used, tool_calls=len(response.tool_calls) if response.tool_calls else 0)
            

            
            # Store the enhanced memory manager in state for later use
            state["enhanced_memory_manager"] = enhanced_memory_manager
            
            return {
                "messages": [response],
                "retry_count": 0,
                "enhanced_memory_manager": enhanced_memory_manager
            }
            
        except (RateLimitExceeded, ContentSafetyViolation, CostLimitExceeded) as e:
            # Return error message for guard rail violations
            error_response = {
                "role": "assistant",
                "content": f"I apologize, but I cannot process your request at this time. {str(e)}"
            }
            return {
                "messages": [error_response],
                "retry_count": 0
            }
        except Exception as e:
            print(f"Error in enhanced_generate_query_or_respond: {e}")
            return {
                "messages": [{"role": "assistant", "content": "I apologize, but I encountered an error. Please try again."}],
                "retry_count": 0
            }

    def update_user_memory(state: EnhancedMessagesState, config: RunnableConfig):
        """Update user memory based on the conversation."""
        user_id = config.get("configurable", {}).get("user_id", "anonymous")
        enhanced_memory_manager = state.get("enhanced_memory_manager") or get_enhanced_memory_manager(config)
        
        try:
            # Extract memory type from tool call
            last_message = state["messages"][-1]
            if not last_message.tool_calls:
                return state
            
            tool_call = last_message.tool_calls[0]
            update_type = tool_call['args']['update_type']
            
            # Prepare messages for Trustcall
            conversation_messages = [msg for msg in state["messages"] if not hasattr(msg, 'tool_calls')]
            
            if update_type == "profile":
                # Update user profile
                existing_profile = enhanced_memory_manager.get_user_profile(user_id)
                existing_data = existing_profile.model_dump() if existing_profile else {}
                
                result = enhanced_memory_manager.profile_extractor.invoke({
                    "messages": conversation_messages,
                    "existing": {"UserProfile": existing_data} if existing_data else None
                })
                
                if result["responses"]:
                    enhanced_memory_manager.save_user_profile(user_id, result["responses"][0])
                
            elif update_type == "user_memory":
                # Save user memory
                result = enhanced_memory_manager.user_memory_extractor.invoke({
                    "messages": conversation_messages
                })
                
                if result["responses"]:
                    for memory in result["responses"]:
                        enhanced_memory_manager.save_user_memory(user_id, memory)
            
            elif update_type == "conversation":
                # Save conversation memory
                result = enhanced_memory_manager.conversation_extractor.invoke({
                    "messages": conversation_messages
                })
                
                if result["responses"]:
                    for memory in result["responses"]:
                        enhanced_memory_manager.save_conversation_memory(user_id, memory)
            
            elif update_type == "instructions":
                # Update assistant instructions
                existing_instructions = enhanced_memory_manager.get_assistant_instructions(user_id)
                existing_data = existing_instructions.model_dump() if existing_instructions else {}
                
                result = enhanced_memory_manager.instructions_extractor.invoke({
                    "messages": conversation_messages,
                    "existing": {"AssistantInstructions": existing_data} if existing_data else None
                })
                
                if result["responses"]:
                    enhanced_memory_manager.save_assistant_instructions(user_id, result["responses"][0])
            
            # Return tool response
            return {
                "messages": [{"role": "tool", "content": f"Memory updated successfully", "tool_call_id": tool_call['id']}]
            }
            
        except Exception as e:
            print(f"Error updating memory: {e}")
            return {
                "messages": [{"role": "tool", "content": f"Error updating memory: {str(e)}", "tool_call_id": tool_call['id']}]
            }

    # Create the graph
    workflow = StateGraph(EnhancedMessagesState)
    
    # Add nodes
    workflow.add_node("enhanced_generate_query_or_respond", enhanced_generate_query_or_respond)
    workflow.add_node("update_memory", update_user_memory)
    workflow.add_node("tools", ToolNode(AVAILABLE_TOOLS))
    
    # Add edges
    workflow.add_edge(START, "enhanced_generate_query_or_respond")
    
    def route_after_generation(state: EnhancedMessagesState):
        """Route after query generation based on tool calls."""
        last_message = state["messages"][-1]
        
        if not last_message.tool_calls:
            return END
        
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call['name']
        
        if tool_name == "UpdateMemoryDecision":
            return "update_memory"
        else:
            return "tools"
    
    workflow.add_conditional_edges("enhanced_generate_query_or_respond", route_after_generation)
    workflow.add_edge("update_memory", "enhanced_generate_query_or_respond")
    workflow.add_edge("tools", "enhanced_generate_query_or_respond")
    
    # Compile with checkpointer
    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer, store=memory_store)
    
    print("✅ Enhanced agent graph created successfully with comprehensive memory management")
    return graph


def create_local_test_graph():
    """Create a simplified graph for local testing."""
    print("🧪 Creating local test graph...")
    
    # Validate environment
    try:
        validate_environment()
    except ValueError as e:
        print(f"⚠️  Environment validation failed: {e}")
        print("🔧 Please set up your environment variables before running locally")
        return None
    
    return create_enhanced_agent_graph()


def run_agent_locally(question: str, user_id: str = "test-user", verbose: bool = True):
    """Run the agent locally for testing."""
    print(f"\n🤖 BargainB Agent - Local Test")
    print(f"{'='*50}")
    
    # Create the graph
    graph = create_local_test_graph()
    if not graph:
        return "Failed to create graph - check environment setup"
    
    # Configure for local testing
    config = {
        "configurable": {
            "thread_id": f"local-test-{user_id}",
            "user_id": user_id
        }
    }
    
    try:
        if verbose:
            print(f"💭 Question: {question}")
            print(f"👤 User ID: {user_id}")
            print(f"🔧 Running with local configuration...")
            print("-" * 50)
        
        # Run the graph
        result = graph.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config=config
        )
        
        # Extract the final response
        final_response = result["messages"][-1].content
        
        if verbose:
            print(f"🎯 Response: {final_response}")
            print("=" * 50)
        
        return final_response
        
    except Exception as e:
        error_msg = f"❌ Error running agent: {e}"
        if verbose:
            print(error_msg)
        return error_msg


# Keep the original functions for backwards compatibility
def create_agent_graph():
    """Alias for backwards compatibility."""
    return create_enhanced_agent_graph()


def create_original_graph():
    """Create the original graph without memory capabilities."""
    # Import here to avoid circular imports
    from langchain_openai import ChatOpenAI
    
    # Initialize the model
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create the state graph
    builder = StateGraph(EnhancedMessagesState)
    
    # Add nodes
    builder.add_node("generate_query_or_respond", generate_query_or_respond)
    builder.add_node("product_search", ToolNode(AVAILABLE_TOOLS))
    builder.add_node("rewrite_question", rewrite_question)
    builder.add_node("generate_answer", generate_answer)
    builder.add_node("generate_fallback", generate_fallback)
    
    # Add edges
    builder.add_edge(START, "generate_query_or_respond")
    builder.add_conditional_edges(
        "generate_query_or_respond",
        lambda state: "product_search" if state["messages"][-1].tool_calls else END,
        {"product_search": "product_search", END: END}
    )
    
    # Product search conditional edges
    builder.add_conditional_edges(
        "product_search",
        grade_documents,
        {
            "generate_answer": "generate_answer",
            "rewrite_question": "rewrite_question", 
            "generate_fallback": "generate_fallback"
        }
    )
    
    builder.add_edge("rewrite_question", "generate_query_or_respond")
    builder.add_edge("generate_answer", END)
    builder.add_edge("generate_fallback", END)
    
    # Compile
    graph = builder.compile()
    
    return graph


def run_agent(question: str, verbose: bool = True):
    """Run the original agent without memory."""
    graph = create_original_graph()
    
    result = graph.invoke({"messages": [{"role": "user", "content": question}]})
    
    final_response = result["messages"][-1].content
    
    if verbose:
        print(f"Question: {question}")
        print(f"Response: {final_response}")
    
    return final_response


def create_graph():
    """Simple function to create the default graph."""
    return create_enhanced_agent_graph()


if __name__ == "__main__":
    # Example usage
    test_query = "What products do you have in the dairy category?"
    print("Query:", test_query)
    print("Response:", run_agent(test_query)) 