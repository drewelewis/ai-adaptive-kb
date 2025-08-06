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
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.utils.function_calling import format_tool_to_openai_function

from langchain_openai import AzureChatOpenAI
from IPython.display import Image, display

from utils.langgraph_utils import save_graph
from dotenv import load_dotenv
from prompts.knowledge_base_prompts import prompts
from tools.knowledge_base_tools import KnowledgeBaseTools
from tools.github_tools import GithubTools
 
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

system_message = f"""Today's date and time: {current_datetime}

{prompts.master_prompt()}

GITHUB INTEGRATION CAPABILITIES:
You also have access to GitHub tools that allow you to:
- Get a list of repositories for any GitHub user
- Browse files and directory structure in any public GitHub repository
- Read the content of specific files in GitHub repositories
- Create issues in GitHub repositories (with proper permissions)

When working with GitHub:
- Always start by getting the user's repositories if they want to work with their own code
- Use the file listing tool before trying to read specific files
- Repository names should be in the format 'username/repository-name'
- Be helpful in exploring codebases and understanding project structures
- You can help analyze code, documentation, and project organization

INTEGRATED WORKFLOW:
You can now help users with both knowledge base management AND GitHub repository exploration:
- Document code from GitHub repositories into knowledge bases
- Create knowledge base articles about GitHub projects
- Help organize development documentation
- Analyze and summarize code from repositories
- Create issues based on knowledge base content or analysis

Always ask for clarification if you're unsure whether the user wants to work with knowledge bases, GitHub repositories, or both.
"""

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv('OPENAI_API_ENDPOINT'),
    azure_deployment=os.getenv('OPENAI_API_MODEL_DEPLOYMENT_NAME'),
    api_version=os.getenv('OPENAI_API_VERSION'),
    streaming=True
)

kb_tools = KnowledgeBaseTools()
github_tools = GithubTools()

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


# Combine knowledge base and GitHub tools
tools = kb_tools.tools() + github_tools.tools()
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
        if "messages" in event:
            last_message = event["messages"][-1]
            # Only print non-tool messages (hide tool calls and tool responses)
            if hasattr(last_message, '__class__'):
                message_type = last_message.__class__.__name__
                if message_type in ['ToolMessage']:
                    continue  # Skip tool messages
            
            # Also skip AI messages that contain tool calls (but show the final response)
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                continue  # Skip messages with tool calls
                
            # Print all other messages (user messages and AI responses without tool calls)
            last_message.pretty_print()

        last_message = event["messages"][-1]
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
    save_graph(image_path, graph)
    
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

graph = build_graph()


def main():
    print("=" * 70)
    print("🤖 AI KNOWLEDGE BASE & GITHUB INTEGRATION CHAT")
    print("=" * 70)
    print("🎯 Capabilities:")
    print("   📚 Knowledge Base Management - Create, update, and organize knowledge bases")
    print("   🐙 GitHub Integration - Explore repositories, read files, and create issues")
    print("   🔄 Integrated Workflows - Document code, analyze projects, and more!")
    print("=" * 70)
    
    # Count available tools
    kb_tool_count = len(kb_tools.tools())
    github_tool_count = len(github_tools.tools())
    total_tools = kb_tool_count + github_tool_count
    
    print(f"🛠️  Available Tools: {total_tools} total")
    print(f"   • Knowledge Base Tools: {kb_tool_count}")
    print(f"   • GitHub Tools: {github_tool_count}")
    print("=" * 70)
    print("💬 Commands:")
    print("   • Type '/q' or '/quit' to exit")
    print("   • Type '/reset' or '/r' to clear conversation state and start fresh")
    print("   • Type '/tools' to show tool status")
    print("   • Type your question or command to interact with the AI")
    print("   • Ask about knowledge bases, GitHub repositories, or both!")
    print("=" * 70)
    
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
                print("=" * 70)
                continue
            
            elif user_input.lower() in ["/tools"]:
                print("🛠️  Tool Status:")
                print(f"   • Knowledge Base Tools: {len(kb_tools.tools())} available")
                print(f"   • GitHub Tools: {len(github_tools.tools())} available")
                print(f"   • Total Tools: {len(tools)} available")
                print(f"   • Max Recursions: {MAX_RECURSIONS}")
                print(f"   • Soft Limit Warning: {SOFT_RECURSION_LIMIT}")
                continue
            
            # Process normal user input
            ai_message = stream_graph_updates("user", user_input)
            
            # Check if we need to suggest a reset due to recursion limit
            if hasattr(ai_message, 'content') and "recursion limit" in str(ai_message.content).lower():
                print("\n💡 Tip: Type '/reset' to start a new conversation with a fresh context.")

        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user. Type '/q' to quit properly.")
            continue
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            print("💡 Tip: Type '/reset' to start a new conversation or '/q' to quit.")
            continue

if __name__ == "__main__":
    main()
