from ..state import AgentState
from langchain_core.messages import HumanMessage
from ..utils.message_utils import convert_messages_to_str, extract_integrated_question
from ..utils.file_operations import get_current_file_path, update_markdown_file
from ..utils.response_parser import parse_llm_response
from ..chains.summary_chain import summary_chain


def summary_node(state: AgentState) -> AgentState:
    """處理消息並進行智能歷史摘要，並將摘要覆蓋到當前編輯的 Markdown 文件。
    
    Args:
        state: 包含消息歷史的代理狀態
        
    Returns:
        更新後的代理狀態，包含整合後的問題
    """
    # 1. 轉換消息歷史為字符串
    original_messages = state["messages"]
    summarized_messages = convert_messages_to_str(original_messages)
    
    # 2. 使用摘要鏈生成摘要
    response = summary_chain.invoke({"messages": summarized_messages})
    
    # 3. 解析 LLM 回應
    parsed_content = parse_llm_response(response.content)
    integrated_question = extract_integrated_question(parsed_content)
    
    # 4. 更新當前編輯的文件
    current_file_path = get_current_file_path()
    if current_file_path:
        update_markdown_file(current_file_path, integrated_question)
    
    return {"messages": [HumanMessage(content=integrated_question)]}
