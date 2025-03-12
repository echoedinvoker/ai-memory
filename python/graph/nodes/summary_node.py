from ..state import AgentState
from langchain_core.messages import HumanMessage
from ..utils.message_utils import convert_messages_to_str, extract_integrated_question
from ..chains.summary_chain import summary_chain
import os
import sys


def summary_node(state: AgentState) -> AgentState:
    """處理消息並進行智能歷史摘要，並將摘要覆蓋到當前編輯的 Markdown 文件。
    
    Args:
        state: 包含消息歷史的代理狀態
        
    Returns:
        更新後的代理狀態，包含整合後的問題
    """
    original_messages = state["messages"]
    
    summarized_messages = convert_messages_to_str(original_messages)

    response = summary_chain.invoke({"messages": summarized_messages})

    content = response.content
    if isinstance(content, str):
        integrated_question = extract_integrated_question(content)
    else:
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                integrated_question = extract_integrated_question(content[0]["text"])
            elif isinstance(content[0], str):
                integrated_question = extract_integrated_question(content[0])
            else:
                integrated_question = str(content)
        else:
            integrated_question = str(content)
    
    # 獲取當前文件路徑（如果在命令行參數中提供）
    current_file_path = ""
    if len(sys.argv) > 1:
        current_file_path = sys.argv[1]
    
    # 如果有文件路徑，則將整合後的問題寫入文件
    if current_file_path and os.path.exists(current_file_path):
        try:
            # 讀取文件內容以保留系統提示（如果有）
            with open(current_file_path, 'r') as file:
                content = file.read()
            
            # 寫入新內容：系統提示（如果有）+ Human: + 整合後的問題
            with open(current_file_path, 'w') as file:
                file.write(f"Human:\n{integrated_question}\n")
            
            # 輸出信號，讓 Neovim 端知道文件已更新
            print("FILE_UPDATED")
        except Exception as e:
            print(f"ERROR: Failed to update file: {str(e)}")
    
    return {"messages": [HumanMessage(content=integrated_question)]}
