from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from ..state import AgentState


search = TavilySearchResults(max_results=1)

@tool
def web_search(query: str):
    """Search the web for the query."""
    return search.invoke({"query": query})

tools = [web_search]

def tools_node(state: AgentState) -> AgentState:
    messages = ToolNode(tools).invoke(state["messages"])
    return {"messages": state["messages"] + messages}
    
