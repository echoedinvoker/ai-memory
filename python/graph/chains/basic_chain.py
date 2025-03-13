from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from ..nodes.tool_node import tools
from ..prompts.code_expert import SYSTEM_PROMPT
from ..models.llm_config import slow_llm


prompt = ChatPromptTemplate.from_messages([
    ( 'system', SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

llm_with_tools = slow_llm.bind_tools(tools)

chain = prompt | llm_with_tools
