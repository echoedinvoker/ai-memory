Human:

File: /home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/summary_node.py
```python
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
```
上面 node 生成 integrated_question 之後會一次性的將其內容寫入到 markdown 文件中, 能不能幫我改成流式接收llm的reponse, 並將其逐步寫入到文件中, 以增加使用者體驗, 不然使用者會有一段等待的時間會開始疑惑 app 到底是不是正常運作中

AI:
# 需求理解

您希望改進 `summary_node` 函數，將其從一次性接收 LLM 回應並寫入文件，改為流式接收 LLM 回應並逐步寫入文件。這樣可以提升用戶體驗，讓用戶能夠看到實時的進度，而不是在等待過程中懷疑應用是否正常運作。

## 資訊收集

首先，我需要了解更多關於現有代碼的上下文和相關函數的實現。讓我查看一下目錄結構，以便找到正確的文件路徑：現在我需要查看相關的文件內容：讓我嘗試正確的路徑：讓我再次檢查目錄結構，確保我找到正確的文件路徑：現在我找到了正確的路徑，讓我查看相關文件：讓我嘗試查看 graph 目錄下的文件：現在我找到了正確的路徑，讓我查看相關文件：## 解決方案概述

根據收集到的資訊，我將實現一個流式接收 LLM 回應並逐步寫入文件的解決方案。主要改進點包括：

1. 使用 LangChain 的流式 API（`stream` 方法）來接收 LLM 的實時回應
2. 創建一個新的函數 `update_markdown_file_stream`，支持逐步更新文件內容
3. 修改 `summary_node` 函數，使用流式處理替代原來的批量處理

這個解決方案將顯著提升用戶體驗，因為用戶可以看到文件內容的實時更新，而不是等待整個處理完成。

## 程式碼實現

首先，我們需要在 `file_operations.py` 中添加一個新的函數來支持流式更新文件：

```python
# /home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/utils/file_operations.py

import os
import sys


def get_current_file_path() -> str:
    """獲取當前編輯的文件路徑（從命令行參數）
    
    Returns:
        str: 當前文件路徑，如果未提供則返回空字符串
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    return ""


def update_markdown_file(file_path: str, content: str) -> bool:
    """更新 Markdown 文件內容
    
    Args:
        file_path: 要更新的文件路徑
        content: 要寫入的新內容
        
    Returns:
        bool: 操作是否成功
    """
    if not file_path or not os.path.exists(file_path):
        print(f"ERROR: File does not exist: {file_path}")
        return False
    
    try:
        with open(file_path, 'w') as file:
            file.write(f"Human:\n{content}\n")
        
        print("FILE_UPDATED")
        return True
    except Exception as e:
        print(f"ERROR: Failed to update file: {str(e)}")
        return False


def update_markdown_file_stream(file_path: str, initial_content: str = "") -> callable:
    """創建一個可以流式更新 Markdown 文件的函數
    
    Args:
        file_path: 要更新的文件路徑
        initial_content: 初始內容
        
    Returns:
        callable: 一個接受新內容塊的函數，用於更新文件
    """
    if not file_path or not os.path.exists(file_path):
        print(f"ERROR: File does not exist: {file_path}")
        return lambda _: False
    
    # 初始化文件
    try:
        with open(file_path, 'w') as file:
            file.write(f"Human:\n{initial_content}")
        
        current_content = initial_content
        
        def update_with_chunk(chunk: str) -> bool:
            nonlocal current_content
            current_content += chunk
            
            try:
                with open(file_path, 'w') as file:
                    file.write(f"Human:\n{current_content}\n")
                return True
            except Exception as e:
                print(f"ERROR: Failed to update file with chunk: {str(e)}")
                return False
        
        return update_with_chunk
    except Exception as e:
        print(f"ERROR: Failed to initialize file: {str(e)}")
        return lambda _: False
```

然後，我們需要修改 `summary_node.py` 文件，實現流式處理：

```python
# /home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/summary_node.py

from ..state import AgentState
from langchain_core.messages import HumanMessage
from ..utils.message_utils import convert_messages_to_str, extract_integrated_question
from ..utils.file_operations import get_current_file_path, update_markdown_file_stream
from ..utils.response_parser import parse_llm_response
from ..chains.summary_chain import summary_chain
from ..models.llm_config import summary_llm
from ..prompts.summary_prompt import summarize_prompt


def summary_node(state: AgentState) -> AgentState:
    """處理消息並進行智能歷史摘要，並將摘要流式寫入到當前編輯的 Markdown 文件。
    
    Args:
        state: 包含消息歷史的代理狀態
        
    Returns:
        更新後的代理狀態，包含整合後的問題
    """
    # 1. 轉換消息歷史為字符串
    original_messages = state["messages"]
    summarized_messages = convert_messages_to_str(original_messages)
    
    # 2. 獲取當前編輯的文件路徑
    current_file_path = get_current_file_path()
    
    # 3. 準備流式處理
    if current_file_path:
        # 初始化文件，開始時為空
        update_stream = update_markdown_file_stream(current_file_path, "正在生成摘要...")
    
    # 4. 使用 LLM 直接流式生成摘要
    prompt = summarize_prompt.format(messages=summarized_messages)
    full_response = ""
    
    # 流式處理 LLM 回應
    for chunk in summary_llm.stream(prompt.to_messages()):
        chunk_content = chunk.content if chunk.content else ""
        full_response += chunk_content
        
        # 如果有文件路徑，則更新文件
        if current_file_path and chunk_content:
            # 嘗試提取整合後的問題（即使是部分回應）
            partial_integrated = extract_integrated_question(full_response)
            update_stream(partial_integrated)
    
    # 5. 從完整回應中提取整合後的問題
    integrated_question = extract_integrated_question(full_response)
    
    # 6. 確保最終內容已更新到文件
    if current_file_path:
        update_stream(integrated_question)
        print("STREAMING_COMPLETE")
    
    return {"messages": [HumanMessage(content=integrated_question)]}
```

## 使用說明

這個改進後的代碼不需要任何額外的設置或配置。它將自動使用流式處理來更新 Markdown 文件，提供更好的用戶體驗。

主要改進點：

1. 當 LLM 開始生成回應時，文件會立即顯示 "正在生成摘要..."，讓用戶知道處理已經開始
2. 隨著 LLM 生成更多內容，文件會實時更新，用戶可以看到生成過程
3. 即使在生成過程中，代碼也會嘗試提取整合後的問題，確保文件內容有意義

## 進一步改進建議

1. **錯誤處理增強**：可以添加更多的錯誤處理和恢復機制，確保在網絡問題或 LLM 服務中斷時能夠優雅地處理
   
2. **進度指示器**：可以在文件中添加一個進度指示器（如 "生成中..."），當完成時自動移除

3. **取消機制**：實現一個取消機制，允許用戶在生成過程中取消操作

4. **緩存部分結果**：如果生成過程中斷，可以保存已生成的部分結果，避免完全重新開始

5. **自適應更新頻率**：根據生成速度動態調整文件更新頻率，避免過於頻繁的 I/O 操作

6. **異步處理**：將整個處理改為異步（使用 `async/await`），可以進一步提高響應性

這些改進將使流式處理更加健壯和用戶友好，提供更好的整體體驗。

Human:

