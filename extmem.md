
Open in Colab Open in LangChain Academy

Chatbot with message summarization & external DB memory
Review
We've covered how to customize graph state schema and reducer.

We've also shown a number of tricks for trimming or filtering messages in graph state.

We've used these concepts in a Chatbot with memory that produces a running summary of the conversation.

Goals
But, what if we want our Chatbot to have memory that persists indefinitely?

Now, we'll introduce some more advanced checkpointers that support external databases.

Here, we'll show how to use Sqlite as a checkpointer, but other checkpointers, such as Postgres are available!

%%capture --no-stderr
%pip install --quiet -U langgraph-checkpoint-sqlite langchain_core langgraph langchain_openai
import os, getpass

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")
Sqlite
A good starting point here is the SqliteSaver checkpointer.

Sqlite is a small, fast, highly popular SQL database.

If we supply ":memory:" it creates an in-memory Sqlite database.

import sqlite3
# In memory
conn = sqlite3.connect(":memory:", check_same_thread = False)
But, if we supply a db path, then it will create a database for us!

# pull file if it doesn't exist and connect to local db
!mkdir -p state_db && [ ! -f state_db/example.db ] && wget -P state_db https://github.com/langchain-ai/langchain-academy/raw/main/module-2/state_db/example.db

db_path = "state_db/example.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
# Here is our checkpointer 
from langgraph.checkpoint.sqlite import SqliteSaver
memory = SqliteSaver(conn)
Let's re-define our chatbot.

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage

from langgraph.graph import END
from langgraph.graph import MessagesState

model = ChatOpenAI(model="gpt-4o",temperature=0)

class State(MessagesState):
    summary: str

# Define the logic to call the model
def call_model(state: State):
    
    # Get summary if it exists
    summary = state.get("summary", "")

    # If there is summary, then we add it
    if summary:
        
        # Add summary to system message
        system_message = f"Summary of conversation earlier: {summary}"

        # Append summary to any newer messages
        messages = [SystemMessage(content=system_message)] + state["messages"]
    
    else:
        messages = state["messages"]
    
    response = model.invoke(messages)
    return {"messages": response}

def summarize_conversation(state: State):
    
    # First, we get any existing summary
    summary = state.get("summary", "")

    # Create our summarization prompt 
    if summary:
        
        # A summary already exists
        summary_message = (
            f"This is summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
        
    else:
        summary_message = "Create a summary of the conversation above:"

    # Add prompt to our history
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    
    # Delete all but the 2 most recent messages
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}

# Determine whether to end or summarize the conversation
def should_continue(state: State):
    
    """Return the next node to execute."""
    
    messages = state["messages"]
    
    # If there are more than six messages, then we summarize the conversation
    if len(messages) > 6:
        return "summarize_conversation"
    
    # Otherwise we can just end
    return END
Now, we just re-compile with our sqlite checkpointer.

from IPython.display import Image, display
from langgraph.graph import StateGraph, START

# Define a new graph
workflow = StateGraph(State)
workflow.add_node("conversation", call_model)
workflow.add_node(summarize_conversation)

# Set the entrypoint as conversation
workflow.add_edge(START, "conversation")
workflow.add_conditional_edges("conversation", should_continue)
workflow.add_edge("summarize_conversation", END)

# Compile
graph = workflow.compile(checkpointer=memory)
display(Image(graph.get_graph().draw_mermaid_png()))

Now, we can invoke the graph several times.

# Create a thread
config = {"configurable": {"thread_id": "1"}}

# Start conversation
input_message = HumanMessage(content="hi! I'm Lance")
output = graph.invoke({"messages": [input_message]}, config) 
for m in output['messages'][-1:]:
    m.pretty_print()

input_message = HumanMessage(content="what's my name?")
output = graph.invoke({"messages": [input_message]}, config) 
for m in output['messages'][-1:]:
    m.pretty_print()

input_message = HumanMessage(content="i like the 49ers!")
output = graph.invoke({"messages": [input_message]}, config) 
for m in output['messages'][-1:]:
    m.pretty_print()
/var/folders/l9/bpjxdmfx7lvd1fbdjn38y5dh0000gn/T/ipykernel_18873/2173919996.py:55: LangChainBetaWarning: The class `RemoveMessage` is in beta. It is actively being worked on, so the API may change.
  delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
================================== Ai Message ==================================

Hello again, Lance! It's great to hear from you. Since you like the 49ers, is there a particular player or moment in their history that stands out to you? Or perhaps you'd like to discuss their current season? Let me know!
================================== Ai Message ==================================

Your name is Lance! How can I assist you today? Would you like to talk more about the San Francisco 49ers or something else?
================================== Ai Message ==================================

That's awesome, Lance! The San Francisco 49ers have a rich history and a passionate fan base. Is there a specific aspect of the team you'd like to discuss? For example, we could talk about:

- Their legendary players like Joe Montana and Jerry Rice
- Memorable games and Super Bowl victories
- The current roster and season prospects
- Rivalries, like the one with the Seattle Seahawks
- Levi's Stadium and the fan experience

Let me know what interests you!
Let's confirm that our state is saved locally.

config = {"configurable": {"thread_id": "1"}}
graph_state = graph.get_state(config)
graph_state
StateSnapshot(values={'messages': [HumanMessage(content="hi! I'm Lance", id='d5bb4b3f-b1e9-4f61-8c75-7a7210b30253'), AIMessage(content="Hello again, Lance! It's great to hear from you. Since you like the 49ers, is there a particular player or moment in their history that stands out to you? Or perhaps you'd like to discuss their current season? Let me know!", additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 50, 'prompt_tokens': 337, 'total_tokens': 387}, 'model_name': 'gpt-4o-2024-05-13', 'system_fingerprint': 'fp_157b3831f5', 'finish_reason': 'stop', 'logprobs': None}, id='run-dde04d51-d305-4a9e-8ad5-6bdf5583196e-0', usage_metadata={'input_tokens': 337, 'output_tokens': 50, 'total_tokens': 387}), HumanMessage(content="what's my name?", id='d7530770-f130-4a05-a602-a96fd87859c6'), AIMessage(content='Your name is Lance! How can I assist you today? Would you like to talk more about the San Francisco 49ers or something else?', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 29, 'prompt_tokens': 243, 'total_tokens': 272}, 'model_name': 'gpt-4o-2024-05-13', 'system_fingerprint': 'fp_fde2829a40', 'finish_reason': 'stop', 'logprobs': None}, id='run-763b6387-c4c9-4658-9d01-7c018dde7a62-0', usage_metadata={'input_tokens': 243, 'output_tokens': 29, 'total_tokens': 272}), HumanMessage(content='i like the 49ers!', id='235dcec4-b656-4bee-b741-e330e1a026e2'), AIMessage(content="That's awesome, Lance! The San Francisco 49ers have a rich history and a passionate fan base. Is there a specific aspect of the team you'd like to discuss? For example, we could talk about:\n\n- Their legendary players like Joe Montana and Jerry Rice\n- Memorable games and Super Bowl victories\n- The current roster and season prospects\n- Rivalries, like the one with the Seattle Seahawks\n- Levi's Stadium and the fan experience\n\nLet me know what interests you!", additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 98, 'prompt_tokens': 287, 'total_tokens': 385}, 'model_name': 'gpt-4o-2024-05-13', 'system_fingerprint': 'fp_fde2829a40', 'finish_reason': 'stop', 'logprobs': None}, id='run-729860b2-16c3-46ff-ad1e-0a5475565b20-0', usage_metadata={'input_tokens': 287, 'output_tokens': 98, 'total_tokens': 385})], 'summary': 'Here\'s an extended summary of the conversation:\n\nLance introduced himself multiple times during the conversation, each time stating, "Hi! I\'m Lance." He expressed his fondness for the San Francisco 49ers football team. The AI assistant acknowledged Lance\'s name each time and showed willingness to discuss the 49ers, offering to talk about various aspects of the team such as their history, current roster, memorable games, prospects for the upcoming season, rivalries, and their home stadium, Levi\'s Stadium. Despite the AI\'s attempts to engage in a more detailed discussion about the 49ers, Lance reintroduced himself again without directly responding to the AI\'s questions or prompts about the team. The conversation remained brief and somewhat repetitive, focusing mainly on Lance\'s introductions and his interest in the 49ers.'}, next=(), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6a36d-ca9c-6144-801b-6d0cf97adc73'}}, metadata={'source': 'loop', 'writes': {'conversation': {'messages': AIMessage(content="That's awesome, Lance! The San Francisco 49ers have a rich history and a passionate fan base. Is there a specific aspect of the team you'd like to discuss? For example, we could talk about:\n\n- Their legendary players like Joe Montana and Jerry Rice\n- Memorable games and Super Bowl victories\n- The current roster and season prospects\n- Rivalries, like the one with the Seattle Seahawks\n- Levi's Stadium and the fan experience\n\nLet me know what interests you!", additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 98, 'prompt_tokens': 287, 'total_tokens': 385}, 'model_name': 'gpt-4o-2024-05-13', 'system_fingerprint': 'fp_fde2829a40', 'finish_reason': 'stop', 'logprobs': None}, id='run-729860b2-16c3-46ff-ad1e-0a5475565b20-0', usage_metadata={'input_tokens': 287, 'output_tokens': 98, 'total_tokens': 385})}}, 'step': 27, 'parents': {}}, created_at='2024-09-03T20:55:33.466540+00:00', parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6a36d-b8f3-6b40-801a-494776d2e9e0'}}, tasks=())
Persisting state
Using database like Sqlite means state is persisted!

For example, we can re-start the notebook kernel and see that we can still load from Sqlite DB on disk.

# Create a thread
config = {"configurable": {"thread_id": "1"}}
graph_state = graph.get_state(config)
graph_state
StateSnapshot(values={'messages': [HumanMessage(content="hi! I'm Lance", id='d5bb4b3f-b1e9-4f61-8c75-7a7210b30253'), AIMessage(content="Hello again, Lance! It's great to hear from you. Since you like the 49ers, is there a particular player or moment in their history that stands out to you? Or perhaps you'd like to discuss their current season? Let me know!", additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 50, 'prompt_tokens': 337, 'total_tokens': 387}, 'model_name': 'gpt-4o-2024-05-13', 'system_fingerprint': 'fp_157b3831f5', 'finish_reason': 'stop', 'logprobs': None}, id='run-dde04d51-d305-4a9e-8ad5-6bdf5583196e-0', usage_metadata={'input_tokens': 337, 'output_tokens': 50, 'total_tokens': 387}), HumanMessage(content="what's my name?", id='d7530770-f130-4a05-a602-a96fd87859c6'), AIMessage(content='Your name is Lance! How can I assist you today? Would you like to talk more about the San Francisco 49ers or something else?', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 29, 'prompt_tokens': 243, 'total_tokens': 272}, 'model_name': 'gpt-4o-2024-05-13', 'system_fingerprint': 'fp_fde2829a40', 'finish_reason': 'stop', 'logprobs': None}, id='run-763b6387-c4c9-4658-9d01-7c018dde7a62-0', usage_metadata={'input_tokens': 243, 'output_tokens': 29, 'total_tokens': 272}), HumanMessage(content='i like the 49ers!', id='235dcec4-b656-4bee-b741-e330e1a026e2'), AIMessage(content="That's awesome, Lance! The San Francisco 49ers have a rich history and a passionate fan base. Is there a specific aspect of the team you'd like to discuss? For example, we could talk about:\n\n- Their legendary players like Joe Montana and Jerry Rice\n- Memorable games and Super Bowl victories\n- The current roster and season prospects\n- Rivalries, like the one with the Seattle Seahawks\n- Levi's Stadium and the fan experience\n\nLet me know what interests you!", additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 98, 'prompt_tokens': 287, 'total_tokens': 385}, 'model_name': 'gpt-4o-2024-05-13', 'system_fingerprint': 'fp_fde2829a40', 'finish_reason': 'stop', 'logprobs': None}, id='run-729860b2-16c3-46ff-ad1e-0a5475565b20-0', usage_metadata={'input_tokens': 287, 'output_tokens': 98, 'total_tokens': 385})], 'summary': 'Here\'s an extended summary of the conversation:\n\nLance introduced himself multiple times during the conversation, each time stating, "Hi! I\'m Lance." He expressed his fondness for the San Francisco 49ers football team. The AI assistant acknowledged Lance\'s name each time and showed willingness to discuss the 49ers, offering to talk about various aspects of the team such as their history, current roster, memorable games, prospects for the upcoming season, rivalries, and their home stadium, Levi\'s Stadium. Despite the AI\'s attempts to engage in a more detailed discussion about the 49ers, Lance reintroduced himself again without directly responding to the AI\'s questions or prompts about the team. The conversation remained brief and somewhat repetitive, focusing mainly on Lance\'s introductions and his interest in the 49ers.'}, next=(), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6a36d-ca9c-6144-801b-6d0cf97adc73'}}, metadata={'source': 'loop', 'writes': {'conversation': {'messages': AIMessage(content="That's awesome, Lance! The San Francisco 49ers have a rich history and a passionate fan base. Is there a specific aspect of the team you'd like to discuss? For example, we could talk about:\n\n- Their legendary players like Joe Montana and Jerry Rice\n- Memorable games and Super Bowl victories\n- The current roster and season prospects\n- Rivalries, like the one with the Seattle Seahawks\n- Levi's Stadium and the fan experience\n\nLet me know what interests you!", additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 98, 'prompt_tokens': 287, 'total_tokens': 385}, 'model_name': 'gpt-4o-2024-05-13', 'system_fingerprint': 'fp_fde2829a40', 'finish_reason': 'stop', 'logprobs': None}, id='run-729860b2-16c3-46ff-ad1e-0a5475565b20-0', usage_metadata={'input_tokens': 287, 'output_tokens': 98, 'total_tokens': 385})}}, 'step': 27, 'parents': {}}, created_at='2024-09-03T20:55:33.466540+00:00', parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6a36d-b8f3-6b40-801a-494776d2e9e0'}}, tasks=())
LangGraph Studio
⚠️ DISCLAIMER

Since the filming of these videos, we've updated Studio so that it can be run locally and opened in your browser. This is now the preferred way to run Studio (rather than using the Desktop App as shown in the video). See documentation here on the local development server and here. To start the local development server, run the following command in your terminal in the /studio directory in this module:

langgraph dev
You should see the following output:

- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs
Open your browser and navigate to the Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024.

