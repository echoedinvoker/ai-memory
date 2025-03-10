from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import END, MessageGraph
from langgraph.prebuilt import ToolNode, tools_condition
from .nodes.basic_node import llm_node
from .constants import BASIC
from .nodes.tool_node import tools


builder = MessageGraph()

builder.add_node(BASIC, llm_node)
builder.add_node("tools", ToolNode(tools))

builder.set_entry_point(BASIC)
builder.add_edge("tools", BASIC)
builder.add_conditional_edges(
    BASIC,
    tools_condition,
    {
        "tools": "tools",
        "__end__": END,
    }
)

graph = builder.compile()


if __name__ == "__main__":
    graph.invoke([
        ('human', 'What is weather of Taipei?'),
    ])
