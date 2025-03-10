from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition
from .nodes.basic_node import llm_node
from .constants import BASIC, TOOLS
from .nodes.tool_node import tools_node
from .state import AgentState


builder = StateGraph(AgentState)

builder.add_node(BASIC, llm_node)
builder.add_node(TOOLS, tools_node)

builder.set_entry_point(BASIC)
builder.add_edge(TOOLS, BASIC)
builder.add_conditional_edges(
    BASIC,
    tools_condition,
    {
        "tools": TOOLS,
        "__end__": END,
    }
)

graph = builder.compile()


if __name__ == "__main__":
    graph.invoke({
        "messages": [
            HumanMessage(content="What is weather of Taipei?")
        ]
    })
