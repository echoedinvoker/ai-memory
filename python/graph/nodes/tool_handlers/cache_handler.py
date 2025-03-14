from langchain_core.messages import ToolMessage
from ...state import AgentState

def handle_cached_result(
    state: AgentState, 
    tool_name: str, 
    tool_args: dict, 
    tool_call_id: str,
    tool_results_cache: dict
) -> tuple[bool, list, dict]:
    """處理緩存的工具調用結果
    
    Returns:
        tuple: (是否有緩存, 工具消息列表, 更新後的緩存)
    """
    # 檢查是否有緩存結果
    cache_key = f"{tool_name}:{str(tool_args)}"
    if cache_key in tool_results_cache:
        # 使用緩存結果而不是重新調用工具
        tool_message = ToolMessage(
            content=f"[使用緩存結果] {tool_results_cache[cache_key]}",
            tool_call_id=tool_call_id
        )
        
        return True, [tool_message], tool_results_cache
    
    return False, [], tool_results_cache  # 沒有緩存結果
