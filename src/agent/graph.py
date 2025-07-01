"""Main graph definition for the product retrieval agent with memory capabilities."""

import os
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.base import BaseStore
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import SystemMessage

from .nodes import (
    generate_query_or_respond,
    grade_documents,
    rewrite_question,
    generate_answer,
    generate_fallback,
    EnhancedMessagesState
)
from .tools import AVAILABLE_TOOLS
from .memory_tools import MemoryManager, UpdateMemory


def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = [
        "OPENAI_API_KEY",
        "SUPABASE_ANON_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    print("✅ Environment validation passed")


def create_agent_graph():
    """Create the enhanced agent graph with memory capabilities."""
    # Validate environment
    validate_environment()
    
    # Import here to avoid circular imports
    from langchain_openai import ChatOpenAI
    
    # Initialize the model and memory manager
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    memory_manager = MemoryManager(model)
    
    # Enhanced system message with memory context
    ENHANCED_SYSTEM_MESSAGE = """You are a helpful grocery and meal planning assistant with long-term memory.

You help users with:
- 🛒 Product searches and recommendations  
- 📝 Grocery list management
- 🍽️ Meal planning
- 💰 Budget tracking
- 📊 Shopping history

You have access to:
1. **Product Database**: Search Dutch grocery products with prices from Albert Heijn, Jumbo, and Dirk
2. **User Memory**: Personal preferences, dietary restrictions, shopping history
3. **Memory Management**: Can save user profiles, grocery lists, meal plans, and budgets

**Current User Context:**
{user_context}

**Instructions:**
1. Use the user's context to personalize all recommendations
2. Consider dietary preferences, allergies, and budget constraints  
3. Suggest products from their preferred stores when possible
4. When users mention personal info, grocery items, meal plans, or budgets, decide whether to update memory
5. Always provide helpful, actionable advice for grocery shopping and meal planning

**Memory Update Decision:**
- Personal information (name, location, preferences, allergies) → update profile
- Grocery items, shopping lists → update grocery_list  
- Meal planning, recipes, cooking → update meal_plan
- Budget amounts, spending limits → update budget
- Shopping receipts, purchase history → update shopping_history

Be proactive about saving relevant information to provide better personalized service in future conversations."""

    def enhanced_generate_query_or_respond(state: EnhancedMessagesState, config: RunnableConfig, store: BaseStore):
        """Enhanced query generation with memory context and routing decisions."""
        user_id = config["configurable"]["user_id"]
        
        # Get user context from memory
        user_context = memory_manager.format_user_context(store, user_id)
        
        # Format system message with user context
        system_msg = ENHANCED_SYSTEM_MESSAGE.format(user_context=user_context)
        
        # Bind both product search tools and memory update tool
        all_tools = AVAILABLE_TOOLS + [UpdateMemory]
        enhanced_model = model.bind_tools(all_tools, parallel_tool_calls=False)
        
        response = enhanced_model.invoke([SystemMessage(content=system_msg)] + state["messages"])
        
        return {"messages": [response]}

    def route_decision(state: EnhancedMessagesState, config: RunnableConfig, store: BaseStore) -> Literal["product_search", "update_memory", "respond_directly"]:
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

    def update_memory_node(state: EnhancedMessagesState, config: RunnableConfig, store: BaseStore):
        """Update user memory based on the memory type specified."""
        user_id = config["configurable"]["user_id"]
        tool_call = state['messages'][-1].tool_calls[0]
        update_type = tool_call['args']['update_type']
        
        # Route to appropriate memory update function
        if update_type == 'profile':
            result = memory_manager.update_profile(store, user_id, state["messages"])
        elif update_type == 'grocery_list':
            result = memory_manager.update_grocery_lists(store, user_id, state["messages"])
        elif update_type == 'meal_plan':
            result = memory_manager.update_meal_plans(store, user_id, state["messages"])
        elif update_type == 'budget':
            result = memory_manager.update_budgets(store, user_id, state["messages"])
        elif update_type == 'shopping_history':
            # For shopping history, we'll extract purchase data from messages
            result = "Shopping history update not yet implemented"
        else:
            result = f"Unknown memory update type: {update_type}"
        
        # Return tool response
        tool_response = {
            "role": "tool",
            "content": result,
            "tool_call_id": tool_call['id']
        }
        
        return {"messages": [tool_response]}

    def respond_directly(state: EnhancedMessagesState, config: RunnableConfig, store: BaseStore):
        """Handle direct responses when no tools are called."""
        # Just pass through the current state - final_response will handle the actual response
        return state

    def final_response(state: EnhancedMessagesState, config: RunnableConfig, store: BaseStore):
        """Generate final response with updated memory context."""
        user_id = config["configurable"]["user_id"]
        
        # Get updated user context
        user_context = memory_manager.format_user_context(store, user_id)
        
        # Create response based on the last interaction
        last_message = state["messages"][-1]
        
        # Check if the last message is a tool message
        from langchain_core.messages import ToolMessage
        if isinstance(last_message, ToolMessage):
            # If last message was a tool response, generate a follow-up
            system_msg = f"""Based on the memory update, provide a helpful response to the user.

{user_context}

Keep your response concise and helpful. If memory was updated, briefly acknowledge it and offer relevant assistance."""
            
            response = model.invoke([SystemMessage(content=system_msg)] + state["messages"][:-2])
        else:
            # Direct response without tool usage
            system_msg = f"""Provide a helpful response based on the user's request and their context.

{user_context}

Be personalized and helpful based on their preferences and history."""
            
            response = model.invoke([SystemMessage(content=system_msg)] + state["messages"])
        
        return {"messages": [response]}

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
        grade_documents,  # Use grade_documents directly as conditional edge function
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
    
    # Direct response flow - route to final_response when no tools are called
    builder.add_edge("respond_directly", "final_response")

    # Store for long-term (across-thread) memory
    across_thread_memory = InMemoryStore()
    
    # Checkpointer for short-term (within-thread) memory
    within_thread_memory = MemorySaver()
    
    # Compile graph with memory capabilities
    graph = builder.compile(
        checkpointer=within_thread_memory,
        store=across_thread_memory
    )
    
    print("✅ Enhanced agent graph with memory capabilities compiled successfully")
    
    return graph


# Keep the existing graph creation for backwards compatibility
def create_original_graph():
    """Create the original product retrieval graph without memory."""
    validate_environment()
    
    # Create the state graph
    builder = StateGraph(EnhancedMessagesState)
    
    # Add nodes with original functionality
    builder.add_node("generate_query_or_respond", generate_query_or_respond)
    builder.add_node("retrieve", ToolNode(AVAILABLE_TOOLS))
    builder.add_node("grade_documents", grade_documents)
    builder.add_node("rewrite_question", rewrite_question)
    builder.add_node("generate_answer", generate_answer)
    builder.add_node("generate_fallback", generate_fallback)
    
    # Add edges for the existing workflow
    builder.add_edge(START, "generate_query_or_respond")
    builder.add_conditional_edges(
        "generate_query_or_respond",
        tools_condition,
        {"tools": "retrieve", "__end__": END}
    )
    builder.add_edge("retrieve", "grade_documents")
    builder.add_conditional_edges(
        "grade_documents",
        lambda state: "generate_answer" if state.get("relevant_docs", False) else "rewrite_question"
    )
    builder.add_edge("rewrite_question", "generate_query_or_respond")
    builder.add_edge("generate_answer", END)
    builder.add_edge("generate_fallback", END)
    
    # Compile without memory for testing
    graph = builder.compile()
    
    print("✅ Original agent graph compiled successfully")
    
    return graph


# Default export is the enhanced graph with memory
graph = create_agent_graph()


def run_agent(question: str, verbose: bool = True):
    """
    Run the agent with a given question.
    
    Args:
        question: The user's question
        verbose: Whether to print intermediate steps
        
    Returns:
        Final response from the agent
    """
    graph = create_agent_graph()
    
    # Initial state with retry tracking
    initial_state = {
        "messages": [{"role": "user", "content": question}],
        "retry_count": 0
    }
    
    if verbose:
        print(f"\n🔍 Processing question: {question}\n")
        print("=" * 60)
    
    try:
        final_response = None
        for chunk in graph.stream(initial_state):
            for node, update in chunk.items():
                if verbose:
                    print(f"\n📍 Update from node: {node}")
                    if "messages" in update and update["messages"]:
                        last_message = update["messages"][-1]
                        if hasattr(last_message, 'pretty_print'):
                            last_message.pretty_print()
                        else:
                            print(f"Content: {last_message.get('content', 'No content')}")
                    print("-" * 40)
                
                # Capture the final response
                if "messages" in update and update["messages"]:
                    final_response = update["messages"][-1]
        
        if verbose:
            print("=" * 60)
            print("✅ Agent processing complete\n")
        
        return final_response
        
    except Exception as e:
        error_msg = f"❌ Error running agent: {e}"
        print(error_msg)
        return {"role": "assistant", "content": "I apologize, but I encountered an error while processing your question. Please try again."}


# For backward compatibility
def create_graph():
    """Legacy function name - use create_agent_graph() instead."""
    return create_agent_graph()


if __name__ == "__main__":
    # Example usage
    test_query = "What products do you have in the dairy category?"
    print("Query:", test_query)
    print("Response:", run_agent(test_query)) 