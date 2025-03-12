from typing import Any


def parse_llm_response(content: Any) -> str:
    """解析 LLM 回應，處理不同的回應格式
    
    Args:
        content: LLM 回應內容，可能是字符串、列表或其他格式
        
    Returns:
        str: 解析後的字符串內容
    """
    if isinstance(content, str):
        return content
    
    if isinstance(content, list) and len(content) > 0:
        if isinstance(content[0], dict) and "text" in content[0]:
            return content[0]["text"]
        elif isinstance(content[0], str):
            return content[0]
    
    return str(content)
