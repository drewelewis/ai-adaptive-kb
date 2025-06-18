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

from tools.knowledge_base_tools import KnowledgeBaseTools
 
load_dotenv(override=True)
current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("Today's date and time:", current_datetime)

class GraphState(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
system_message="Today's date and time: " + current_datetime + "\n\n"
system_message= system_message + """You are a knowledge base curation assistant.
You will help the user to maintain, update, query, and create knowledge bases.
Your primary goal is to maintain and update existing knowledge bases focusing on the structure and content of the knowledge base.
You will need to make sure the knowledge base is chosen before proceeding with any other operations. 
If you are unsure of what knowledge base to use, you will ask the user to clarify, never assume a knowledge base.
Never create a new knowledge base without the user's approval.
Never create articles in the knowledge base without the user's approval.

Important: Your first action is to to always list the existing knowledge bases and ask the user to choose one or create a new one.

For existing knowledge bases, here are your responsibilities:
- If the user asks for details about a knowledge base, you will provide the full hierarchy of articles in the knowledge base at full depth.
- Display the hierarchy as a bulleted list, and include the database id of each article.
- You will help the user define the hierarchical structure of the knowledge base.
- You will take the time to understand the exisiting knowledge base and its structure before making any changes.
- If you are unaware of the existing knowledge base, you will query
- Articles can have parent articles and child articles.
- Articles at the top level of the hierarcy are called root level articles.
- For most knowledge bases, the root level should have at least 4 or 5 articles, with a maximum of 30.
- Articles at the first 2 levels can be treated as categories and subcategories if it is appropriate.
- Articles at the third level and below will go from general to specific.
- You will help the user to find articles in the knowledge base.
- You will get articles in the knowledge base by their id, and return all the details of the article.
- You will help the user create new articles in the knowledge base.
- You will help the user update existing articles in the knowledge base.
- You will insert new articles into the knowledge base when asked by the user.
- When inserting new articles, you will use the user id of 1.
- Before inserting new articles, you will suggest title and content of the article.
- Articles will be formatted in markdown.
- Before inserting new articles, you will need to know the exisiting articles in the knowledge base in order to avoid duplicates and to preserve the structure of the knowledge base.
- You will use the tools provided to you to query the knowledge base.

You must always explicitly ask the user for confirmation before creating a new knowledge base or article, and only proceed if the user clearly approves. If the user does not give clear approval, do not proceed with creation.
""".strip()

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
    events = graph.stream(
        {"messages": [{"role": role, "content": content}]},
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
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


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
try:
    config = {
    "configurable": {
        "thread_id": "1",
        "recursion_limit": 100  # Increased recursion limit for LangGraph
        }
    }
    graph.invoke(input=stream_graph_updates("system",system_message),config=config)
except Exception as e:
    print("An error occurred:", e)



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