from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_anthropic import ChatAnthropic
from ..nodes.tool_node import tools


prompt = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="messages")
])

llm = ChatAnthropic(model_name="claude-3-7-sonnet-latest", timeout=10, stop=[])
llm_with_tools = llm.bind_tools(tools)

chain = prompt | llm_with_tools
