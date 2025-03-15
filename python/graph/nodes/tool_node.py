from langchain_core.messages import AIMessage
from ..state import AgentState
from .tools import tools  # 保留這個導入，因為其他模組依賴它
from .tool_handlers.cache_handler import handle_cached_result
from .tool_handlers.limit_handler import handle_tool_limit
from .tool_handlers.tool_executor import execute_tool

def tools_node(state: AgentState) -> AgentState:
    """處理工具調用的主節點函數"""
    # 初始化狀態變數
    tool_usage_count = state.get("tool_usage_count", 0)
    tool_results_cache = state.get("tool_results_cache", {})
    max_tool_uses = state.get("max_tool_uses", 20)
    max_tokens = state.get("max_tokens", 10000)  # 設定一個默認的 tokens 上限

    # 從最後一條消息中提取工具調用信息
    last_message = state["messages"][-1]
    
    # 檢查是否為 AIMessage 並且有工具調用
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # 檢查是否達到工具使用上限或 tokens 上限
        limit_reached, limit_messages = handle_tool_limit(
            tool_usage_count, 
            max_tool_uses, 
            last_message.tool_calls,
            state["messages"],  # type: ignore
            max_tokens
        )
        
        if limit_reached:
            return {
                "messages": state["messages"] + limit_messages,
                "tool_usage_count": tool_usage_count,
                "tool_results_cache": tool_results_cache,
                "max_tool_uses": max_tool_uses,
                "max_tokens": max_tokens
            }
        
        # 提取工具名稱和參數
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_call_id = tool_call.get("id") or "unknown_id"
        
        # 檢查是否有緩存結果
        cache_key = f"{tool_name}:{str(tool_args)}"
        has_cache, cache_messages, updated_cache = handle_cached_result(
            state, 
            tool_name, 
            tool_args, 
            tool_call_id,
            tool_results_cache
        )
        
        if has_cache:
            return {
                "messages": state["messages"] + cache_messages,
                "tool_usage_count": tool_usage_count,
                "tool_results_cache": updated_cache,
                "max_tool_uses": max_tool_uses,
                "max_tokens": max_tokens
            }
        
        # 執行工具調用
        tool_messages, updated_cache, usage_increment = execute_tool(
            state["messages"], 
            tools, 
            cache_key, 
            tool_results_cache
        )
        
        return {
            "messages": state["messages"] + tool_messages,
            "tool_usage_count": tool_usage_count + usage_increment,
            "tool_results_cache": updated_cache,
            "max_tool_uses": max_tool_uses,
            "max_tokens": max_tokens
        }
    else:
        # 如果沒有工具調用，直接返回原始狀態
        return state
