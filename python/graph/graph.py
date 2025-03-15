from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition
from python.graph.nodes.basic_node import llm_node
from python.graph.constants import BASIC, TOOLS, NEW_QUESTION
from python.graph.nodes.tool_node import tools_node
from python.graph.state import AgentState


def new_question_node(state: AgentState) -> AgentState:
    return state


builder = StateGraph(AgentState)

builder.add_node(BASIC, llm_node)
builder.add_node(TOOLS, tools_node)
builder.add_node(NEW_QUESTION, new_question_node)

builder.set_entry_point(BASIC)
builder.add_conditional_edges(
    BASIC,
    tools_condition,
    {
        "tools": TOOLS,
        "__end__": END,
    }
)

def route_from_tools(state: AgentState) -> str:
    if state["total_tokens"] > state["max_tokens"]:
        return NEW_QUESTION
    return BASIC

builder.add_conditional_edges(
    TOOLS,
    route_from_tools,
    {
        BASIC: BASIC,
        NEW_QUESTION: NEW_QUESTION
    }
)

builder.add_edge(NEW_QUESTION, END)

graph = builder.compile()


if __name__ == "__main__":
    graph.invoke({
        "messages": [
            HumanMessage(content="What is weather of Taipei?")
        ]
    })
