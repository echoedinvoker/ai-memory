from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from ..state import AgentState
from .tools import tools

def tools_node(state: AgentState) -> AgentState:
    tool_usage_count = state.get("tool_usage_count", 0)
    tool_results_cache = state.get("tool_results_cache", {})
    max_tool_uses = state.get("max_tool_uses", 20)

    # 從最後一條消息中提取工具調用信息
    last_message = state["messages"][-1]
    
    # 檢查是否為 AIMessage 並且有工具調用
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # 如果達到上限，返回一個格式正確的 ToolMessage
        if tool_usage_count >= max_tool_uses:
            tool_messages = []
            for tool_call in last_message.tool_calls:
                tool_call_id = tool_call.get("id", "unknown_id")
                # 創建一個 ToolMessage 而不是 AIMessage
                tool_message = ToolMessage(
                    content=f"已達到工具使用上限({max_tool_uses}次)。請根據已有信息回答，或者重新組織問題。",
                    tool_call_id=tool_call_id
                )
                tool_messages.append(tool_message)
            
            return {
                "messages": state["messages"] + tool_messages,
                "tool_usage_count": tool_usage_count,
                "tool_results_cache": tool_results_cache,
                "max_tool_uses": max_tool_uses
            }
        
        tool_name = None
        tool_args = {}
        
        # 提取工具名稱和參數
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        
        # 檢查是否有緩存結果
        cache_key = f"{tool_name}:{str(tool_args)}"
        if cache_key in tool_results_cache:
            # 使用緩存結果而不是重新調用工具
            # 注意：這裡需要創建正確格式的 ToolMessage
            tool_messages = []
            for tool_call in last_message.tool_calls:
                tool_call_id = tool_call.get("id", "unknown_id")
                tool_message = ToolMessage(
                    content=f"[使用緩存結果] {tool_results_cache[cache_key]}",
                    tool_call_id=tool_call_id
                )
                tool_messages.append(tool_message)
            
            return {
                "messages": state["messages"] + tool_messages,
                "tool_usage_count": tool_usage_count,
                "tool_results_cache": tool_results_cache,
                "max_tool_uses": max_tool_uses
            }
        else:
            # 調用工具並更新計數器
            messages = ToolNode(tools).invoke(state["messages"])
            # 緩存結果
            if messages and len(messages) > 0:
                tool_results_cache[cache_key] = messages[0].content
            tool_usage_count += 1
            
            return {
                "messages": state["messages"] + messages,
                "tool_usage_count": tool_usage_count,
                "tool_results_cache": tool_results_cache,
                "max_tool_uses": max_tool_uses
            }
    else:
        # 如果沒有工具調用，直接返回原始狀態
        return state
