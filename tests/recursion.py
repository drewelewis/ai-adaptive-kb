from langgraph.graph import StateGraph, END
from typing import TypedDict

# Define the state schema
class ChatState(TypedDict):
    count: int
    last_message: str

# Define a simple state
default_state: ChatState = {"count": 0, "last_message": ""}

# Define node A
def node_a(state):
    user_input = input("[A] You: ")
    if user_input.strip().lower() == "/quit":
        print("[A] Exiting chat.")
        return END
    state["count"] += 1
    state["last_message"] = user_input
    print(f"[A] Bot: You said '{user_input}' (message #{state['count']})")
    return "node_b"

# Define node B
def node_b(state):
    user_input = input("[B] You: ")
    if user_input.strip().lower() == "/quit":
        print("[B] Exiting chat.")
        return END
    state["count"] += 1
    state["last_message"] = user_input
    print(f"[B] Bot: You said '{user_input}' (message #{state['count']})")
    return "node_a"

# Build the graph
graph = StateGraph(ChatState)  # Pass the state schema here
graph.add_node("node_a", node_a)
graph.add_node("node_b", node_b)
graph.set_entry_point("node_a")
graph.set_finish_point(END)

# Compile and run
compiled = graph.compile()
compiled.invoke(default_state)
