"""Nodes for the product retrieval agent."""

import os
from typing import Literal, TypedDict
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState
from .tools import AVAILABLE_TOOLS

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
    """Grade documents using a binary score for relevance check."""

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )


GRADE_PROMPT = (
    "You are a grader assessing relevance of retrieved product information to a user question. \n "
    "Here is the retrieved product information: \n\n {context} \n\n"
    "Here is the user question: {question} \n"
    "If the product information contains details that are relevant to answering the user's question "
    "about products, prices, brands, categories, or specifications, grade it as relevant. \n"
    "Give a binary score 'yes' or 'no' to indicate whether the product information is relevant to the question."
)


grader_model = init_chat_model("openai:gpt-4o-mini", temperature=0)


def grade_documents(
    state: EnhancedMessagesState,
) -> Literal["generate_answer", "rewrite_question", "generate_fallback"]:
    """
    Determine whether the retrieved product information is relevant to the question.
    Includes recursion prevention by tracking retry attempts.
    """
    question = state["messages"][0].content
    context = state["messages"][-1].content
    
    # Get retry count from state, defaulting to 0
    retry_count = state.get('retry_count', 0)
    
    # If we've hit the retry limit, generate a fallback response
    if retry_count >= MAX_RETRIES:
        print(f"Maximum retries ({MAX_RETRIES}) reached. Generating fallback response.")
        return "generate_fallback"
    
    # Check if the context indicates a failed query (empty, error message, etc.)
    if not context or context.strip() == "" or "error" in context.lower() or "no products found" in context.lower():
        print(f"Failed query detected. Retry count: {retry_count + 1}")
        # Return updated state with incremented retry count
        return "rewrite_question"
    
    prompt = GRADE_PROMPT.format(question=question, context=context)
    try:
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
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question that might better match product information:"
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


def generate_answer(state: EnhancedMessagesState):
    """Generate an answer based on the product information."""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    
    try:
        response = response_model.invoke([{"role": "user", "content": prompt}])
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
    "You could try:\n"
    "- Using different or more specific search terms\n"
    "- Asking about product categories or brands instead of specific items\n"
    "- Checking if the product name or brand is spelled correctly\n\n"
    "Is there anything else I can help you with?"
)


def generate_fallback(state: EnhancedMessagesState):
    """Generate a fallback response when retrieval consistently fails."""
    question = state["messages"][0].content
    fallback_content = FALLBACK_PROMPT.format(question=question)
    
    return {
        "messages": [{"role": "assistant", "content": fallback_content}],
        "retry_count": 0  # Reset retry count for future queries
    } 