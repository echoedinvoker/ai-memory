from typing import Sequence
from langchain_core.messages import BaseMessage
from ..chains.basic_chain import chain


def llm_node(messages: Sequence[BaseMessage]):
    return chain.invoke({"messages": messages})
