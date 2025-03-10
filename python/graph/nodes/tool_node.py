from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool


search = TavilySearchResults(max_results=1)

@tool
def web_search(query: str):
    """Search the web for the query."""
    return search.invoke({"query": query})


tools = [web_search]
