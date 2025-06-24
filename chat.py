import sys

import os
import json
import datetime
import uuid
from time import sleep
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.utils.function_calling import format_tool_to_openai_function

from langchain_openai import AzureChatOpenAI
from IPython.display import Image, display

from utils.langgraph_utils import save_graph
from dotenv import load_dotenv
from prompts.knowledge_base_prompts import prompts
from tools.knowledge_base_tools import KnowledgeBaseTools
 
load_dotenv(override=True)
current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    recursions: int


# Define recursion limit
MAX_RECURSIONS = 25


system_message="Today's date and time: " + current_datetime + "\n\n"
system_message= system_message + prompts.master_prompt()

llm  = AzureChatOpenAI(
    azure_endpoint=os.getenv('OPENAI_API_ENDPOINT'),
    azure_deployment=os.getenv('OPENAI_API_MODEL_DEPLOYMENT_NAME'),
    api_version=os.getenv('OPENAI_API_VERSION'),
    streaming=True
)


kb_tools = KnowledgeBaseTools()


tools= kb_tools.tools()
llm_with_tools = llm.bind_tools(tools)

def stream_graph_updates(role: str, content: str):
    config = {"configurable": {"thread_id": "1"}}
    
    events = graph.stream(
        {
            "messages": [{"role": role, "content": content}],
            "recursions": 0},
        config,
        stream_mode="values",
    )
    
    for event in events:
        # print(event)
        if "messages" in event:
            last_message = event["messages"][-1]
            # Only print non-tool messages (hide tool calls and tool responses)
            # Check for ToolMessage type or messages with tool_calls
            if hasattr(last_message, '__class__'):
                message_type = last_message.__class__.__name__
                if message_type in ['ToolMessage']:
                    continue  # Skip tool messages
            
            # Also skip AI messages that contain tool calls (but show the final response)
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                continue  # Skip messages with tool calls
                
            # Print all other messages (user messages and AI responses without tool calls)
            last_message.pretty_print()

        last_message=event["messages"][-1]
    return last_message


# Define Nodes
def chat_node(state: GraphState):

    # Extract the current list of messages from the state
    messages = state["messages"]
    recursions= state["recursions"]

    # Check recursion limit
    if recursions >= MAX_RECURSIONS:
        print(f"  - Recursion limit of {MAX_RECURSIONS} reached. Ending conversation.")
        return {"messages": [{"role": "assistant", "content": f"I've reached the maximum recursion limit of {MAX_RECURSIONS}. Please start a new conversation."}], "recursions": recursions}

    # Print the current state for debugging
    # print("chat_node: Current state:")
    # print(f"  - Messages: {messages}")
    print(f"  - Recursions: {recursions}")

    # Print the incoming messages for debugging
    # print("chat_node: Received messages:")
    # for msg in messages:
        # print(f"  - {msg}")    # Invoke the LLM with tools, passing the current messages
    response = llm_with_tools.invoke(messages)

    # Print the response from the LLM for debugging
    # print("chat_node: LLM response:")
    # print(response.content)
    
    # Return the updated state with the new message appended
    return {"messages": [response], "recursions": recursions + 1}


def should_continue(state: GraphState):
    """Determine whether to continue with tools or end based on recursion limit and tool calls."""
    recursions = state["recursions"]
    
    # If we've hit the recursion limit, end the conversation
    if recursions >= MAX_RECURSIONS:
        return END
    
    # Otherwise, use the standard tools_condition to decide
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    else:
        return END


# Global memory saver for state management
memory = MemorySaver()

# Init Graph
def build_graph():
    global memory
    graph_builder = StateGraph(GraphState)
    graph_builder.add_node("chat_node", chat_node)
    graph_builder.add_edge(START, "chat_node")

    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_conditional_edges(
        "chat_node",
        should_continue,
    )
    graph_builder.add_edge("tools", "chat_node")
    graph = graph_builder.compile(checkpointer=memory)

    image_path = __file__.replace(".py", ".png")
    save_graph(image_path,graph)
    
    return graph

def clear_conversation_state():
    """Clear all conversation state from memory."""
    global memory, graph
    
    try:
        # Clear the memory saver by creating a new instance
        memory = MemorySaver()
        # Rebuild the graph with the new memory
        graph = build_graph()
        print("✓ Conversation state cleared successfully.")
        print("✓ Memory reset complete.")
        print("✓ Ready for new conversation.")
    except Exception as e:
        print(f"⚠ Error clearing state: {e}")
        print("You may need to restart the application for a complete reset.")

graph=build_graph()



def main():
    print("=" * 60)
    print("=" * 60)
    print("=" * 60)
    print("🤖 AI Knowledge Base Chat started!")
    print("Commands:")
    print("  • Type '/q' or '/quit' to exit")
    print("  • Type '/reset' or '/r' to clear conversation state and start fresh")
    print("  • Type your question or command to interact with the AI")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("> ")
            print("")
            
            if user_input.lower() in ["/q", "/quit"]:
                print("👋 Goodbye!")
                break
                
            elif user_input.lower() in ["/reset", "/r"]:
                print("🔄 Clearing conversation state and starting new conversation...")
                clear_conversation_state()
                print("=" * 60)
                continue
            
            # Process normal user input
            ai_message = stream_graph_updates("user", user_input)
            
            # Check if we need to suggest a reset due to recursion limit
            if hasattr(ai_message, 'content') and "recursion limit" in str(ai_message.content).lower():
                print("\n💡 Tip: Type '/reset' to start a new conversation with a fresh context.")
            
            # print(ai_message.content)

        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user. Type '/q' to quit properly.")
            continue
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            print("💡 Tip: Type '/reset' to start a new conversation or '/q' to quit.")
            continue

if __name__ == "__main__":
    main()