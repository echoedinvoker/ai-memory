Human:


File: /home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/tool_node.py
```python
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
    max_tokens = state.get("max_tokens", 50000)  # 設定一個默認的 tokens 上限

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
```

我希望這個 node 會 return 計算的 total tokens,應該在 handle_tool_limit 中已經有做這個計算, 只是沒有 return 出來, AgentState 也需要新增這個 key


AI:
# 需求理解

您希望在 `tools_node` 函數中返回計算的總 tokens 數量，這個計算應該已經在 `handle_tool_limit` 函數中完成，但目前沒有返回出來。您需要修改 `AgentState` 以添加一個新的 key 來存儲這個值，並確保它在函數返回時包含在狀態中。

讓我先查看相關的代碼文件，特別是 `handle_tool_limit` 函數，以了解它如何計算 tokens。現在讓我查看 `AgentState` 的定義，以了解如何添加新的 key：讓我查看 `execute_tool` 函數的實現，以了解完整的工具執行流程：# 資訊收集

從代碼分析中，我發現：

1. `handle_tool_limit` 函數中已經實現了 tokens 計算功能，使用 `calculate_tokens` 函數計算所有消息的 tokens 總數。
2. 目前 `AgentState` 類型定義中已經有 `max_tokens` 字段，但沒有存儲當前 tokens 計數的字段。
3. `handle_tool_limit` 函數計算了 tokens 數量，但沒有將這個值返回，只是用於判斷是否超過限制。

# 解決方案概述

我將進行以下修改：

1. 更新 `AgentState` 類型定義，添加 `total_tokens` 字段。
2. 修改 `handle_tool_limit` 函數，使其返回計算的 tokens 數量。
3. 更新 `tools_node` 函數，接收 tokens 計數並在返回的狀態中包含它。

# 程式碼實現

## 1. 修改 AgentState 類型定義 (state.py)

```python
from typing import Any, Dict, TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: list[BaseMessage]
    tool_usage_count: int  # 跟踪工具使用次數
    tool_results_cache: Dict[str, Any]  # 緩存工具結果以避免重複調用
    max_tool_uses: int  # 最大工具使用次數限制
    max_tokens: int  # tokens 上限
    total_tokens: int  # 當前使用的 tokens 總數
```

## 2. 修改 handle_tool_limit 函數 (limit_handler.py)

```python
def handle_tool_limit(
    tool_usage_count: int, 
    max_tool_uses: int, 
    tool_calls: list,
    messages: Optional[List[Union[BaseMessage, Dict[str, Any]]]] = None,
    max_tokens: int = 50000  # 設定一個默認的 tokens 上限
) -> tuple[bool, list, int]:
    """處理工具使用次數限制
    
    Args:
        tool_usage_count: 當前工具使用次數
        max_tool_uses: 最大工具使用次數
        tool_calls: 工具調用列表
        messages: 所有消息列表，用於計算 tokens
        max_tokens: 最大 tokens 數量
        
    Returns:
        tuple: (是否達到限制, 工具消息列表, 當前 tokens 總數)
    """
    # 初始化 tokens 計數
    tokens_count = 0
    
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
        
        # 如果有消息，計算 tokens
        if messages:
            try:
                all_content = extract_content_from_messages(messages)
                tokens_count = calculate_tokens(all_content)
            except Exception as e:
                print(f"計算 tokens 時出現錯誤: {e}")
        
        return True, tool_messages, tokens_count
    
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
                
                return True, tool_messages, tokens_count
        except Exception as e:
            # 如果在處理 messages 時出現錯誤，記錄錯誤並繼續
            print(f"處理 messages 時出現錯誤: {e}")
    
    return False, [], tokens_count  # 未達到限制，返回 tokens 計數
```

## 3. 修改 tools_node 函數 (tool_node.py)

```python
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
    max_tokens = state.get("max_tokens", 50000)  # 設定一個默認的 tokens 上限
    total_tokens = state.get("total_tokens", 0)  # 獲取當前 tokens 總數，默認為 0

    # 從最後一條消息中提取工具調用信息
    last_message = state["messages"][-1]
    
    # 檢查是否為 AIMessage 並且有工具調用
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # 檢查是否達到工具使用上限或 tokens 上限
        limit_reached, limit_messages, current_tokens = handle_tool_limit(
            tool_usage_count, 
            max_tool_uses, 
            last_message.tool_calls,
            state["messages"],  # type: ignore
            max_tokens
        )
        
        # 更新 total_tokens
        total_tokens = current_tokens
        
        if limit_reached:
            return {
                "messages": state["messages"] + limit_messages,
                "tool_usage_count": tool_usage_count,
                "tool_results_cache": tool_results_cache,
                "max_tool_uses": max_tool_uses,
                "max_tokens": max_tokens,
                "total_tokens": total_tokens  # 返回計算的 tokens 總數
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
                "max_tokens": max_tokens,
                "total_tokens": total_tokens  # 返回計算的 tokens 總數
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
            "max_tokens": max_tokens,
            "total_tokens": total_tokens  # 返回計算的 tokens 總數
        }
    else:
        # 如果沒有工具調用，直接返回原始狀態，但確保包含 total_tokens
        return {**state, "total_tokens": total_tokens}
```

# 使用說明

修改後的代碼會在每次工具調用時計算當前的 tokens 總數，並將其作為 `total_tokens` 字段返回在 `AgentState` 中。這樣，您可以在應用程序的其他部分訪問這個值，例如用於顯示給用戶或進行其他決策。

要使用這個功能：

1. 更新 `state.py` 文件，添加 `total_tokens` 字段到 `AgentState` 類型定義中。
2. 更新 `limit_handler.py` 文件，修改 `handle_tool_limit` 函數以返回 tokens 計數。
3. 更新 `tool_node.py` 文件，修改 `tools_node` 函數以接收和返回 tokens 計數。

這些修改不會影響現有功能，只是添加了對 tokens 計數的跟踪和返回。

# 改進建議

1. **優化 tokens 計算**：目前的 tokens 計算方法是將所有消息的內容合併後計算，這可能不是最準確的方法。考慮使用更精確的方法，例如分別計算每條消息的 tokens 並累加。

2. **增量計算**：目前每次都重新計算所有消息的 tokens，這在消息量大時可能效率較低。考慮實現增量計算，只計算新增消息的 tokens 並累加到總數中。

3. **錯誤處理**：增強錯誤處理機制，確保即使 tokens 計算失敗，系統仍能正常運行。

4. **日誌記錄**：添加更詳細的日誌記錄，以便於調試和監控 tokens 使用情況。

5. **可配置性**：考慮使 tokens 計算方法可配置，例如允許用戶選擇不同的編碼器或估算方法。

Human:

