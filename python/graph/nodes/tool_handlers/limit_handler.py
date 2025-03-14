from langchain_core.messages import AIMessage, ToolMessage

def handle_tool_limit(
    tool_usage_count: int, 
    max_tool_uses: int, 
    tool_calls: list
) -> tuple[bool, list]:
    """處理工具使用次數限制
    
    Returns:
        tuple: (是否達到限制, 工具消息列表)
    """
    # 如果達到上限，返回一個格式正確的 ToolMessage
    if tool_usage_count >= max_tool_uses and tool_calls:
        tool_messages = []
        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id", "unknown_id")
            # 創建一個 ToolMessage 而不是 AIMessage
            tool_message = ToolMessage(
                content=f"已達到工具使用上限({max_tool_uses}次)。請根據已有信息回答，或者重新組織問題。",
                tool_call_id=tool_call_id
            )
            tool_messages.append(tool_message)
        
        return True, tool_messages
    
    return False, []  # 未達到限制
