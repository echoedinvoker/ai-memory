from langgraph.prebuilt import ToolNode
from ..state import AgentState
from .tools import tools

def tools_node(state: AgentState) -> AgentState:
    messages = ToolNode(tools).invoke(state["messages"])
    return {"messages": state["messages"] + messages}
