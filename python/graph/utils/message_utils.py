from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

def convert_messages_to_str(messages: list[BaseMessage]) -> str:
    """將 LangChain 消息列表轉換為字符串格式"""
    history = ""
    for message in messages:
        if isinstance(message, AIMessage):
            history += f"AI:\n{message.content}\n\n"
        elif isinstance(message, HumanMessage):
            history += f"User:\n{message.content}\n\n"
    return history


def extract_integrated_question(response_text: str) -> str:
    """從摘要回應中提取整合後的問題"""
    marker = "整合後的新問題:"
    
    marker_index = response_text.find(marker)
    
    if marker_index != -1:
        extracted_question = response_text[marker_index + len(marker):].strip()
        return extracted_question
    
    return response_text
