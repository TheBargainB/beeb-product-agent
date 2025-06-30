"""Main graph definition for the product retrieval agent."""

import os
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from .nodes import (
    generate_query_or_respond,
    grade_documents,
    rewrite_question,
    generate_answer,
    generate_fallback,
    EnhancedMessagesState
)
from .tools import AVAILABLE_TOOLS


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
    """Create and compile the agent graph."""
    
    # Validate environment first
    validate_environment()
    
    # Create workflow with enhanced state
    workflow = StateGraph(EnhancedMessagesState)

    # Define the nodes we will cycle between
    workflow.add_node("generate_query_or_respond", generate_query_or_respond)
    workflow.add_node("retrieve", ToolNode(AVAILABLE_TOOLS))
    workflow.add_node("rewrite_question", rewrite_question)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("generate_fallback", generate_fallback)

    # Set the entry point
    workflow.add_edge(START, "generate_query_or_respond")

    # Decide whether to retrieve or respond directly
    workflow.add_conditional_edges(
        "generate_query_or_respond",
        # Assess LLM decision (call tools or respond to the user)
        tools_condition,
        {
            # Translate the condition outputs to nodes in our graph
            "tools": "retrieve",
            END: END,
        },
    )

    # After retrieval, grade the documents
    workflow.add_conditional_edges(
        "retrieve",
        # Assess agent decision and handle retries
        grade_documents,
        {
            "generate_answer": "generate_answer",
            "rewrite_question": "rewrite_question", 
            "generate_fallback": "generate_fallback"
        }
    )
    
    # Connect answer generation to end
    workflow.add_edge("generate_answer", END)
    
    # Connect fallback generation to end
    workflow.add_edge("generate_fallback", END)
    
    # Rewrite question loops back to try again
    workflow.add_edge("rewrite_question", "generate_query_or_respond")

    # Compile the graph
    graph = workflow.compile()
    
    print("✅ Agent graph compiled successfully")
    return graph


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