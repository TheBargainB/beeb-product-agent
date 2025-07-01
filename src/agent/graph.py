"""Main graph definition for the product retrieval agent with Supabase memory capabilities and guard rails."""

import os
import time
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage

from .nodes import (
    generate_query_or_respond,
    grade_documents,
    rewrite_question,
    generate_answer,
    generate_fallback,
    EnhancedMessagesState
)
from .tools import AVAILABLE_TOOLS
from .memory_tools import SupabaseMemoryManager, UpdateMemory
from .config import get_config
from .guard_rails import (
    get_guard_rails, 
    RateLimitExceeded, 
    ContentSafetyViolation, 
    CostLimitExceeded
)


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


def create_enhanced_agent_graph():
    """Create the enhanced agent graph with Supabase memory capabilities."""
    # Validate environment
    validate_environment()
    
    # Get configuration
    config = get_config()
    print(config.get_config_summary())
    
    # Import here to avoid circular imports
    from langchain_openai import ChatOpenAI
    from .supabase_client import SupabaseClient
    
    # Initialize the model, supabase client, and memory manager
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    supabase_client = SupabaseClient()
    memory_manager = SupabaseMemoryManager(model, supabase_client)
    
    # Enhanced system message with memory context
    ENHANCED_SYSTEM_MESSAGE = """You are a helpful grocery and meal planning assistant for {customer_name}.

🎯 **Your Role:**
You help with grocery shopping, meal planning, budget tracking, and product recommendations using real Dutch supermarket data.

🛠️ **Your Capabilities:**
1. **Product Search**: Search products from Albert Heijn, Jumbo, and Dirk with real prices
2. **Memory Management**: Remember user preferences, grocery lists, meal plans, and budgets
3. **Personalized Recommendations**: Suggest products based on dietary restrictions and preferences
4. **Price Comparison**: Compare prices across different stores
5. **Smart Shopping**: Create and manage grocery lists with cost estimates

📊 **Current User Context:**
{user_context}

🎯 **Instructions:**
1. **Be Personal**: Use the user's context to provide personalized recommendations
2. **Consider Constraints**: Always respect dietary restrictions, allergies, and budget limits
3. **Be Practical**: Provide actionable advice with specific products and stores
4. **Save Information**: When users mention personal info, grocery items, meal plans, or budgets, update memory appropriately
5. **Compare Prices**: When showing products, include prices from multiple stores when available
6. **Be Helpful**: Suggest alternatives, recipes, and money-saving tips

**Memory Update Decision Rules:**
- 🧑‍💼 Personal information (name, preferences, allergies, diet) → update profile
- 🛒 Grocery items, shopping lists, specific products → update grocery_list  
- 🍽️ Meal planning, recipes, cooking plans → update meal_plan
- 💰 Budget amounts, spending limits, financial goals → update budget

**Response Style:**
- Be friendly and conversational
- Use emojis to make responses engaging
- Include practical tips and suggestions
- Always mention store names and prices when relevant
- Keep responses concise but informative (max {max_response_length} chars)"""

    def enhanced_generate_query_or_respond(state: EnhancedMessagesState, config: RunnableConfig):
        """Enhanced query generation with memory context, routing decisions, and guard rails."""
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
            
            # Get user context from memory manager
            user_context = memory_manager.format_user_context()
            
            # Get the agent config (not the RunnableConfig)
            agent_config = get_config()
            
            # Format system message with user context and config
            system_msg = ENHANCED_SYSTEM_MESSAGE.format(
                customer_name=agent_config.get_customer_name(),
                user_context=user_context,
                max_response_length=agent_config.get_max_response_length()
            )
            
            # Bind both product search tools and memory update tool
            all_tools = AVAILABLE_TOOLS + [UpdateMemory]
            enhanced_model = model.bind_tools(all_tools, parallel_tool_calls=False)
            
            # Make the LLM call
            response = enhanced_model.invoke([SystemMessage(content=system_msg)] + state["messages"])
            
            # Check cost limits based on token usage
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens_used = response.usage_metadata.get('total_tokens', 0)
                guard_rails.check_cost_limits(user_id, tokens_used=tokens_used, tool_calls=len(response.tool_calls) if response.tool_calls else 0)
            
            # Record response time
            response_time = (time.time() - start_time) * 1000
            guard_rails.record_response_time(response_time)
            
            return {"messages": [response]}
            
        except (RateLimitExceeded, ContentSafetyViolation, CostLimitExceeded) as e:
            guard_rails.record_error(user_id, e)
            
            # Return appropriate fallback response
            if isinstance(e, RateLimitExceeded):
                fallback = guard_rails.get_fallback_response('rate_limit')
            elif isinstance(e, ContentSafetyViolation):
                fallback = guard_rails.get_fallback_response('content_safety')
            elif isinstance(e, CostLimitExceeded):
                fallback = guard_rails.get_fallback_response('cost_limit')
            else:
                fallback = guard_rails.get_fallback_response('general_error')
            
            # Return fallback as AI message
            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage(content=fallback)]}
            
        except Exception as e:
            guard_rails.record_error(user_id, e)
            
            # If graceful degradation is enabled, return fallback
            if agent_config.is_graceful_degradation_enabled():
                fallback = guard_rails.get_fallback_response('general_error')
                from langchain_core.messages import AIMessage
                return {"messages": [AIMessage(content=fallback)]}
            
            # Otherwise re-raise the exception
            raise

    def route_decision(state: EnhancedMessagesState, config: RunnableConfig) -> Literal["product_search", "update_memory", "respond_directly"]:
        """Route based on the tool calls made by the model."""
        message = state['messages'][-1]
        
        if not message.tool_calls:
            return "respond_directly"
        
        tool_call = message.tool_calls[0]
        tool_name = tool_call['name']
        
        if tool_name == "UpdateMemory":
            return "update_memory"
        elif tool_name in ["search_products", "get_product_by_gtin", "search_products_by_category", "search_products_by_brand"]:
            return "product_search"
        else:
            return "respond_directly"

    def update_memory_node(state: EnhancedMessagesState, config: RunnableConfig):
        """Update user memory based on the memory type specified."""
        tool_call = state['messages'][-1].tool_calls[0]
        update_type = tool_call['args']['update_type']
        
        # Route to appropriate memory update function
        if update_type == 'profile':
            result = memory_manager.update_profile_memory(state["messages"])
        elif update_type == 'grocery_list':
            result = memory_manager.update_grocery_memory(state["messages"])
        elif update_type == 'meal_plan':
            result = memory_manager.update_meal_memory(state["messages"])
        elif update_type == 'budget':
            result = memory_manager.update_budget_memory(state["messages"])
        else:
            result = f"Unknown memory update type: {update_type}"
        
        # Return tool response
        tool_response = {
            "role": "tool",
            "content": result,
            "tool_call_id": tool_call['id']
        }
        
        return {"messages": [tool_response]}

    def respond_directly(state: EnhancedMessagesState, config: RunnableConfig):
        """Handle direct responses when no tools are called."""
        return state

    def final_response(state: EnhancedMessagesState, config: RunnableConfig):
        """Generate final response with updated memory context and comprehensive communication validation."""
        guard_rails = get_guard_rails()
        user_id = config.get("configurable", {}).get("user_id", "anonymous")
        
        try:
            # Get updated user context
            user_context = memory_manager.format_user_context()
            
            # Get the original user query for compliance checking
            user_query = ""
            for msg in state["messages"]:
                if hasattr(msg, 'type') and msg.type == 'human':
                    user_query = msg.content
                    break
            
            # Create response based on the last interaction
            last_message = state["messages"][-1]
            
            # Enhanced system message with communication guidelines
            system_guidelines = """
COMMUNICATION GUIDELINES:
- Maintain a friendly, helpful tone while being professional
- Focus on grocery shopping, meal planning, and product recommendations
- Always cite store names when mentioning prices (Albert Heijn, Jumbo, Dirk)
- Provide actionable, specific advice
- Respect dietary restrictions and cultural preferences
- Be honest about limitations - don't provide medical, financial, or legal advice
- Include appropriate disclaimers for prices and availability
- Keep responses concise but informative
- Use positive, encouraging language
"""
            
            # Check if the last message is a tool message
            from langchain_core.messages import ToolMessage
            if isinstance(last_message, ToolMessage):
                # If last message was a tool response, generate a follow-up
                system_msg = f"""Based on the memory update, provide a helpful response to the user.

Current User Context:
{user_context}

{system_guidelines}

Keep your response concise and helpful. Briefly acknowledge the update and offer relevant assistance."""
                
                response = model.invoke([SystemMessage(content=system_msg)] + state["messages"][:-2])
            else:
                # Direct response without tool usage
                system_msg = f"""Provide a helpful response based on the user's request and their context.

Current User Context:
{user_context}

{system_guidelines}

Be personalized and helpful based on their preferences, dietary restrictions, and shopping history.
If suggesting products, include specific stores and prices when possible."""
                
                response = model.invoke([SystemMessage(content=system_msg)] + state["messages"])
            
            # Comprehensive response validation
            if hasattr(response, 'content'):
                original_content = response.content
                
                # Apply basic validation and sanitization
                validated_content = guard_rails.validate_response(original_content)
                
                # Check communication compliance
                compliance_check = guard_rails.validate_communication_compliance(validated_content, user_query)
                
                if not compliance_check["compliant"]:
                    # Log compliance issues
                    for issue in compliance_check["issues"]:
                        guard_rails.logger.warning(f"Communication compliance issue: {issue}")
                    
                    # If confidence is very low, use a fallback response
                    if compliance_check["confidence_score"] < 0.5:
                        validated_content = guard_rails.get_fallback_response('general_error')
                    
                    # Add a compliance note for monitoring
                    guard_rails.logger.info(f"Response compliance score: {compliance_check['confidence_score']:.2f}")
                
                response.content = validated_content
            
            return {"messages": [response]}
            
        except Exception as e:
            guard_rails.record_error(user_id, e)
            
            # If graceful degradation is enabled, return fallback
            agent_config = get_config()
            if agent_config.is_graceful_degradation_enabled():
                fallback = guard_rails.get_fallback_response('general_error')
                from langchain_core.messages import AIMessage
                return {"messages": [AIMessage(content=fallback)]}
            
            raise

    # Create the state graph
    builder = StateGraph(EnhancedMessagesState)
    
    # Add nodes
    builder.add_node("enhanced_generate_query_or_respond", enhanced_generate_query_or_respond)
    builder.add_node("product_search", ToolNode(AVAILABLE_TOOLS))
    builder.add_node("update_memory", update_memory_node)
    builder.add_node("respond_directly", respond_directly)
    builder.add_node("rewrite_question", rewrite_question)
    builder.add_node("generate_answer", generate_answer)
    builder.add_node("generate_fallback", generate_fallback)
    builder.add_node("final_response", final_response)
    
    # Add edges
    builder.add_edge(START, "enhanced_generate_query_or_respond")
    builder.add_conditional_edges("enhanced_generate_query_or_respond", route_decision)
    
    # Product search flow (existing logic)
    builder.add_conditional_edges(
        "product_search",
        grade_documents,
        {
            "generate_answer": "generate_answer",
            "rewrite_question": "rewrite_question", 
            "generate_fallback": "generate_fallback"
        }
    )
    builder.add_edge("rewrite_question", "enhanced_generate_query_or_respond")
    builder.add_edge("generate_answer", END)
    builder.add_edge("generate_fallback", END)
    
    # Memory update flow  
    builder.add_edge("update_memory", "final_response")
    builder.add_edge("final_response", END)
    
    # Direct response flow
    builder.add_edge("respond_directly", "final_response")

    # Checkpointer for short-term (within-thread) memory
    within_thread_memory = MemorySaver()
    
    # Compile graph with memory capabilities
    graph = builder.compile(checkpointer=within_thread_memory)
    
    print("✅ Enhanced agent graph with Supabase memory capabilities compiled successfully")
    
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