from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_anthropic import ChatAnthropic
from ..nodes.tool_node import tools
from ..prompts.code_expert import SYSTEM_PROMPT


prompt = ChatPromptTemplate.from_messages([
    ( 'system', SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest", # type: ignore
    temperature=0,
    max_tokens=8096, # type: ignore
    timeout=None,
    max_retries=2,
    ) # type: ignore

llm_with_tools = llm.bind_tools(tools)

chain = prompt | llm_with_tools
