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
# from langgraph.prebuilt import ToolNode  # Commented out due to import issue
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
    consecutive_tool_calls: int  # Track consecutive tool calls
    last_tool_result: str  # Track the last tool result to avoid repetition


# Define recursion limit
MAX_RECURSIONS = 15  # Reduced from 25 to catch issues earlier
SOFT_RECURSION_LIMIT = 8  # Warning threshold

system_message="Today's date and time: " + current_datetime + "\n\n"
system_message= system_message + prompts.master_prompt()
system_message= system_message + "\n\nIMPORTANT: When inserting articles, never include an 'id' field in the article object. The database automatically generates unique IDs."
system_message= system_message + "\n\nEFFICIENCY GUIDELINES:\n- Minimize tool usage - only call tools when absolutely necessary\n- After calling tools, provide a complete response rather than additional tool calls\n- If you need multiple operations, try to accomplish them in fewer tool calls\n- Always aim to give a final answer after using tools"

llm  = AzureChatOpenAI(
    azure_endpoint=os.getenv('OPENAI_API_ENDPOINT'),
    azure_deployment=os.getenv('OPENAI_API_MODEL_DEPLOYMENT_NAME'),
    api_version=os.getenv('OPENAI_API_VERSION'),
    streaming=True
)


kb_tools = KnowledgeBaseTools()

# Manual ToolNode implementation (workaround for missing langgraph.prebuilt.ToolNode)
class ToolNode:
    """Manual implementation of ToolNode functionality with loop prevention"""
    
    def __init__(self, tools):
        self.tools_by_name = {tool.name: tool for tool in tools}
        self.recent_results = {}  # Cache recent results to detect loops
    
    def __call__(self, state):
        """Execute tools based on the last AI message's tool calls"""
        messages = state.get("messages", [])
        if not messages:
            return {"messages": []}
        
        last_message = messages[-1]
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            return {"messages": []}
        
        tool_messages = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            
            # Create a key for caching to detect repeated identical calls
            cache_key = f"{tool_name}:{str(sorted(tool_args.items()) if isinstance(tool_args, dict) else tool_args)}"
            
            if tool_name in self.tools_by_name:
                try:
                    # Check if we've seen this exact call recently
                    if cache_key in self.recent_results:
                        # Return cached result with a note about repetition
                        cached_result = self.recent_results[cache_key]
                        tool_message = ToolMessage(
                            content=f"{cached_result}\n\n[Note: This appears to be a repeated call - consider providing a final answer instead of making more tool calls]",
                            tool_call_id=tool_call_id,
                            name=tool_name
                        )
                        tool_messages.append(tool_message)
                    else:
                        # Execute the tool normally
                        tool = self.tools_by_name[tool_name]
                        result = tool.invoke(tool_args)
                        result_str = str(result)
                        
                        # Cache the result
                        self.recent_results[cache_key] = result_str
                        
                        # Keep cache size manageable
                        if len(self.recent_results) > 10:
                            # Remove oldest entry
                            oldest_key = next(iter(self.recent_results))
                            del self.recent_results[oldest_key]
                        
                        tool_message = ToolMessage(
                            content=result_str,
                            tool_call_id=tool_call_id,
                            name=tool_name
                        )
                        tool_messages.append(tool_message)
                        
                except Exception as e:
                    error_message = ToolMessage(
                        content=f"Error executing {tool_name}: {str(e)}",
                        tool_call_id=tool_call_id,
                        name=tool_name
                    )
                    tool_messages.append(error_message)
            else:
                error_message = ToolMessage(
                    content=f"Tool {tool_name} not found",
                    tool_call_id=tool_call_id,
                    name=tool_name
                )
                tool_messages.append(error_message)
        
        return {"messages": tool_messages}


tools= kb_tools.tools()
llm_with_tools = llm.bind_tools(tools)

def stream_graph_updates(role: str, content: str):
    config = {"configurable": {"thread_id": "1"}}
    
    events = graph.stream(
        {
            "messages": [{"role": role, "content": content}],
            "recursions": 0,
            "consecutive_tool_calls": 0},  # Initialize new state fields
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
    recursions = state["recursions"]
    consecutive_tool_calls = state.get("consecutive_tool_calls", 0)
    
    # Check recursion limit
    if recursions >= MAX_RECURSIONS:
        print(f"  - Recursion limit of {MAX_RECURSIONS} reached. Ending conversation.")
        return {"messages": [{"role": "assistant", "content": f"I've reached the maximum recursion limit of {MAX_RECURSIONS}. Please start a new conversation."}], "recursions": recursions}

    # Soft warning for approaching limit
    if recursions >= SOFT_RECURSION_LIMIT:
        efficiency_reminder = "\n\nREMINDER: You're approaching the recursion limit. Focus on providing a complete final response."
        # Add efficiency reminder to system context
        messages_with_reminder = messages + [{"role": "system", "content": efficiency_reminder}]
    else:
        messages_with_reminder = messages

    # Warning for too many consecutive tool calls
    if consecutive_tool_calls >= 3:
        tool_warning = "\n\nWARNING: You've made several consecutive tool calls. Provide a comprehensive final answer now instead of calling more tools."
        messages_with_reminder = messages_with_reminder + [{"role": "system", "content": tool_warning}]

    # Print the current state for debugging
    print(f"  - Recursions: {recursions}, Consecutive tool calls: {consecutive_tool_calls}")

    # Invoke the LLM with tools, passing the current messages
    response = llm_with_tools.invoke(messages_with_reminder)
    
    # Track if this response has tool calls
    has_tool_calls = hasattr(response, 'tool_calls') and response.tool_calls
    new_consecutive_calls = consecutive_tool_calls + 1 if has_tool_calls else 0
    
    # Return the updated state with the new message appended
    return {
        "messages": [response], 
        "recursions": recursions + 1,
        "consecutive_tool_calls": new_consecutive_calls
    }


def should_continue(state: GraphState):
    """Determine whether to continue with tools or end based on recursion limit and tool calls."""
    recursions = state["recursions"]
    consecutive_tool_calls = state.get("consecutive_tool_calls", 0)
    
    # If we've hit the recursion limit, end the conversation
    if recursions >= MAX_RECURSIONS:
        return END
    
    # Force stop if too many consecutive tool calls (likely stuck in loop)
    if consecutive_tool_calls >= 4:
        print(f"  - Stopping due to {consecutive_tool_calls} consecutive tool calls (likely loop)")
        return END
    
    # Check for tool calls in the last message
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