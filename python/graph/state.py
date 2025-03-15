from typing import Any, Dict, TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: list[BaseMessage]
    tool_usage_count: int  # 跟踪工具使用次數
    tool_results_cache: Dict[str, Any]  # 緩存工具結果以避免重複調用
    max_tool_uses: int  # 最大工具使用次數限制
    max_tokens: int  # tokens 上限
