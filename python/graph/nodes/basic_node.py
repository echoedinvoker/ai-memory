from ..chains.basic_chain import chain
from ..state import AgentState


def llm_node(state: AgentState) -> AgentState:
    message = chain.invoke({"messages": state["messages"]})
    return {"messages": state["messages"] + [message]}

