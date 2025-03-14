from langgraph.prebuilt import ToolNode

def execute_tool(
    messages: list, 
    tools: list, 
    cache_key: str, 
    tool_results_cache: dict
) -> tuple[list, dict, int]:
    """執行工具調用並更新緩存
    
    Returns:
        tuple: (工具消息列表, 更新後的緩存, 工具使用增量)
    """
    # 調用工具
    tool_messages = ToolNode(tools).invoke(messages)
    
    # 緩存結果
    if tool_messages and len(tool_messages) > 0:
        tool_results_cache[cache_key] = tool_messages[0].content
    
    return tool_messages, tool_results_cache, 1  # 返回消息、緩存和使用計數增量
