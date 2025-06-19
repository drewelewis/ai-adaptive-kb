import sys

import os
import json
import datetime
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
            event["messages"][-1].pretty_print()

        last_message=event["messages"][-1]
    return last_message


# Define Nodes
def chat_node(state: GraphState):

    # Extract the current list of messages from the state
    messages = state["messages"]
    recursions= state["recursions"]

    # Print the current state for debugging
    # print("chat_node: Current state:")
    # print(f"  - Messages: {messages}")
    print(f"  - Recursions: {recursions}")

    # Print the incoming messages for debugging
    # print("chat_node: Received messages:")
    # for msg in messages:
        # print(f"  - {msg}")

    # Invoke the LLM with tools, passing the current messages
    response = llm_with_tools.invoke(messages)

    # Print the response from the LLM for debugging
    # print("chat_node: LLM response:")
    print(response.content)

    # Return the updated state with the new message appended
    return {"messages": [response], "recursions": recursions + 1}


# Init Graph
def build_graph():

    memory = MemorySaver()
    graph_builder = StateGraph(GraphState)
    graph_builder.add_node("chat_node", chat_node)
    graph_builder.add_edge(START, "chat_node")

    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_conditional_edges(
    "chat_node",
    tools_condition,
    )
    graph_builder.add_edge("tools", "chat_node")
    graph = graph_builder.compile(checkpointer=memory)



    image_path = __file__.replace(".py", ".png")
    save_graph(image_path,graph)
    
    return graph

graph=build_graph()



def main():
    
    while True:
        try:
            user_input = input("> ")
            print("")
            if user_input.lower() in ["/q"]:
                break
            ai_message=stream_graph_updates("user",user_input)
            # print(ai_message.content)

        except Exception as e:
            print("An error occurred:", e)
            break

if __name__ == "__main__":
    main()