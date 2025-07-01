
Chatbot with Memory
Review
Memory is a cognitive function that allows people to store, retrieve, and use information to understand their present and future.

There are various long-term memory types that can be used in AI applications.

Goals
Here, we'll introduce the LangGraph Memory Store as a way to save and retrieve long-term memories.

We'll build a chatbot that uses both short-term (within-thread) and long-term (across-thread) memory.

We'll focus on long-term semantic memory, which will be facts about the user.

These long-term memories will be used to create a personalized chatbot that can remember facts about the user.

It will save memory "in the hot path", as the user is chatting with it.

%%capture --no-stderr
%pip install -U langchain_openai langgraph langchain_core
We'll use LangSmith for tracing.

import os, getpass

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("LANGSMITH_API_KEY")
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "langchain-academy"
Introduction to the LangGraph Store
The LangGraph Memory Store provides a way to store and retrieve information across threads in LangGraph.

This is an open source base class for persistent key-value stores.

import uuid
from langgraph.store.memory import InMemoryStore
in_memory_store = InMemoryStore()
When storing objects (e.g., memories) in the Store, we provide:

The namespace for the object, a tuple (similar to directories)
the object key (similar to filenames)
the object value (similar to file contents)
We use the put method to save an object to the store by namespace and key.

langgraph_store.png

# Namespace for the memory to save
user_id = "1"
namespace_for_memory = (user_id, "memories")

# Save a memory to namespace as key and value
key = str(uuid.uuid4())

# The value needs to be a dictionary  
value = {"food_preference" : "I like pizza"}

# Save the memory
in_memory_store.put(namespace_for_memory, key, value)
We use search to retrieve objects from the store by namespace.

This returns a list.

# Search 
memories = in_memory_store.search(namespace_for_memory)
type(memories)
list
# Metatdata 
memories[0].dict()
{'value': {'food_preference': 'I like pizza'},
 'key': 'a754b8c5-e8b7-40ec-834b-c426a9a7c7cc',
 'namespace': ['1', 'memories'],
 'created_at': '2024-11-04T22:48:16.727572+00:00',
 'updated_at': '2024-11-04T22:48:16.727574+00:00'}
# The key, value
print(memories[0].key, memories[0].value)
a754b8c5-e8b7-40ec-834b-c426a9a7c7cc {'food_preference': 'I like pizza'}
We can also use get to retrieve an object by namespace and key.

# Get the memory by namespace and key
memory = in_memory_store.get(namespace_for_memory, key)
memory.dict()
{'value': {'food_preference': 'I like pizza'},
 'key': 'a754b8c5-e8b7-40ec-834b-c426a9a7c7cc',
 'namespace': ['1', 'memories'],
 'created_at': '2024-11-04T22:48:16.727572+00:00',
 'updated_at': '2024-11-04T22:48:16.727574+00:00'}
Chatbot with long-term memory
We want a chatbot that has two types of memory:

Short-term (within-thread) memory: Chatbot can persist conversational history and / or allow interruptions in a chat session.
Long-term (cross-thread) memory: Chatbot can remember information about a specific user across all chat sessions.
_set_env("OPENAI_API_KEY")
For short-term memory, we'll use a checkpointer.

See Module 2 and our conceptual docs for more on checkpointers, but in summary:

They write the graph state at each step to a thread.
They persist the chat history in the thread.
They allow the graph to be interrupted and / or resumed from any step in the thread.
And, for long-term memory, we'll use the LangGraph Store as introduced above.

# Chat model 
from langchain_openai import ChatOpenAI

# Initialize the LLM
model = ChatOpenAI(model="gpt-4o", temperature=0) 
The chat history will be saved to short-term memory using the checkpointer.

The chatbot will reflect on the chat history.

It will then create and save a memory to the LangGraph Store.

This memory is accessible in future chat sessions to personalize the chatbot's responses.

from IPython.display import Image, display

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.store.base import BaseStore

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig

# Chatbot instruction
MODEL_SYSTEM_MESSAGE = """You are a helpful assistant with memory that provides information about the user. 
If you have memory for this user, use it to personalize your responses.
Here is the memory (it may be empty): {memory}"""

# Create new memory from the chat history and any existing memory
CREATE_MEMORY_INSTRUCTION = """"You are collecting information about the user to personalize your responses.

CURRENT USER INFORMATION:
{memory}

INSTRUCTIONS:
1. Review the chat history below carefully
2. Identify new information about the user, such as:
   - Personal details (name, location)
   - Preferences (likes, dislikes)
   - Interests and hobbies
   - Past experiences
   - Goals or future plans
3. Merge any new information with existing memory
4. Format the memory as a clear, bulleted list
5. If new information conflicts with existing memory, keep the most recent version

Remember: Only include factual information directly stated by the user. Do not make assumptions or inferences.

Based on the chat history below, please update the user information:"""

def call_model(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Load memory from the store and use it to personalize the chatbot's response."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve memory from the store
    namespace = ("memory", user_id)
    key = "user_memory"
    existing_memory = store.get(namespace, key)

    # Extract the actual memory content if it exists and add a prefix
    if existing_memory:
        # Value is a dictionary with a memory key
        existing_memory_content = existing_memory.value.get('memory')
    else:
        existing_memory_content = "No existing memory found."

    # Format the memory in the system prompt
    system_msg = MODEL_SYSTEM_MESSAGE.format(memory=existing_memory_content)
    
    # Respond using memory as well as the chat history
    response = model.invoke([SystemMessage(content=system_msg)]+state["messages"])

    return {"messages": response}

def write_memory(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and save a memory to the store."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve existing memory from the store
    namespace = ("memory", user_id)
    existing_memory = store.get(namespace, "user_memory")
        
    # Extract the memory
    if existing_memory:
        existing_memory_content = existing_memory.value.get('memory')
    else:
        existing_memory_content = "No existing memory found."

    # Format the memory in the system prompt
    system_msg = CREATE_MEMORY_INSTRUCTION.format(memory=existing_memory_content)
    new_memory = model.invoke([SystemMessage(content=system_msg)]+state['messages'])

    # Overwrite the existing memory in the store 
    key = "user_memory"

    # Write value as a dictionary with a memory key
    store.put(namespace, key, {"memory": new_memory.content})

# Define the graph
builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_node("write_memory", write_memory)
builder.add_edge(START, "call_model")
builder.add_edge("call_model", "write_memory")
builder.add_edge("write_memory", END)

# Store for long-term (across-thread) memory
across_thread_memory = InMemoryStore()

# Checkpointer for short-term (within-thread) memory
within_thread_memory = MemorySaver()

# Compile the graph with the checkpointer fir and store
graph = builder.compile(checkpointer=within_thread_memory, store=across_thread_memory)

# View
display(Image(graph.get_graph(xray=1).draw_mermaid_png()))

When we interact with the chatbot, we supply two things:

Short-term (within-thread) memory: A thread ID for persisting the chat history.
Long-term (cross-thread) memory: A user ID to namespace long-term memories to the user.
Let's see how these work together in practice.

# We supply a thread ID for short-term (within-thread) memory
# We supply a user ID for long-term (across-thread) memory 
config = {"configurable": {"thread_id": "1", "user_id": "1"}}

# User input 
input_messages = [HumanMessage(content="Hi, my name is Lance")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

Hi, my name is Lance
================================== Ai Message ==================================

Hello, Lance! It's nice to meet you. How can I assist you today?
# User input 
input_messages = [HumanMessage(content="I like to bike around San Francisco")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

I like to bike around San Francisco
================================== Ai Message ==================================

That sounds like a great way to explore the city, Lance! San Francisco has some beautiful routes and views. Do you have a favorite trail or area you like to bike in?
We're using the MemorySaver checkpointer for within-thread memory.

This saves the chat history to the thread.

We can look at the chat history saved to the thread.

thread = {"configurable": {"thread_id": "1"}}
state = graph.get_state(thread).values
for m in state["messages"]: 
    m.pretty_print()
================================ Human Message =================================

Hi, my name is Lance
================================== Ai Message ==================================

Hello, Lance! It's nice to meet you. How can I assist you today?
================================ Human Message =================================

I like to bike around San Francisco
================================== Ai Message ==================================

That sounds like a great way to explore the city, Lance! San Francisco has some beautiful routes and views. Do you have a favorite trail or area you like to bike in?
Recall that we compiled the graph with our the store:

across_thread_memory = InMemoryStore()
And, we added a node to the graph (write_memory) that reflects on the chat history and saves a memory to the store.

We can to see if the memory was saved to the store.

# Namespace for the memory to save
user_id = "1"
namespace = ("memory", user_id)
existing_memory = across_thread_memory.get(namespace, "user_memory")
existing_memory.dict()
{'value': {'memory': "**Updated User Information:**\n- User's name is Lance.\n- Likes to bike around San Francisco."},
 'key': 'user_memory',
 'namespace': ['memory', '1'],
 'created_at': '2024-11-05T00:12:17.383918+00:00',
 'updated_at': '2024-11-05T00:12:25.469528+00:00'}
Now, let's kick off a new thread with the same user ID.

We should see that the chatbot remembered the user's profile and used it to personalize the response.

# We supply a user ID for across-thread memory as well as a new thread ID
config = {"configurable": {"thread_id": "2", "user_id": "1"}}

# User input 
input_messages = [HumanMessage(content="Hi! Where would you recommend that I go biking?")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

Hi! Where would you recommend that I go biking?
================================== Ai Message ==================================

Hi Lance! Since you enjoy biking around San Francisco, there are some fantastic routes you might love. Here are a few recommendations:

1. **Golden Gate Park**: This is a classic choice with plenty of trails and beautiful scenery. You can explore the park's many attractions, like the Conservatory of Flowers and the Japanese Tea Garden.

2. **The Embarcadero**: A ride along the Embarcadero offers stunning views of the Bay Bridge and the waterfront. It's a great way to experience the city's vibrant atmosphere.

3. **Marin Headlands**: If you're up for a bit of a challenge, biking across the Golden Gate Bridge to the Marin Headlands offers breathtaking views of the city and the Pacific Ocean.

4. **Presidio**: This area has a network of trails with varying difficulty levels, and you can enjoy views of the Golden Gate Bridge and the bay.

5. **Twin Peaks**: For a more challenging ride, head up to Twin Peaks. The climb is worth it for the panoramic views of the city.

Let me know if you want more details on any of these routes!
# User input 
input_messages = [HumanMessage(content="Great, are there any bakeries nearby that I can check out? I like a croissant after biking.")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

Great, are there any bakeries nearby that I can check out? I like a croissant after biking.
================================== Ai Message ==================================

Absolutely, Lance! Here are a few bakeries in San Francisco where you can enjoy a delicious croissant after your ride:

1. **Tartine Bakery**: Located in the Mission District, Tartine is famous for its pastries, and their croissants are a must-try.

2. **Arsicault Bakery**: This bakery in the Richmond District has been praised for its buttery, flaky croissants. It's a bit of a detour, but worth it!

3. **b. Patisserie**: Situated in Lower Pacific Heights, b. Patisserie offers a variety of pastries, and their croissants are particularly popular.

4. **Le Marais Bakery**: With locations in the Marina and Castro, Le Marais offers a charming French bakery experience with excellent croissants.

5. **Neighbor Bakehouse**: Located in the Dogpatch, this bakery is known for its creative pastries, including some fantastic croissants.

These spots should provide a delightful treat after your biking adventures. Enjoy your ride and your croissant!
Viewing traces in LangSmith
We can see that the memories are retrieved from the store and supplied as part of the system prompt, as expected:

https://smith.langchain.com/public/10268d64-82ff-434e-ac02-4afa5cc15432/r

Studio
We can also interact with our chatbot in Studio.

Screenshot 2024-10-28 at 10.08.27 AM.png



Chatbot with Collection Schema
Review
We extended our chatbot to save semantic memories to a single user profile.

We also introduced a library, Trustcall, to update this schema with new information.

Goals
Sometimes we want to save memories to a collection rather than single profile.

Here we'll update our chatbot to save memories to a collection.

We'll also show how to use Trustcall to update this collection.

%%capture --no-stderr
%pip install -U langchain_openai langgraph trustcall langchain_core
import os, getpass

def _set_env(var: str):
    # Check if the variable is set in the OS environment
    env_value = os.environ.get(var)
    if not env_value:
        # If not set, prompt the user for input
        env_value = getpass.getpass(f"{var}: ")
    
    # Set the environment variable for the current process
    os.environ[var] = env_value

_set_env("LANGSMITH_API_KEY")
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "langchain-academy"
Defining a collection schema
Instead of storing user information in a fixed profile structure, we'll create a flexible collection schema to store memories about user interactions.

Each memory will be stored as a separate entry with a single content field for the main information we want to remember

This approach allows us to build an open-ended collection of memories that can grow and change as we learn more about the user.

We can define a collection schema as a Pydantic object.

from pydantic import BaseModel, Field

class Memory(BaseModel):
    content: str = Field(description="The main content of the memory. For example: User expressed interest in learning about French.")

class MemoryCollection(BaseModel):
    memories: list[Memory] = Field(description="A list of memories about the user.")
_set_env("OPENAI_API_KEY")
We can used LangChain's chat model chat model interface's with_structured_output method to enforce structured output.

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0)

# Bind schema to model
model_with_structure = model.with_structured_output(MemoryCollection)

# Invoke the model to produce structured output that matches the schema
memory_collection = model_with_structure.invoke([HumanMessage("My name is Lance. I like to bike.")])
memory_collection.memories
[Memory(content="User's name is Lance."),
 Memory(content='Lance likes to bike.')]
We can use model_dump() to serialize a Pydantic model instance into a Python dictionary.

memory_collection.memories[0].model_dump()
{'content': "User's name is Lance."}
Save dictionary representation of each memory to the store.

import uuid
from langgraph.store.memory import InMemoryStore

# Initialize the in-memory store
in_memory_store = InMemoryStore()

# Namespace for the memory to save
user_id = "1"
namespace_for_memory = (user_id, "memories")

# Save a memory to namespace as key and value
key = str(uuid.uuid4())
value = memory_collection.memories[0].model_dump()
in_memory_store.put(namespace_for_memory, key, value)

key = str(uuid.uuid4())
value = memory_collection.memories[1].model_dump()
in_memory_store.put(namespace_for_memory, key, value)
Search for memories in the store.

# Search 
for m in in_memory_store.search(namespace_for_memory):
    print(m.dict())
{'value': {'content': "User's name is Lance."}, 'key': 'e1c4e5ab-ab0f-4cbb-822d-f29240a983af', 'namespace': ['1', 'memories'], 'created_at': '2024-10-30T21:43:26.893775+00:00', 'updated_at': '2024-10-30T21:43:26.893779+00:00'}
{'value': {'content': 'Lance likes to bike.'}, 'key': 'e132a1ea-6202-43ac-a9a6-3ecf2c1780a8', 'namespace': ['1', 'memories'], 'created_at': '2024-10-30T21:43:26.893833+00:00', 'updated_at': '2024-10-30T21:43:26.893834+00:00'}
Updating collection schema
We discussed the challenges with updating a profile schema in the last lesson.

The same applies for collections!

We want the ability to update the collection with new memories as well as update existing memories in the collection.

Now we'll show that Trustcall can be also used to update a collection.

This enables both addition of new memories as well as updating existing memories in the collection.

Let's define a new extractor with Trustcall.

As before, we provide the schema for each memory, Memory.

But, we can supply enable_inserts=True to allow the extractor to insert new memories to the collection.

from trustcall import create_extractor

# Create the extractor
trustcall_extractor = create_extractor(
    model,
    tools=[Memory],
    tool_choice="Memory",
    enable_inserts=True,
)
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Instruction
instruction = """Extract memories from the following conversation:"""

# Conversation
conversation = [HumanMessage(content="Hi, I'm Lance."), 
                AIMessage(content="Nice to meet you, Lance."), 
                HumanMessage(content="This morning I had a nice bike ride in San Francisco.")]

# Invoke the extractor
result = trustcall_extractor.invoke({"messages": [SystemMessage(content=instruction)] + conversation})
# Messages contain the tool calls
for m in result["messages"]:
    m.pretty_print()
================================== Ai Message ==================================
Tool Calls:
  Memory (call_Pj4kctFlpg9TgcMBfMH33N30)
 Call ID: call_Pj4kctFlpg9TgcMBfMH33N30
  Args:
    content: Lance had a nice bike ride in San Francisco this morning.
# Responses contain the memories that adhere to the schema
for m in result["responses"]: 
    print(m)
content='Lance had a nice bike ride in San Francisco this morning.'
# Metadata contains the tool call  
for m in result["response_metadata"]: 
    print(m)
{'id': 'call_Pj4kctFlpg9TgcMBfMH33N30'}
# Update the conversation
updated_conversation = [AIMessage(content="That's great, did you do after?"), 
                        HumanMessage(content="I went to Tartine and ate a croissant."),                        
                        AIMessage(content="What else is on your mind?"),
                        HumanMessage(content="I was thinking about my Japan, and going back this winter!"),]

# Update the instruction
system_msg = """Update existing memories and create new ones based on the following conversation:"""

# We'll save existing memories, giving them an ID, key (tool name), and value
tool_name = "Memory"
existing_memories = [(str(i), tool_name, memory.model_dump()) for i, memory in enumerate(result["responses"])] if result["responses"] else None
existing_memories
[('0',
  'Memory',
  {'content': 'Lance had a nice bike ride in San Francisco this morning.'})]
# Invoke the extractor with our updated conversation and existing memories
result = trustcall_extractor.invoke({"messages": updated_conversation, 
                                     "existing": existing_memories})
# Messages from the model indicate two tool calls were made
for m in result["messages"]:
    m.pretty_print()
================================== Ai Message ==================================
Tool Calls:
  Memory (call_vxks0YH1hwUxkghv4f5zdkTr)
 Call ID: call_vxks0YH1hwUxkghv4f5zdkTr
  Args:
    content: Lance had a nice bike ride in San Francisco this morning. He went to Tartine and ate a croissant. He was thinking about his trip to Japan and going back this winter!
  Memory (call_Y4S3poQgFmDfPy2ExPaMRk8g)
 Call ID: call_Y4S3poQgFmDfPy2ExPaMRk8g
  Args:
    content: Lance went to Tartine and ate a croissant. He was thinking about his trip to Japan and going back this winter!
# Responses contain the memories that adhere to the schema
for m in result["responses"]: 
    print(m)
content='Lance had a nice bike ride in San Francisco this morning. He went to Tartine and ate a croissant. He was thinking about his trip to Japan and going back this winter!'
content='Lance went to Tartine and ate a croissant. He was thinking about his trip to Japan and going back this winter!'
This tells us that we updated the first memory in the collection by specifying the json_doc_id.

# Metadata contains the tool call  
for m in result["response_metadata"]: 
    print(m)
{'id': 'call_vxks0YH1hwUxkghv4f5zdkTr', 'json_doc_id': '0'}
{'id': 'call_Y4S3poQgFmDfPy2ExPaMRk8g'}
LangSmith trace:

https://smith.langchain.com/public/ebc1cb01-f021-4794-80c0-c75d6ea90446/r

Chatbot with collection schema updating
Now, let's bring Trustcall into our chatbot to create and update a memory collection.

from IPython.display import Image, display

import uuid

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.store.memory import InMemoryStore
from langchain_core.messages import merge_message_runs
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.base import BaseStore

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0)

# Memory schema
class Memory(BaseModel):
    content: str = Field(description="The main content of the memory. For example: User expressed interest in learning about French.")

# Create the Trustcall extractor
trustcall_extractor = create_extractor(
    model,
    tools=[Memory],
    tool_choice="Memory",
    # This allows the extractor to insert new memories
    enable_inserts=True,
)

# Chatbot instruction
MODEL_SYSTEM_MESSAGE = """You are a helpful chatbot. You are designed to be a companion to a user. 

You have a long term memory which keeps track of information you learn about the user over time.

Current Memory (may include updated memories from this conversation): 

{memory}"""

# Trustcall instruction
TRUSTCALL_INSTRUCTION = """Reflect on following interaction. 

Use the provided tools to retain any necessary memories about the user. 

Use parallel tool calling to handle updates and insertions simultaneously:"""

def call_model(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Load memories from the store and use them to personalize the chatbot's response."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve memory from the store
    namespace = ("memories", user_id)
    memories = store.search(namespace)

    # Format the memories for the system prompt
    info = "\n".join(f"- {mem.value['content']}" for mem in memories)
    system_msg = MODEL_SYSTEM_MESSAGE.format(memory=info)

    # Respond using memory as well as the chat history
    response = model.invoke([SystemMessage(content=system_msg)]+state["messages"])

    return {"messages": response}

def write_memory(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and update the memory collection."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Define the namespace for the memories
    namespace = ("memories", user_id)

    # Retrieve the most recent memories for context
    existing_items = store.search(namespace)

    # Format the existing memories for the Trustcall extractor
    tool_name = "Memory"
    existing_memories = ([(existing_item.key, tool_name, existing_item.value)
                          for existing_item in existing_items]
                          if existing_items
                          else None
                        )

    # Merge the chat history and the instruction
    updated_messages=list(merge_message_runs(messages=[SystemMessage(content=TRUSTCALL_INSTRUCTION)] + state["messages"]))

    # Invoke the extractor
    result = trustcall_extractor.invoke({"messages": updated_messages, 
                                        "existing": existing_memories})

    # Save the memories from Trustcall to the store
    for r, rmeta in zip(result["responses"], result["response_metadata"]):
        store.put(namespace,
                  rmeta.get("json_doc_id", str(uuid.uuid4())),
                  r.model_dump(mode="json"),
            )

# Define the graph
builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_node("write_memory", write_memory)
builder.add_edge(START, "call_model")
builder.add_edge("call_model", "write_memory")
builder.add_edge("write_memory", END)

# Store for long-term (across-thread) memory
across_thread_memory = InMemoryStore()

# Checkpointer for short-term (within-thread) memory
within_thread_memory = MemorySaver()

# Compile the graph with the checkpointer fir and store
graph = builder.compile(checkpointer=within_thread_memory, store=across_thread_memory)

# View
display(Image(graph.get_graph(xray=1).draw_mermaid_png()))

# We supply a thread ID for short-term (within-thread) memory
# We supply a user ID for long-term (across-thread) memory 
config = {"configurable": {"thread_id": "1", "user_id": "1"}}

# User input 
input_messages = [HumanMessage(content="Hi, my name is Lance")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

Hi, my name is Lance
================================== Ai Message ==================================

Hi Lance! It's great to meet you. How can I assist you today?
# User input 
input_messages = [HumanMessage(content="I like to bike around San Francisco")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

I like to bike around San Francisco
================================== Ai Message ==================================

That sounds like a lot of fun! San Francisco has some beautiful routes for biking. Do you have a favorite trail or area you like to explore?
# Namespace for the memory to save
user_id = "1"
namespace = ("memories", user_id)
memories = across_thread_memory.search(namespace)
for m in memories:
    print(m.dict())
{'value': {'content': "User's name is Lance."}, 'key': 'dee65880-dd7d-4184-8ca1-1f7400f7596b', 'namespace': ['memories', '1'], 'created_at': '2024-10-30T22:18:52.413283+00:00', 'updated_at': '2024-10-30T22:18:52.413284+00:00'}
{'value': {'content': 'User likes to bike around San Francisco.'}, 'key': '662195fc-8ea4-4f64-a6b6-6b86d9cb85c0', 'namespace': ['memories', '1'], 'created_at': '2024-10-30T22:18:56.597813+00:00', 'updated_at': '2024-10-30T22:18:56.597814+00:00'}
# User input 
input_messages = [HumanMessage(content="I also enjoy going to bakeries")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

I also enjoy going to bakeries
================================== Ai Message ==================================

Biking and bakeries make a great combination! Do you have a favorite bakery in San Francisco, or are you on the hunt for new ones to try?
Continue the conversation in a new thread.

# We supply a thread ID for short-term (within-thread) memory
# We supply a user ID for long-term (across-thread) memory 
config = {"configurable": {"thread_id": "2", "user_id": "1"}}

# User input 
input_messages = [HumanMessage(content="What bakeries do you recommend for me?")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

What bakeries do you recommend for me?
================================== Ai Message ==================================

Since you enjoy biking around San Francisco, you might like to check out some of these bakeries that are both delicious and located in areas that are great for a bike ride:

1. **Tartine Bakery** - Located in the Mission District, it's famous for its bread and pastries. The area is vibrant and perfect for a leisurely ride.

2. **Arsicault Bakery** - Known for its incredible croissants, it's in the Richmond District, which offers a nice ride through Golden Gate Park.

3. **B. Patisserie** - Situated in Lower Pacific Heights, this bakery is renowned for its kouign-amann and other French pastries. The neighborhood is charming and bike-friendly.

4. **Mr. Holmes Bakehouse** - Famous for its cruffins, it's located in the Tenderloin, which is a bit more urban but still accessible by bike.

5. **Noe Valley Bakery** - A cozy spot in Noe Valley, perfect for a stop after exploring the hilly streets of the area.

Do any of these sound like a good fit for your next biking adventure?
LangSmith
https://smith.langchain.com/public/c87543ec-b426-4a82-a3ab-94d01c01d9f4/r

Studio
Screenshot 2024-10-30 at 11.29.25 AM.png

 
Chatbot with Profile Schema
Review
We introduced the LangGraph Memory Store as a way to save and retrieve long-term memories.

We built a simple chatbot that uses both short-term (within-thread) and long-term (across-thread) memory.

It saved long-term semantic memory (facts about the user) "in the hot path", as the user is chatting with it.

Goals
Our chatbot saved memories as a string. In practice, we often want memories to have a structure.

For example, memories can be a single, continuously updated schema).

In our case, we want this to be a single user profile.

We'll extend our chatbot to save semantic memories to a single user profile.

We'll also introduce a library, Trustcall, to update this schema with new information.

%%capture --no-stderr
%pip install -U langchain_openai langgraph trustcall langchain_core
import os, getpass

def _set_env(var: str):
    # Check if the variable is set in the OS environment
    env_value = os.environ.get(var)
    if not env_value:
        # If not set, prompt the user for input
        env_value = getpass.getpass(f"{var}: ")
    
    # Set the environment variable for the current process
    os.environ[var] = env_value

_set_env("LANGSMITH_API_KEY")
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "langchain-academy"
Defining a user profile schema
Python has many different types for structured data, such as TypedDict, Dictionaries, JSON, and Pydantic.

Let's start by using TypedDict to define a user profile schema.

from typing import TypedDict, List

class UserProfile(TypedDict):
    """User profile schema with typed fields"""
    user_name: str  # The user's preferred name
    interests: List[str]  # A list of the user's interests
Saving a schema to the store
The LangGraph Store accepts any Python dictionary as the value.

# TypedDict instance
user_profile: UserProfile = {
    "user_name": "Lance",
    "interests": ["biking", "technology", "coffee"]
}
user_profile
{'user_name': 'Lance', 'interests': ['biking', 'technology', 'coffee']}
We use the put method to save the TypedDict to the store.

import uuid
from langgraph.store.memory import InMemoryStore

# Initialize the in-memory store
in_memory_store = InMemoryStore()

# Namespace for the memory to save
user_id = "1"
namespace_for_memory = (user_id, "memory")

# Save a memory to namespace as key and value
key = "user_profile"
value = user_profile
in_memory_store.put(namespace_for_memory, key, value)
We use search to retrieve objects from the store by namespace.

# Search 
for m in in_memory_store.search(namespace_for_memory):
    print(m.dict())
{'value': {'user_name': 'Lance', 'interests': ['biking', 'technology', 'coffee']}, 'key': 'user_profile', 'namespace': ['1', 'memory'], 'created_at': '2024-11-04T23:37:34.871675+00:00', 'updated_at': '2024-11-04T23:37:34.871680+00:00'}
We can also use get to retrieve a specific object by namespace and key.

# Get the memory by namespace and key
profile = in_memory_store.get(namespace_for_memory, "user_profile")
profile.value
{'user_name': 'Lance', 'interests': ['biking', 'technology', 'coffee']}
Chatbot with profile schema
Now we know how to specify a schema for the memories and save it to the store.

Now, how do we actually create memories with this particular schema?

In our chatbot, we want to create memories from a user chat.

This is where the concept of structured outputs is useful.

LangChain's chat model interface has a with_structured_output method to enforce structured output.

This is useful when we want to enforce that the output conforms to a schema, and it parses the output for us.

_set_env("OPENAI_API_KEY")
Let's pass the UserProfile schema we created to the with_structured_output method.

We can then invoke the chat model with a list of messages and get a structured output that conforms to our schema.

from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0)

# Bind schema to model
model_with_structure = model.with_structured_output(UserProfile)

# Invoke the model to produce structured output that matches the schema
structured_output = model_with_structure.invoke([HumanMessage("My name is Lance, I like to bike.")])
structured_output
{'user_name': 'Lance', 'interests': ['biking']}
Now, let's use this with our chatbot.

This only requires minor changes to the write_memory function.

We use model_with_structure, as defined above, to produce a profile that matches our schema.

from IPython.display import Image, display

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.store.base import BaseStore

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig

# Chatbot instruction
MODEL_SYSTEM_MESSAGE = """You are a helpful assistant with memory that provides information about the user. 
If you have memory for this user, use it to personalize your responses.
Here is the memory (it may be empty): {memory}"""

# Create new memory from the chat history and any existing memory
CREATE_MEMORY_INSTRUCTION = """Create or update a user profile memory based on the user's chat history. 
This will be saved for long-term memory. If there is an existing memory, simply update it. 
Here is the existing memory (it may be empty): {memory}"""

def call_model(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Load memory from the store and use it to personalize the chatbot's response."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve memory from the store
    namespace = ("memory", user_id)
    existing_memory = store.get(namespace, "user_memory")

    # Format the memories for the system prompt
    if existing_memory and existing_memory.value:
        memory_dict = existing_memory.value
        formatted_memory = (
            f"Name: {memory_dict.get('user_name', 'Unknown')}\n"
            f"Interests: {', '.join(memory_dict.get('interests', []))}"
        )
    else:
        formatted_memory = None

    # Format the memory in the system prompt
    system_msg = MODEL_SYSTEM_MESSAGE.format(memory=formatted_memory)

    # Respond using memory as well as the chat history
    response = model.invoke([SystemMessage(content=system_msg)]+state["messages"])

    return {"messages": response}

def write_memory(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and save a memory to the store."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve existing memory from the store
    namespace = ("memory", user_id)
    existing_memory = store.get(namespace, "user_memory")

    # Format the memories for the system prompt
    if existing_memory and existing_memory.value:
        memory_dict = existing_memory.value
        formatted_memory = (
            f"Name: {memory_dict.get('user_name', 'Unknown')}\n"
            f"Interests: {', '.join(memory_dict.get('interests', []))}"
        )
    else:
        formatted_memory = None
        
    # Format the existing memory in the instruction
    system_msg = CREATE_MEMORY_INSTRUCTION.format(memory=formatted_memory)

    # Invoke the model to produce structured output that matches the schema
    new_memory = model_with_structure.invoke([SystemMessage(content=system_msg)]+state['messages'])

    # Overwrite the existing use profile memory
    key = "user_memory"
    store.put(namespace, key, new_memory)

# Define the graph
builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_node("write_memory", write_memory)
builder.add_edge(START, "call_model")
builder.add_edge("call_model", "write_memory")
builder.add_edge("write_memory", END)

# Store for long-term (across-thread) memory
across_thread_memory = InMemoryStore()

# Checkpointer for short-term (within-thread) memory
within_thread_memory = MemorySaver()

# Compile the graph with the checkpointer fir and store
graph = builder.compile(checkpointer=within_thread_memory, store=across_thread_memory)

# View
display(Image(graph.get_graph(xray=1).draw_mermaid_png()))

# We supply a thread ID for short-term (within-thread) memory
# We supply a user ID for long-term (across-thread) memory 
config = {"configurable": {"thread_id": "1", "user_id": "1"}}

# User input 
input_messages = [HumanMessage(content="Hi, my name is Lance and I like to bike around San Francisco and eat at bakeries.")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

Hi, my name is Lance and I like to bike around San Francisco and eat at bakeries.
================================== Ai Message ==================================

Hi Lance! It's great to meet you. Biking around San Francisco sounds like a fantastic way to explore the city, and there are so many amazing bakeries to try. Do you have any favorite bakeries or biking routes in the city?
Let's check the memory in the store.

We can see that the memory is a dictionary that matches our schema.

# Namespace for the memory to save
user_id = "1"
namespace = ("memory", user_id)
existing_memory = across_thread_memory.get(namespace, "user_memory")
existing_memory.value
{'user_name': 'Lance', 'interests': ['biking', 'bakeries', 'San Francisco']}
When can this fail?
with_structured_output is very useful, but what happens if we're working with a more complex schema?

Here's an example of a more complex schema, which we'll test below.

This is a Pydantic model that describes a user's preferences for communication and trust fall.

from typing import List, Optional

class OutputFormat(BaseModel):
    preference: str
    sentence_preference_revealed: str

class TelegramPreferences(BaseModel):
    preferred_encoding: Optional[List[OutputFormat]] = None
    favorite_telegram_operators: Optional[List[OutputFormat]] = None
    preferred_telegram_paper: Optional[List[OutputFormat]] = None

class MorseCode(BaseModel):
    preferred_key_type: Optional[List[OutputFormat]] = None
    favorite_morse_abbreviations: Optional[List[OutputFormat]] = None

class Semaphore(BaseModel):
    preferred_flag_color: Optional[List[OutputFormat]] = None
    semaphore_skill_level: Optional[List[OutputFormat]] = None

class TrustFallPreferences(BaseModel):
    preferred_fall_height: Optional[List[OutputFormat]] = None
    trust_level: Optional[List[OutputFormat]] = None
    preferred_catching_technique: Optional[List[OutputFormat]] = None

class CommunicationPreferences(BaseModel):
    telegram: TelegramPreferences
    morse_code: MorseCode
    semaphore: Semaphore

class UserPreferences(BaseModel):
    communication_preferences: CommunicationPreferences
    trust_fall_preferences: TrustFallPreferences

class TelegramAndTrustFallPreferences(BaseModel):
    pertinent_user_preferences: UserPreferences
Now, let's try extraction of this schema using the with_structured_output method.

from pydantic import ValidationError

# Bind schema to model
model_with_structure = model.with_structured_output(TelegramAndTrustFallPreferences)

# Conversation
conversation = """Operator: How may I assist with your telegram, sir?
Customer: I need to send a message about our trust fall exercise.
Operator: Certainly. Morse code or standard encoding?
Customer: Morse, please. I love using a straight key.
Operator: Excellent. What's your message?
Customer: Tell him I'm ready for a higher fall, and I prefer the diamond formation for catching.
Operator: Done. Shall I use our "Daredevil" paper for this daring message?
Customer: Perfect! Send it by your fastest carrier pigeon.
Operator: It'll be there within the hour, sir."""

# Invoke the model
try:
    model_with_structure.invoke(f"""Extract the preferences from the following conversation:
    <convo>
    {conversation}
    </convo>""")
except ValidationError as e:
    print(e)
1 validation error for TelegramAndTrustFallPreferences
pertinent_user_preferences.communication_preferences.semaphore
  Input should be a valid dictionary or instance of Semaphore [type=model_type, input_value=None, input_type=NoneType]
    For further information visit https://errors.pydantic.dev/2.9/v/model_type
If we naively extract more complex schemas, even using high capacity model like gpt-4o, it is prone to failure.

Trustcall for creating and updating profile schemas
As we can see, working with schemas can be tricky.

Complex schemas can be difficult to extract.

In addition, updating even simple schemas can pose challenges.

Consider our above chatbot.

We regenerated the profile schema from scratch each time we chose to save a new memory.

This is inefficient, potentially wasting model tokens if the schema contains a lot of information to re-generate each time.

Worse, we may loose information when regenerating the profile from scratch.

Addressing these problems is the motivation for TrustCall!

This is an open-source library for updating JSON schemas developed by one Will Fu-Hinthorn on the LangChain team.

It's motivated by exactly these challenges while working on memory.

Let's first show simple usage of extraction with TrustCall on this list of messages.

# Conversation
conversation = [HumanMessage(content="Hi, I'm Lance."), 
                AIMessage(content="Nice to meet you, Lance."), 
                HumanMessage(content="I really like biking around San Francisco.")]
We use create_extractor, passing in the model as well as our schema as a tool.

With TrustCall, can supply supply the schema in various ways.

For example, we can pass a JSON object / Python dictionary or Pydantic model.

Under the hood, TrustCall uses tool calling to produce structured output from an input list of messages.

To force Trustcall to produce structured output, we can include the schema name in the tool_choice argument.

We can invoke the extractor with the above conversation.

from trustcall import create_extractor

# Schema 
class UserProfile(BaseModel):
    """User profile schema with typed fields"""
    user_name: str = Field(description="The user's preferred name")
    interests: List[str] = Field(description="A list of the user's interests")

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0)

# Create the extractor
trustcall_extractor = create_extractor(
    model,
    tools=[UserProfile],
    tool_choice="UserProfile"
)

# Instruction
system_msg = "Extract the user profile from the following conversation"

# Invoke the extractor
result = trustcall_extractor.invoke({"messages": [SystemMessage(content=system_msg)]+conversation})
When we invoke the extractor, we get a few things:

messages: The list of AIMessages that contain the tool calls.
responses: The resulting parsed tool calls that match our schema.
response_metadata: Applicable if updating existing tool calls. It says which of the responses correspond to which of the existing objects.
for m in result["messages"]: 
    m.pretty_print()
================================== Ai Message ==================================
Tool Calls:
  UserProfile (call_spGGUsoaUFXU7oOrUNCASzfL)
 Call ID: call_spGGUsoaUFXU7oOrUNCASzfL
  Args:
    user_name: Lance
    interests: ['biking around San Francisco']
schema = result["responses"]
schema
[UserProfile(user_name='Lance', interests=['biking around San Francisco'])]
schema[0].model_dump()
{'user_name': 'Lance', 'interests': ['biking around San Francisco']}
result["response_metadata"]
[{'id': 'call_spGGUsoaUFXU7oOrUNCASzfL'}]
Let's see how we can use it to update the profile.

For updating, TrustCall takes a set of messages as well as the existing schema.

The central idea is that it prompts the model to produce a JSON Patch to update only the relevant parts of the schema.

This is less error-prone than naively overwriting the entire schema.

It's also more efficient since the model only needs to generate the parts of the schema that have changed.

We can save the existing schema as a dict.

We can use model_dump() to serialize a Pydantic model instance into a dict.

We pass it to the "existing" argument along with the schema name, UserProfile.

# Update the conversation
updated_conversation = [HumanMessage(content="Hi, I'm Lance."), 
                        AIMessage(content="Nice to meet you, Lance."), 
                        HumanMessage(content="I really like biking around San Francisco."),
                        AIMessage(content="San Francisco is a great city! Where do you go after biking?"),
                        HumanMessage(content="I really like to go to a bakery after biking."),]

# Update the instruction
system_msg = f"""Update the memory (JSON doc) to incorporate new information from the following conversation"""

# Invoke the extractor with the updated instruction and existing profile with the corresponding tool name (UserProfile)
result = trustcall_extractor.invoke({"messages": [SystemMessage(content=system_msg)]+updated_conversation}, 
                                    {"existing": {"UserProfile": schema[0].model_dump()}})  
for m in result["messages"]: 
    m.pretty_print()
================================== Ai Message ==================================
Tool Calls:
  UserProfile (call_WeZl0ACfQStxblim0ps8LNKT)
 Call ID: call_WeZl0ACfQStxblim0ps8LNKT
  Args:
    user_name: Lance
    interests: ['biking', 'visiting bakeries']
result["response_metadata"]
[{'id': 'call_WeZl0ACfQStxblim0ps8LNKT'}]
updated_schema = result["responses"][0]
updated_schema.model_dump()
{'user_name': 'Lance', 'interests': ['biking', 'visiting bakeries']}
LangSmith trace:

https://smith.langchain.com/public/229eae22-1edb-44c6-93e6-489124a43968/r

Now, let's also test Trustcall on the challenging schema that we saw earlier.

bound = create_extractor(
    model,
    tools=[TelegramAndTrustFallPreferences],
    tool_choice="TelegramAndTrustFallPreferences",
)

# Conversation
conversation = """Operator: How may I assist with your telegram, sir?
Customer: I need to send a message about our trust fall exercise.
Operator: Certainly. Morse code or standard encoding?
Customer: Morse, please. I love using a straight key.
Operator: Excellent. What's your message?
Customer: Tell him I'm ready for a higher fall, and I prefer the diamond formation for catching.
Operator: Done. Shall I use our "Daredevil" paper for this daring message?
Customer: Perfect! Send it by your fastest carrier pigeon.
Operator: It'll be there within the hour, sir."""

result = bound.invoke(
    f"""Extract the preferences from the following conversation:
<convo>
{conversation}
</convo>"""
)

# Extract the preferences
result["responses"][0]
TelegramAndTrustFallPreferences(pertinent_user_preferences=UserPreferences(communication_preferences=CommunicationPreferences(telegram=TelegramPreferences(preferred_encoding=[OutputFormat(preference='standard encoding', sentence_preference_revealed='standard encoding')], favorite_telegram_operators=None, preferred_telegram_paper=[OutputFormat(preference='Daredevil', sentence_preference_revealed='Daredevil')]), morse_code=MorseCode(preferred_key_type=[OutputFormat(preference='straight key', sentence_preference_revealed='straight key')], favorite_morse_abbreviations=None), semaphore=Semaphore(preferred_flag_color=None, semaphore_skill_level=None)), trust_fall_preferences=TrustFallPreferences(preferred_fall_height=[OutputFormat(preference='higher', sentence_preference_revealed='higher')], trust_level=None, preferred_catching_technique=[OutputFormat(preference='diamond formation', sentence_preference_revealed='diamond formation')])))
Trace:

https://smith.langchain.com/public/5cd23009-3e05-4b00-99f0-c66ee3edd06e/r

For more examples, you can see an overview video here.

Chatbot with profile schema updating
Now, let's bring Trustcall into our chatbot to create and update a memory profile.

from IPython.display import Image, display

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.base import BaseStore

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0)

# Schema 
class UserProfile(BaseModel):
    """ Profile of a user """
    user_name: str = Field(description="The user's preferred name")
    user_location: str = Field(description="The user's location")
    interests: list = Field(description="A list of the user's interests")

# Create the extractor
trustcall_extractor = create_extractor(
    model,
    tools=[UserProfile],
    tool_choice="UserProfile", # Enforces use of the UserProfile tool
)

# Chatbot instruction
MODEL_SYSTEM_MESSAGE = """You are a helpful assistant with memory that provides information about the user. 
If you have memory for this user, use it to personalize your responses.
Here is the memory (it may be empty): {memory}"""

# Extraction instruction
TRUSTCALL_INSTRUCTION = """Create or update the memory (JSON doc) to incorporate information from the following conversation:"""

def call_model(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Load memory from the store and use it to personalize the chatbot's response."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve memory from the store
    namespace = ("memory", user_id)
    existing_memory = store.get(namespace, "user_memory")

    # Format the memories for the system prompt
    if existing_memory and existing_memory.value:
        memory_dict = existing_memory.value
        formatted_memory = (
            f"Name: {memory_dict.get('user_name', 'Unknown')}\n"
            f"Location: {memory_dict.get('user_location', 'Unknown')}\n"
            f"Interests: {', '.join(memory_dict.get('interests', []))}"      
        )
    else:
        formatted_memory = None

    # Format the memory in the system prompt
    system_msg = MODEL_SYSTEM_MESSAGE.format(memory=formatted_memory)

    # Respond using memory as well as the chat history
    response = model.invoke([SystemMessage(content=system_msg)]+state["messages"])

    return {"messages": response}

def write_memory(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and save a memory to the store."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve existing memory from the store
    namespace = ("memory", user_id)
    existing_memory = store.get(namespace, "user_memory")
        
    # Get the profile as the value from the list, and convert it to a JSON doc
    existing_profile = {"UserProfile": existing_memory.value} if existing_memory else None
    
    # Invoke the extractor
    result = trustcall_extractor.invoke({"messages": [SystemMessage(content=TRUSTCALL_INSTRUCTION)]+state["messages"], "existing": existing_profile})
    
    # Get the updated profile as a JSON object
    updated_profile = result["responses"][0].model_dump()

    # Save the updated profile
    key = "user_memory"
    store.put(namespace, key, updated_profile)

# Define the graph
builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_node("write_memory", write_memory)
builder.add_edge(START, "call_model")
builder.add_edge("call_model", "write_memory")
builder.add_edge("write_memory", END)

# Store for long-term (across-thread) memory
across_thread_memory = InMemoryStore()

# Checkpointer for short-term (within-thread) memory
within_thread_memory = MemorySaver()

# Compile the graph with the checkpointer fir and store
graph = builder.compile(checkpointer=within_thread_memory, store=across_thread_memory)

# View
display(Image(graph.get_graph(xray=1).draw_mermaid_png()))

# We supply a thread ID for short-term (within-thread) memory
# We supply a user ID for long-term (across-thread) memory 
config = {"configurable": {"thread_id": "1", "user_id": "1"}}

# User input 
input_messages = [HumanMessage(content="Hi, my name is Lance")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

Hi, my name is Lance
================================== Ai Message ==================================

Hello, Lance! It's nice to meet you. How can I assist you today?
# User input 
input_messages = [HumanMessage(content="I like to bike around San Francisco")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

I like to bike around San Francisco
================================== Ai Message ==================================

That sounds like a great way to explore the city! San Francisco has some beautiful routes and views. Do you have any favorite trails or spots you like to visit while biking?
# Namespace for the memory to save
user_id = "1"
namespace = ("memory", user_id)
existing_memory = across_thread_memory.get(namespace, "user_memory")
existing_memory.dict()
{'value': {'user_name': 'Lance',
  'user_location': 'San Francisco',
  'interests': ['biking']},
 'key': 'user_memory',
 'namespace': ['memory', '1'],
 'created_at': '2024-11-04T23:51:17.662428+00:00',
 'updated_at': '2024-11-04T23:51:41.697652+00:00'}
# The user profile saved as a JSON object
existing_memory.value
{'user_name': 'Lance',
 'user_location': 'San Francisco',
 'interests': ['biking']}
# User input 
input_messages = [HumanMessage(content="I also enjoy going to bakeries")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

I also enjoy going to bakeries
================================== Ai Message ==================================

Biking and visiting bakeries sounds like a delightful combination! San Francisco has some fantastic bakeries. Do you have any favorites, or are you looking for new recommendations to try out?
Continue the conversation in a new thread.

# We supply a thread ID for short-term (within-thread) memory
# We supply a user ID for long-term (across-thread) memory 
config = {"configurable": {"thread_id": "2", "user_id": "1"}}

# User input 
input_messages = [HumanMessage(content="What bakeries do you recommend for me?")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

What bakeries do you recommend for me?
================================== Ai Message ==================================

Since you're in San Francisco and enjoy going to bakeries, here are a few recommendations you might like:

1. **Tartine Bakery** - Known for its delicious bread and pastries, it's a must-visit for any bakery enthusiast.
2. **B. Patisserie** - Offers a delightful selection of French pastries, including their famous kouign-amann.
3. **Arsicault Bakery** - Renowned for its croissants, which have been praised as some of the best in the country.
4. **Craftsman and Wolves** - Known for their inventive pastries and the "Rebel Within," a savory muffin with a soft-cooked egg inside.
5. **Mr. Holmes Bakehouse** - Famous for their cruffins and other creative pastries.

These spots should offer a great variety of treats for you to enjoy. Happy bakery hopping!
Trace:

https://smith.langchain.com/public/f45bdaf0-6963-4c19-8ec9-f4b7fe0f68ad/r

Studio
Screenshot 2024-10-30 at 11.26.31 AM.png

 
Memory Agent
Review
We created a chatbot that saves semantic memories to a single user profile or collection.

We introduced Trustcall as a way to update either schema.

Goals
Now, we're going to pull together the pieces we've learned to build an agent with long-term memory.

Our agent, task_mAIstro, will help us manage a ToDo list!

The chatbots we built previously always reflected on the conversation and saved memories.

task_mAIstro will decide when to save memories (items to our ToDo list).

The chatbots we built previously always saved one type of memory, a profile or a collection.

task_mAIstro can decide to save to either a user profile or a collection of ToDo items.

In addition semantic memory, task_mAIstro also will manage procedural memory.

This allows the user to update their preferences for creating ToDo items.

%%capture --no-stderr
%pip install -U langchain_openai langgraph trustcall langchain_core
import os, getpass

def _set_env(var: str):
    # Check if the variable is set in the OS environment
    env_value = os.environ.get(var)
    if not env_value:
        # If not set, prompt the user for input
        env_value = getpass.getpass(f"{var}: ")
    
    # Set the environment variable for the current process
    os.environ[var] = env_value

_set_env("LANGSMITH_API_KEY")
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "langchain-academy"
_set_env("OPENAI_API_KEY")
Visibility into Trustcall updates
Trustcall creates and updates JSON schemas.

What if we want visibility into the specific changes made by Trustcall?

For example, we saw before that Trustcall has some of its own tools to:

Self-correct from validation failures -- see trace example here
Update existing documents -- see trace example here
Visibility into these tools can be useful for the agent we're going to build.

Below, we'll show how to do this!

from pydantic import BaseModel, Field

class Memory(BaseModel):
    content: str = Field(description="The main content of the memory. For example: User expressed interest in learning about French.")

class MemoryCollection(BaseModel):
    memories: list[Memory] = Field(description="A list of memories about the user.")
We can add a listener to the Trustcall extractor.

This will pass runs from the extractor's execution to a class, Spy, that we will define.

Our Spy class will extract information about what tool calls were made by Trustcall.

from trustcall import create_extractor
from langchain_openai import ChatOpenAI

# Inspect the tool calls made by Trustcall
class Spy:
    def __init__(self):
        self.called_tools = []

    def __call__(self, run):
        # Collect information about the tool calls made by the extractor.
        q = [run]
        while q:
            r = q.pop()
            if r.child_runs:
                q.extend(r.child_runs)
            if r.run_type == "chat_model":
                self.called_tools.append(
                    r.outputs["generations"][0][0]["message"]["kwargs"]["tool_calls"]
                )

# Initialize the spy
spy = Spy()

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0)

# Create the extractor
trustcall_extractor = create_extractor(
    model,
    tools=[Memory],
    tool_choice="Memory",
    enable_inserts=True,
)

# Add the spy as a listener
trustcall_extractor_see_all_tool_calls = trustcall_extractor.with_listeners(on_end=spy)
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Instruction
instruction = """Extract memories from the following conversation:"""

# Conversation
conversation = [HumanMessage(content="Hi, I'm Lance."), 
                AIMessage(content="Nice to meet you, Lance."), 
                HumanMessage(content="This morning I had a nice bike ride in San Francisco.")]

# Invoke the extractor
result = trustcall_extractor.invoke({"messages": [SystemMessage(content=instruction)] + conversation})
# Messages contain the tool calls
for m in result["messages"]:
    m.pretty_print()
================================== Ai Message ==================================
Tool Calls:
  Memory (call_NkjwwJGjrgxHzTb7KwD8lTaH)
 Call ID: call_NkjwwJGjrgxHzTb7KwD8lTaH
  Args:
    content: Lance had a nice bike ride in San Francisco this morning.
# Responses contain the memories that adhere to the schema
for m in result["responses"]: 
    print(m)
content='Lance had a nice bike ride in San Francisco this morning.'
# Metadata contains the tool call  
for m in result["response_metadata"]: 
    print(m)
{'id': 'call_NkjwwJGjrgxHzTb7KwD8lTaH'}
# Update the conversation
updated_conversation = [AIMessage(content="That's great, did you do after?"), 
                        HumanMessage(content="I went to Tartine and ate a croissant."),                        
                        AIMessage(content="What else is on your mind?"),
                        HumanMessage(content="I was thinking about my Japan, and going back this winter!"),]

# Update the instruction
system_msg = """Update existing memories and create new ones based on the following conversation:"""

# We'll save existing memories, giving them an ID, key (tool name), and value
tool_name = "Memory"
existing_memories = [(str(i), tool_name, memory.model_dump()) for i, memory in enumerate(result["responses"])] if result["responses"] else None
existing_memories
[('0',
  'Memory',
  {'content': 'Lance had a nice bike ride in San Francisco this morning.'})]
# Invoke the extractor with our updated conversation and existing memories
result = trustcall_extractor_see_all_tool_calls.invoke({"messages": updated_conversation, 
                                                        "existing": existing_memories})
# Metadata contains the tool call  
for m in result["response_metadata"]: 
    print(m)
{'id': 'call_bF0w0hE4YZmGyDbuJVe1mh5H', 'json_doc_id': '0'}
{'id': 'call_fQAxxRypV914Xev6nJ9VKw3X'}
# Messages contain the tool calls
for m in result["messages"]:
    m.pretty_print()
================================== Ai Message ==================================
Tool Calls:
  Memory (call_bF0w0hE4YZmGyDbuJVe1mh5H)
 Call ID: call_bF0w0hE4YZmGyDbuJVe1mh5H
  Args:
    content: Lance had a nice bike ride in San Francisco this morning. Afterward, he went to Tartine and ate a croissant. He was also thinking about his trip to Japan and going back this winter.
  Memory (call_fQAxxRypV914Xev6nJ9VKw3X)
 Call ID: call_fQAxxRypV914Xev6nJ9VKw3X
  Args:
    content: Lance went to Tartine and ate a croissant. He was also thinking about his trip to Japan and going back this winter.
# Parsed responses
for m in result["responses"]:
    print(m)
content='Lance had a nice bike ride in San Francisco this morning. Afterward, he went to Tartine and ate a croissant. He was also thinking about his trip to Japan and going back this winter.'
content='Lance went to Tartine and ate a croissant. He was also thinking about his trip to Japan and going back this winter.'
# Inspect the tool calls made by Trustcall
spy.called_tools
[[{'name': 'PatchDoc',
   'args': {'json_doc_id': '0',
    'planned_edits': '1. Replace the existing content with the updated memory that includes the new activities: going to Tartine for a croissant and thinking about going back to Japan this winter.',
    'patches': [{'op': 'replace',
      'path': '/content',
      'value': 'Lance had a nice bike ride in San Francisco this morning. Afterward, he went to Tartine and ate a croissant. He was also thinking about his trip to Japan and going back this winter.'}]},
   'id': 'call_bF0w0hE4YZmGyDbuJVe1mh5H',
   'type': 'tool_call'},
  {'name': 'Memory',
   'args': {'content': 'Lance went to Tartine and ate a croissant. He was also thinking about his trip to Japan and going back this winter.'},
   'id': 'call_fQAxxRypV914Xev6nJ9VKw3X',
   'type': 'tool_call'}]]
def extract_tool_info(tool_calls, schema_name="Memory"):
    """Extract information from tool calls for both patches and new memories.
    
    Args:
        tool_calls: List of tool calls from the model
        schema_name: Name of the schema tool (e.g., "Memory", "ToDo", "Profile")
    """

    # Initialize list of changes
    changes = []
    
    for call_group in tool_calls:
        for call in call_group:
            if call['name'] == 'PatchDoc':
                changes.append({
                    'type': 'update',
                    'doc_id': call['args']['json_doc_id'],
                    'planned_edits': call['args']['planned_edits'],
                    'value': call['args']['patches'][0]['value']
                })
            elif call['name'] == schema_name:
                changes.append({
                    'type': 'new',
                    'value': call['args']
                })

    # Format results as a single string
    result_parts = []
    for change in changes:
        if change['type'] == 'update':
            result_parts.append(
                f"Document {change['doc_id']} updated:\n"
                f"Plan: {change['planned_edits']}\n"
                f"Added content: {change['value']}"
            )
        else:
            result_parts.append(
                f"New {schema_name} created:\n"
                f"Content: {change['value']}"
            )
    
    return "\n\n".join(result_parts)

# Inspect spy.called_tools to see exactly what happened during the extraction
schema_name = "Memory"
changes = extract_tool_info(spy.called_tools, schema_name)
print(changes)
Document 0 updated:
Plan: 1. Replace the existing content with the updated memory that includes the new activities: going to Tartine for a croissant and thinking about going back to Japan this winter.
Added content: Lance had a nice bike ride in San Francisco this morning. Afterward, he went to Tartine and ate a croissant. He was also thinking about his trip to Japan and going back this winter.

New Memory created:
Content: {'content': 'Lance went to Tartine and ate a croissant. He was also thinking about his trip to Japan and going back this winter.'}
Creating an agent
There are many different agent architectures to choose from.

Here, we'll implement something simple, a ReAct agent.

This agent will be a helpful companion for creating and managing a ToDo list.

This agent can make a decision to update three types of long-term memory:

(a) Create or update a user profile with general user information

(b) Add or update items in a ToDo list collection

(c) Update its own instructions on how to update items to the ToDo list

from typing import TypedDict, Literal

# Update memory tool
class UpdateMemory(TypedDict):
    """ Decision on what memory type to update """
    update_type: Literal['user', 'todo', 'instructions']
_set_env("OPENAI_API_KEY")
Graph definition
We add a simple router, route_message, that makes a binary decision to save memories.

The memory collection updating is handled by Trustcall in the write_memory node, as before!

import uuid
from IPython.display import Image, display

from datetime import datetime
from trustcall import create_extractor
from typing import Optional
from pydantic import BaseModel, Field

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import merge_message_runs, HumanMessage, SystemMessage

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore

from langchain_openai import ChatOpenAI

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0)

# User profile schema
class Profile(BaseModel):
    """This is the profile of the user you are chatting with"""
    name: Optional[str] = Field(description="The user's name", default=None)
    location: Optional[str] = Field(description="The user's location", default=None)
    job: Optional[str] = Field(description="The user's job", default=None)
    connections: list[str] = Field(
        description="Personal connection of the user, such as family members, friends, or coworkers",
        default_factory=list
    )
    interests: list[str] = Field(
        description="Interests that the user has", 
        default_factory=list
    )

# ToDo schema
class ToDo(BaseModel):
    task: str = Field(description="The task to be completed.")
    time_to_complete: Optional[int] = Field(description="Estimated time to complete the task (minutes).")
    deadline: Optional[datetime] = Field(
        description="When the task needs to be completed by (if applicable)",
        default=None
    )
    solutions: list[str] = Field(
        description="List of specific, actionable solutions (e.g., specific ideas, service providers, or concrete options relevant to completing the task)",
        min_items=1,
        default_factory=list
    )
    status: Literal["not started", "in progress", "done", "archived"] = Field(
        description="Current status of the task",
        default="not started"
    )

# Create the Trustcall extractor for updating the user profile 
profile_extractor = create_extractor(
    model,
    tools=[Profile],
    tool_choice="Profile",
)

# Chatbot instruction for choosing what to update and what tools to call 
MODEL_SYSTEM_MESSAGE = """You are a helpful chatbot. 

You are designed to be a companion to a user, helping them keep track of their ToDo list.

You have a long term memory which keeps track of three things:
1. The user's profile (general information about them) 
2. The user's ToDo list
3. General instructions for updating the ToDo list

Here is the current User Profile (may be empty if no information has been collected yet):
<user_profile>
{user_profile}
</user_profile>

Here is the current ToDo List (may be empty if no tasks have been added yet):
<todo>
{todo}
</todo>

Here are the current user-specified preferences for updating the ToDo list (may be empty if no preferences have been specified yet):
<instructions>
{instructions}
</instructions>

Here are your instructions for reasoning about the user's messages:

1. Reason carefully about the user's messages as presented below. 

2. Decide whether any of the your long-term memory should be updated:
- If personal information was provided about the user, update the user's profile by calling UpdateMemory tool with type `user`
- If tasks are mentioned, update the ToDo list by calling UpdateMemory tool with type `todo`
- If the user has specified preferences for how to update the ToDo list, update the instructions by calling UpdateMemory tool with type `instructions`

3. Tell the user that you have updated your memory, if appropriate:
- Do not tell the user you have updated the user's profile
- Tell the user them when you update the todo list
- Do not tell the user that you have updated instructions

4. Err on the side of updating the todo list. No need to ask for explicit permission.

5. Respond naturally to user user after a tool call was made to save memories, or if no tool call was made."""

# Trustcall instruction
TRUSTCALL_INSTRUCTION = """Reflect on following interaction. 

Use the provided tools to retain any necessary memories about the user. 

Use parallel tool calling to handle updates and insertions simultaneously.

System Time: {time}"""

# Instructions for updating the ToDo list
CREATE_INSTRUCTIONS = """Reflect on the following interaction.

Based on this interaction, update your instructions for how to update ToDo list items. 

Use any feedback from the user to update how they like to have items added, etc.

Your current instructions are:

<current_instructions>
{current_instructions}
</current_instructions>"""

# Node definitions
def task_mAIstro(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Load memories from the store and use them to personalize the chatbot's response."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve profile memory from the store
    namespace = ("profile", user_id)
    memories = store.search(namespace)
    if memories:
        user_profile = memories[0].value
    else:
        user_profile = None

    # Retrieve task memory from the store
    namespace = ("todo", user_id)
    memories = store.search(namespace)
    todo = "\n".join(f"{mem.value}" for mem in memories)

    # Retrieve custom instructions
    namespace = ("instructions", user_id)
    memories = store.search(namespace)
    if memories:
        instructions = memories[0].value
    else:
        instructions = ""
    
    system_msg = MODEL_SYSTEM_MESSAGE.format(user_profile=user_profile, todo=todo, instructions=instructions)

    # Respond using memory as well as the chat history
    response = model.bind_tools([UpdateMemory], parallel_tool_calls=False).invoke([SystemMessage(content=system_msg)]+state["messages"])

    return {"messages": [response]}

def update_profile(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and update the memory collection."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Define the namespace for the memories
    namespace = ("profile", user_id)

    # Retrieve the most recent memories for context
    existing_items = store.search(namespace)

    # Format the existing memories for the Trustcall extractor
    tool_name = "Profile"
    existing_memories = ([(existing_item.key, tool_name, existing_item.value)
                          for existing_item in existing_items]
                          if existing_items
                          else None
                        )

    # Merge the chat history and the instruction
    TRUSTCALL_INSTRUCTION_FORMATTED=TRUSTCALL_INSTRUCTION.format(time=datetime.now().isoformat())
    updated_messages=list(merge_message_runs(messages=[SystemMessage(content=TRUSTCALL_INSTRUCTION_FORMATTED)] + state["messages"][:-1]))

    # Invoke the extractor
    result = profile_extractor.invoke({"messages": updated_messages, 
                                         "existing": existing_memories})

    # Save the memories from Trustcall to the store
    for r, rmeta in zip(result["responses"], result["response_metadata"]):
        store.put(namespace,
                  rmeta.get("json_doc_id", str(uuid.uuid4())),
                  r.model_dump(mode="json"),
            )
    tool_calls = state['messages'][-1].tool_calls
    return {"messages": [{"role": "tool", "content": "updated profile", "tool_call_id":tool_calls[0]['id']}]}

def update_todos(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and update the memory collection."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Define the namespace for the memories
    namespace = ("todo", user_id)

    # Retrieve the most recent memories for context
    existing_items = store.search(namespace)

    # Format the existing memories for the Trustcall extractor
    tool_name = "ToDo"
    existing_memories = ([(existing_item.key, tool_name, existing_item.value)
                          for existing_item in existing_items]
                          if existing_items
                          else None
                        )

    # Merge the chat history and the instruction
    TRUSTCALL_INSTRUCTION_FORMATTED=TRUSTCALL_INSTRUCTION.format(time=datetime.now().isoformat())
    updated_messages=list(merge_message_runs(messages=[SystemMessage(content=TRUSTCALL_INSTRUCTION_FORMATTED)] + state["messages"][:-1]))

    # Initialize the spy for visibility into the tool calls made by Trustcall
    spy = Spy()
    
    # Create the Trustcall extractor for updating the ToDo list 
    todo_extractor = create_extractor(
    model,
    tools=[ToDo],
    tool_choice=tool_name,
    enable_inserts=True
    ).with_listeners(on_end=spy)

    # Invoke the extractor
    result = todo_extractor.invoke({"messages": updated_messages, 
                                    "existing": existing_memories})

    # Save the memories from Trustcall to the store
    for r, rmeta in zip(result["responses"], result["response_metadata"]):
        store.put(namespace,
                  rmeta.get("json_doc_id", str(uuid.uuid4())),
                  r.model_dump(mode="json"),
            )
        
    # Respond to the tool call made in task_mAIstro, confirming the update
    tool_calls = state['messages'][-1].tool_calls

    # Extract the changes made by Trustcall and add the the ToolMessage returned to task_mAIstro
    todo_update_msg = extract_tool_info(spy.called_tools, tool_name)
    return {"messages": [{"role": "tool", "content": todo_update_msg, "tool_call_id":tool_calls[0]['id']}]}

def update_instructions(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and update the memory collection."""
    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]
    
    namespace = ("instructions", user_id)

    existing_memory = store.get(namespace, "user_instructions")
        
    # Format the memory in the system prompt
    system_msg = CREATE_INSTRUCTIONS.format(current_instructions=existing_memory.value if existing_memory else None)
    new_memory = model.invoke([SystemMessage(content=system_msg)]+state['messages'][:-1] + [HumanMessage(content="Please update the instructions based on the conversation")])

    # Overwrite the existing memory in the store 
    key = "user_instructions"
    store.put(namespace, key, {"memory": new_memory.content})
    tool_calls = state['messages'][-1].tool_calls
    return {"messages": [{"role": "tool", "content": "updated instructions", "tool_call_id":tool_calls[0]['id']}]}

# Conditional edge
def route_message(state: MessagesState, config: RunnableConfig, store: BaseStore) -> Literal[END, "update_todos", "update_instructions", "update_profile"]:

    """Reflect on the memories and chat history to decide whether to update the memory collection."""
    message = state['messages'][-1]
    if len(message.tool_calls) ==0:
        return END
    else:
        tool_call = message.tool_calls[0]
        if tool_call['args']['update_type'] == "user":
            return "update_profile"
        elif tool_call['args']['update_type'] == "todo":
            return "update_todos"
        elif tool_call['args']['update_type'] == "instructions":
            return "update_instructions"
        else:
            raise ValueError

# Create the graph + all nodes
builder = StateGraph(MessagesState)

# Define the flow of the memory extraction process
builder.add_node(task_mAIstro)
builder.add_node(update_todos)
builder.add_node(update_profile)
builder.add_node(update_instructions)
builder.add_edge(START, "task_mAIstro")
builder.add_conditional_edges("task_mAIstro", route_message)
builder.add_edge("update_todos", "task_mAIstro")
builder.add_edge("update_profile", "task_mAIstro")
builder.add_edge("update_instructions", "task_mAIstro")

# Store for long-term (across-thread) memory
across_thread_memory = InMemoryStore()

# Checkpointer for short-term (within-thread) memory
within_thread_memory = MemorySaver()

# We compile the graph with the checkpointer and store
graph = builder.compile(checkpointer=within_thread_memory, store=across_thread_memory)

# View
display(Image(graph.get_graph(xray=1).draw_mermaid_png()))

# We supply a thread ID for short-term (within-thread) memory
# We supply a user ID for long-term (across-thread) memory 
config = {"configurable": {"thread_id": "1", "user_id": "Lance"}}

# User input to create a profile memory
input_messages = [HumanMessage(content="My name is Lance. I live in SF with my wife. I have a 1 year old daughter.")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

My name is Lance. I live in SF with my wife. I have a 1 year old daughter.
================================== Ai Message ==================================
Tool Calls:
  UpdateMemory (call_rOuw3bLYjFFKuSVWsIHF27k5)
 Call ID: call_rOuw3bLYjFFKuSVWsIHF27k5
  Args:
    update_type: user
================================= Tool Message =================================

updated profile
================================== Ai Message ==================================

Got it! How can I assist you today, Lance?
# User input for a ToDo
input_messages = [HumanMessage(content="My wife asked me to book swim lessons for the baby.")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

My wife asked me to book swim lessons for the baby.
================================== Ai Message ==================================
Tool Calls:
  UpdateMemory (call_VjLbRpbLqniJ8we2CNKQ0m3P)
 Call ID: call_VjLbRpbLqniJ8we2CNKQ0m3P
  Args:
    update_type: todo
================================= Tool Message =================================

New ToDo created:
Content: {'task': 'Book swim lessons for 1-year-old daughter.', 'time_to_complete': 30, 'solutions': ['Check local swim schools in SF', 'Look for baby swim classes online', 'Ask friends for recommendations'], 'status': 'not started'}
================================== Ai Message ==================================

I've added "Book swim lessons for your 1-year-old daughter" to your ToDo list. If you need any help with that, just let me know!
# User input to update instructions for creating ToDos
input_messages = [HumanMessage(content="When creating or updating ToDo items, include specific local businesses / vendors.")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

When creating or updating ToDo items, include specific local businesses / vendors.
================================== Ai Message ==================================
Tool Calls:
  UpdateMemory (call_22w3V3Krhjf8WxDeH9YrQILa)
 Call ID: call_22w3V3Krhjf8WxDeH9YrQILa
  Args:
    update_type: instructions
================================= Tool Message =================================

updated instructions
================================== Ai Message ==================================

Got it! I'll make sure to include specific local businesses or vendors in San Francisco when creating or updating your ToDo items. Let me know if there's anything else you need!
# Check for updated instructions
user_id = "Lance"

# Search 
for memory in across_thread_memory.search(("instructions", user_id)):
    print(memory.value)
{'memory': '<current_instructions>\nWhen creating or updating ToDo list items for Lance, include specific local businesses or vendors in San Francisco. For example, when adding a task like booking swim lessons, suggest local swim schools or classes in the area.\n</current_instructions>'}
# User input for a ToDo
input_messages = [HumanMessage(content="I need to fix the jammed electric Yale lock on the door.")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

I need to fix the jammed electric Yale lock on the door.
================================== Ai Message ==================================
Tool Calls:
  UpdateMemory (call_7ooNemi3d6qWMfjf2g2h97EF)
 Call ID: call_7ooNemi3d6qWMfjf2g2h97EF
  Args:
    update_type: todo
================================= Tool Message =================================

New ToDo created:
Content: {'task': 'Fix the jammed electric Yale lock on the door.', 'time_to_complete': 60, 'solutions': ['Contact a local locksmith in SF', "Check Yale's customer support for troubleshooting", 'Look for repair guides online'], 'status': 'not started'}

Document ed0af900-52fa-4f15-907c-1aed1e17b0ce updated:
Plan: Add specific local businesses or vendors to the solutions for booking swim lessons.
Added content: ['Check local swim schools in SF', 'Look for baby swim classes online', 'Ask friends for recommendations', 'Contact La Petite Baleen Swim School', 'Check with SF Recreation and Parks for classes']
================================== Ai Message ==================================

I've added "Fix the jammed electric Yale lock on the door" to your ToDo list. If you need any specific recommendations or help, feel free to ask!
# Namespace for the memory to save
user_id = "Lance"

# Search 
for memory in across_thread_memory.search(("todo", user_id)):
    print(memory.value)
{'task': 'Book swim lessons for 1-year-old daughter.', 'time_to_complete': 30, 'deadline': None, 'solutions': ['Check local swim schools in SF', 'Look for baby swim classes online', 'Ask friends for recommendations', 'Contact La Petite Baleen Swim School', 'Check with SF Recreation and Parks for classes'], 'status': 'not started'}
{'task': 'Fix the jammed electric Yale lock on the door.', 'time_to_complete': 60, 'deadline': None, 'solutions': ['Contact a local locksmith in SF', "Check Yale's customer support for troubleshooting", 'Look for repair guides online'], 'status': 'not started'}
# User input to update an existing ToDo
input_messages = [HumanMessage(content="For the swim lessons, I need to get that done by end of November.")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

For the swim lessons, I need to get that done by end of November.
================================== Ai Message ==================================
Tool Calls:
  UpdateMemory (call_6AbsrTps4EPyD0gKBzkMIC90)
 Call ID: call_6AbsrTps4EPyD0gKBzkMIC90
  Args:
    update_type: todo
================================= Tool Message =================================

Document ed0af900-52fa-4f15-907c-1aed1e17b0ce updated:
Plan: Add a deadline for the swim lessons task to ensure it is completed by the end of November.
Added content: 2024-11-30T23:59:59
================================== Ai Message ==================================

I've updated the swim lessons task with a deadline to be completed by the end of November. If there's anything else you need, just let me know!
We can see that Trustcall performs patching of the existing memory:

https://smith.langchain.com/public/4ad3a8af-3b1e-493d-b163-3111aa3d575a/r

# User input for a ToDo
input_messages = [HumanMessage(content="Need to call back City Toyota to schedule car service.")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

Need to call back City Toyota to schedule car service.
================================== Ai Message ==================================
Tool Calls:
  UpdateMemory (call_tDuYZL7njpwOkg2YMEcf6DDJ)
 Call ID: call_tDuYZL7njpwOkg2YMEcf6DDJ
  Args:
    update_type: todo
================================= Tool Message =================================

New ToDo created:
Content: {'task': 'Call back City Toyota to schedule car service.', 'time_to_complete': 10, 'solutions': ["Find City Toyota's contact number", 'Check car service availability', 'Prepare car details for service scheduling'], 'status': 'not started'}

Document a77482f0-d654-4b41-ab74-d6f2b343a969 updated:
Plan: Add specific local businesses or vendors to the solutions for fixing the jammed electric Yale lock.
Added content: Contact City Locksmith SF
================================== Ai Message ==================================

I've added "Call back City Toyota to schedule car service" to your ToDo list. If you need any assistance with that, just let me know!
# Namespace for the memory to save
user_id = "Lance"

# Search 
for memory in across_thread_memory.search(("todo", user_id)):
    print(memory.value)
{'task': 'Book swim lessons for 1-year-old daughter.', 'time_to_complete': 30, 'deadline': '2024-11-30T23:59:59', 'solutions': ['Check local swim schools in SF', 'Look for baby swim classes online', 'Ask friends for recommendations', 'Contact La Petite Baleen Swim School', 'Check with SF Recreation and Parks for classes'], 'status': 'not started'}
{'task': 'Fix the jammed electric Yale lock on the door.', 'time_to_complete': 60, 'deadline': None, 'solutions': ['Contact a local locksmith in SF', "Check Yale's customer support for troubleshooting", 'Look for repair guides online', 'Contact City Locksmith SF', 'Visit SF Lock and Key for assistance'], 'status': 'not started'}
{'task': 'Call back City Toyota to schedule car service.', 'time_to_complete': 10, 'deadline': None, 'solutions': ["Find City Toyota's contact number", 'Check car service availability', 'Prepare car details for service scheduling'], 'status': 'not started'}
Now we can create a new thread.

This creates a new session.

Profile, ToDos, and Instructions saved to long-term memory are accessed.

# We supply a thread ID for short-term (within-thread) memory
# We supply a user ID for long-term (across-thread) memory 
config = {"configurable": {"thread_id": "2", "user_id": "Lance"}}

# Chat with the chatbot
input_messages = [HumanMessage(content="I have 30 minutes, what tasks can I get done?")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

I have 30 minutes, what tasks can I get done?
================================== Ai Message ==================================

You can work on the following tasks that fit within your 30-minute timeframe:

1. **Book swim lessons for your 1-year-old daughter.** 
   - Estimated time to complete: 30 minutes
   - Solutions include checking local swim schools in SF, looking for baby swim classes online, asking friends for recommendations, contacting La Petite Baleen Swim School, or checking with SF Recreation and Parks for classes.

2. **Call back City Toyota to schedule car service.**
   - Estimated time to complete: 10 minutes
   - Solutions include finding City Toyota's contact number, checking car service availability, and preparing car details for service scheduling.

You can choose either of these tasks to complete within your available time.
# Chat with the chatbot
input_messages = [HumanMessage(content="Yes, give me some options to call for swim lessons.")]

# Run the graph
for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
================================ Human Message =================================

Yes, give me some options to call for swim lessons.
================================== Ai Message ==================================

Here are some options you can consider for booking swim lessons for your 1-year-old daughter in San Francisco:

1. **La Petite Baleen Swim School**: Known for their baby swim classes, you can contact them to inquire about their schedule and availability.

2. **SF Recreation and Parks**: They often offer swim classes for young children. Check their website or contact them for more information.

3. **Local Swim Schools**: Search for other local swim schools in SF that offer baby swim classes. You might find some good options nearby.

4. **Ask Friends for Recommendations**: Reach out to friends or family in the area who might have experience with swim lessons for young children.

These options should help you get started on booking swim lessons.
Trace:

https://smith.langchain.com/public/84768705-be91-43e4-8a6f-f9d3cee93782/r

Studio
Screenshot 2024-11-04 at 1.00.19 PM.png