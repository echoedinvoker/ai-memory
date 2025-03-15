from typing import Optional, Union, Dict, Any, List
from langchain_core.messages import ToolMessage, BaseMessage
import tiktoken

def calculate_tokens(text: str) -> int:
    """計算文本的 tokens 數量
    
    Args:
        text: 要計算 tokens 的文本
        
    Returns:
        int: tokens 數量
    """
    try:
        # 使用 tiktoken 計算 tokens 數量
        encoding = tiktoken.get_encoding("cl100k_base")  # 使用 OpenAI 的編碼器
        num_tokens = len(encoding.encode(text))
        print(f"tokens 數量: {num_tokens}")
        return num_tokens
    except ImportError:
        # 如果沒有安裝 tiktoken，使用簡單的估算方法
        # 英文大約每 4 個字符為 1 個 token，中文每個字符約為 1.5 個 token
        # 這只是一個粗略的估計
        return len(text) // 2

def extract_content_from_messages(messages: List[Union[BaseMessage, Dict[str, Any]]]) -> str:
    """從所有 messages 中提取 content 並合併成一個字串
    
    Args:
        messages: 消息列表，可以是 BaseMessage 對象或字典
        
    Returns:
        str: 合併後的字串
    """
    all_content = []
    
    for message in messages:
        # 處理 BaseMessage 對象
        if hasattr(message, 'content'):
            content = message.content
            
            # 如果 content 是字串，直接添加
            if isinstance(content, str):
                all_content.append(content)
            # 如果 content 是 list of dict，提取每個 dict 中的 text
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        all_content.append(item["text"])
                    elif isinstance(item, dict) and "content" in item:
                        all_content.append(item["content"])
        
        # 處理字典類型的消息
        elif isinstance(message, dict):
            # 嘗試從字典中提取 content
            if "content" in message:
                content = message["content"]
                if isinstance(content, str):
                    all_content.append(content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            all_content.append(item["text"])
                        elif isinstance(item, dict) and "content" in item:
                            all_content.append(item["content"])
    
    # 合併所有 content
    return " ".join(all_content)

def handle_tool_limit(
    tool_usage_count: int, 
    max_tool_uses: int, 
    tool_calls: list,
    messages: Optional[List[Union[BaseMessage, Dict[str, Any]]]] = None,
    max_tokens: int = 50000  # 設定一個默認的 tokens 上限
) -> tuple[bool, list]:
    """處理工具使用次數限制
    
    Args:
        tool_usage_count: 當前工具使用次數
        max_tool_uses: 最大工具使用次數
        tool_calls: 工具調用列表
        messages: 所有消息列表，用於計算 tokens
        max_tokens: 最大 tokens 數量
        
    Returns:
        tuple: (是否達到限制, 工具消息列表)
    """
    # 檢查是否達到工具使用次數上限
    if tool_usage_count >= max_tool_uses and tool_calls:
        tool_messages = []
        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id", "unknown_id")
            tool_message = ToolMessage(
                content=f"已達到工具使用上限({max_tool_uses}次)。請根據已有信息回答，或者重新組織問題。",
                tool_call_id=tool_call_id
            )
            tool_messages.append(tool_message)
        
        return True, tool_messages
    
    # 檢查是否達到 tokens 上限
    if messages:
        try:
            # 提取所有 messages 的 content 並合併成一個字串
            all_content = extract_content_from_messages(messages)
            # 計算 tokens 數量
            tokens_count = calculate_tokens(all_content)
            
            # 如果達到 tokens 上限，返回一個格式正確的 ToolMessage
            if tokens_count >= max_tokens and tool_calls:
                tool_messages = []
                for tool_call in tool_calls:
                    tool_call_id = tool_call.get("id", "unknown_id")
                    tool_message = ToolMessage(
                        content=f"已達到 tokens 上限({max_tokens} tokens)。請根據已有信息回答，或者重新組織問題。",
                        tool_call_id=tool_call_id
                    )
                    tool_messages.append(tool_message)
                
                return True, tool_messages
        except Exception as e:
            # 如果在處理 messages 時出現錯誤，記錄錯誤並繼續
            print(f"處理 messages 時出現錯誤: {e}")
    
    return False, []  # 未達到限制
