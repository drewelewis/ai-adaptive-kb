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
from langchain_community.tools.tavily_search import TavilySearchResults

from utils.langgraph_utils import save_graph
from dotenv import load_dotenv


from tools.github_tools import GithubTools
from tools.tekton_tools import ElasticsearchTools

load_dotenv(override=True)
current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("Today's date and time:", current_datetime)

class GraphState(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
system_message="Today's date and time: " + current_datetime + "\n\n"
system_message= system_message + """You are an application support agent.  
You will help developers with their questions about the application.
You will use the tools available to you to answer the user's questions.
Application logs are stored in an ElasticSearch index.
You can search for code in a GitHub repository.
You can get a list of repositories from a GitHub user account autonomously.
You can get a list of files in a GitHub repository autonomously.
You can get the content of a file in a GitHub repository autonomously.
You can use the calculator to perform calculations.
When possible, use your tools to answer the user's questions.
If there is no tool available or you are unsure of which tool to use, ask for clarifying questions.
Here are some default values for the tools you can use:

If you are not given a GitHub user, you can use the default user name drewelewis
You can verify with the user if they want to use a different user name.
The default repo is drewelewis/ContosoBankAPI
If you are asked to search for code in a GitHub repository, the default query is def main
If you dont have the user_name and repository, you can ask the user for it.

""".strip()
def get_llm():
    """Get the LLM instance."""
    return AzureChatOpenAI(
        azure_endpoint=os.getenv('OPENAI_API_ENDPOINT'),
        azure_deployment=os.getenv('OPENAI_API_MODEL_DEPLOYMENT_NAME'),
        api_version=os.getenv('OPENAI_API_VERSION'),
        temperature=0,
        streaming=True
    )


github_tools = GithubTools()
elasticsearch_tools = ElasticsearchTools()

# tools= calculator_tools.tools + github_tools.tools + elasticsearch_tools.tools 
# llm_with_tools = get_llm.bind_tools(tools)
proxy_agent_llm=get_llm()
github_agent_llm=get_llm().bind_tools(github_tools.tools)
elastic_search_agent_llm=get_llm().bind_tools(elasticsearch_tools.tools)

# Define Nodes
def proxy_agent(state: GraphState):
    return {"messages": [proxy_agent_llm.invoke(state["messages"])]}

def github_agent(state: GraphState):
    return {"messages": [github_agent_llm.invoke(state["messages"])]}

def elastic_search_agent(state: GraphState):
    return {"messages": [elastic_search_agent_llm.invoke(state["messages"])]}

# Init Graph
def build_graph():

    memory = MemorySaver()
    graph_builder = StateGraph(GraphState)
    graph_builder.add_node("proxy_agent", proxy_agent)
    graph_builder.add_node("github_agent", github_agent)
    graph_builder.add_node("elastic_search_agent", elastic_search_agent)
    
    graph_builder.add_edge(START, "proxy_agent")

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


def stream_graph_updates(role: str, content: str):
    config = {"configurable": {"thread_id": "1"}}
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

def main():

    for _ in range(0, 3):
        sleep(0.5)
        print(".")
    print("How can I help you? (type '/q' to exit)")
    stream_graph_updates("system",system_message)
    
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