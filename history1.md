Human:

File: /home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/tool_node.py
```python
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
```

上面檔案內容已經過於複雜難以閱讀, 請幫我重構到不同檔案以增加可讀性

AI:
# 需求理解

我理解您希望將 `tool_node.py` 檔案重構，將其拆分成多個檔案以提高可讀性。目前的檔案包含了工具節點的邏輯，處理工具調用、緩存結果、限制工具使用次數等功能，但代碼結構較為複雜，不易維護。

## 資訊收集

讓我先了解一下目前的目錄結構，以便規劃重構後的檔案組織：讓我查看一下 state.py 的內容，以了解 AgentState 的定義：讓我查看一下 tools 的定義：讓我查看一下 nodes 目錄下的 __init__.py 文件：讓我查看一下 tools 目錄下的 __init__.py 文件：## 解決方案概述

基於對現有代碼的分析，我將把 `tool_node.py` 重構為以下幾個文件：

1. **tool_node.py** - 主入口點，只包含主要的 `tools_node` 函數
2. **tool_handlers/** 目錄 - 包含處理工具調用的不同邏輯
   - **__init__.py** - 導出所有處理器
   - **cache_handler.py** - 處理工具結果緩存
   - **limit_handler.py** - 處理工具使用次數限制
   - **tool_executor.py** - 執行工具調用

這種結構將使代碼更加模塊化，每個文件都有明確的單一職責，提高可讀性和可維護性。

## 程式碼實現

### 1. 首先，創建新的目錄結構

```
/home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/tool_handlers/
```

### 2. 創建 tool_handlers/__init__.py

```python
# /home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/tool_handlers/__init__.py

from .cache_handler import handle_cached_result
from .limit_handler import handle_tool_limit
from .tool_executor import execute_tool

__all__ = ["handle_cached_result", "handle_tool_limit", "execute_tool"]
```

### 3. 創建 tool_handlers/cache_handler.py

```python
# /home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/tool_handlers/cache_handler.py

from langchain_core.messages import AIMessage, ToolMessage
from ...state import AgentState

def handle_cached_result(
    state: AgentState, 
    last_message: AIMessage, 
    tool_name: str, 
    tool_args: dict
) -> AgentState:
    """
    檢查並處理緩存的工具調用結果
    
    Args:
        state: 當前代理狀態
        last_message: 最後一條 AI 消息
        tool_name: 工具名稱
        tool_args: 工具參數
        
    Returns:
        更新後的代理狀態，如果有緩存結果則包含緩存結果消息
    """
    tool_results_cache = state.get("tool_results_cache", {})
    tool_usage_count = state.get("tool_usage_count", 0)
    max_tool_uses = state.get("max_tool_uses", 20)
    
    # 檢查是否有緩存結果
    cache_key = f"{tool_name}:{str(tool_args)}"
    if cache_key in tool_results_cache:
        # 使用緩存結果而不是重新調用工具
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
    
    # 如果沒有緩存結果，返回 None
    return None
```

### 4. 創建 tool_handlers/limit_handler.py

```python
# /home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/tool_handlers/limit_handler.py

from langchain_core.messages import AIMessage, ToolMessage
from ...state import AgentState

def handle_tool_limit(
    state: AgentState, 
    last_message: AIMessage
) -> AgentState:
    """
    檢查並處理工具使用次數限制
    
    Args:
        state: 當前代理狀態
        last_message: 最後一條 AI 消息
        
    Returns:
        如果達到工具使用上限，返回包含限制消息的更新狀態；否則返回 None
    """
    tool_usage_count = state.get("tool_usage_count", 0)
    tool_results_cache = state.get("tool_results_cache", {})
    max_tool_uses = state.get("max_tool_uses", 20)
    
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
    
    # 如果沒有達到上限，返回 None
    return None
```

### 5. 創建 tool_handlers/tool_executor.py

```python
# /home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/tool_handlers/tool_executor.py

from langgraph.prebuilt import ToolNode
from ...state import AgentState
from ..tools import tools

def execute_tool(
    state: AgentState, 
    tool_name: str, 
    tool_args: dict
) -> AgentState:
    """
    執行工具調用並更新狀態
    
    Args:
        state: 當前代理狀態
        tool_name: 工具名稱
        tool_args: 工具參數
        
    Returns:
        包含工具執行結果的更新狀態
    """
    tool_usage_count = state.get("tool_usage_count", 0)
    tool_results_cache = state.get("tool_results_cache", {})
    max_tool_uses = state.get("max_tool_uses", 20)
    
    # 調用工具並更新計數器
    messages = ToolNode(tools).invoke(state["messages"])
    
    # 緩存結果
    cache_key = f"{tool_name}:{str(tool_args)}"
    if messages and len(messages) > 0:
        tool_results_cache[cache_key] = messages[-1].content
    
    tool_usage_count += 1
    
    return {
        "messages": state["messages"] + messages,
        "tool_usage_count": tool_usage_count,
        "tool_results_cache": tool_results_cache,
        "max_tool_uses": max_tool_uses
    }
```

### 6. 重構主要的 tool_node.py

```python
# /home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/tool_node.py

from langchain_core.messages import AIMessage
from ..state import AgentState
from .tool_handlers import handle_tool_limit, handle_cached_result, execute_tool

def tools_node(state: AgentState) -> AgentState:
    """
    處理工具調用的主要節點函數
    
    Args:
        state: 當前代理狀態
        
    Returns:
        更新後的代理狀態
    """
    # 初始化狀態變量
    tool_usage_count = state.get("tool_usage_count", 0)
    tool_results_cache = state.get("tool_results_cache", {})
    max_tool_uses = state.get("max_tool_uses", 20)

    # 從最後一條消息中提取工具調用信息
    last_message = state["messages"][-1]
    
    # 檢查是否為 AIMessage 並且有工具調用
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # 檢查是否達到工具使用上限
        limit_state = handle_tool_limit(state, last_message)
        if limit_state:
            return limit_state
        
        # 提取工具名稱和參數
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        
        # 檢查是否有緩存結果
        cache_state = handle_cached_result(state, last_message, tool_name, tool_args)
        if cache_state:
            return cache_state
        
        # 執行工具調用
        return execute_tool(state, tool_name, tool_args)
    else:
        # 如果沒有工具調用，直接返回原始狀態
        return state
```

## 使用說明

重構後的代碼結構如下：

```
/home/matt/dotfiles/nvim/.config/nvim/lua/ai-memory/python/graph/nodes/
├── tool_node.py - 主入口點
└── tool_handlers/ - 處理工具調用的模塊
    ├── __init__.py - 導出所有處理器
    ├── cache_handler.py - 處理工具結果緩存
    ├── limit_handler.py - 處理工具使用次數限制
    └── tool_executor.py - 執行工具調用
```

使用方法與原來相同，只需要導入 `tools_node` 函數：

```python
from .nodes.tool_node import tools_node
```

重構後的代碼保持了原有的功能，但將不同的邏輯分離到不同的文件中，每個文件都有明確的單一職責，提高了代碼的可讀性和可維護性。

## 進一步改進建議

1. **錯誤處理增強**：可以在 `tool_executor.py` 中添加更健壯的錯誤處理機制，處理工具執行過程中可能出現的異常。

2. **日誌記錄**：添加日誌記錄功能，記錄工具調用、緩存命中和限制觸發等事件，便於調試和監控。

3. **配置外部化**：將最大工具使用次數等配置參數移到配置文件中，使其更容易調整。

4. **單元測試**：為每個處理器添加單元測試，確保它們在各種情況下都能正確工作。

5. **類型提示完善**：添加更詳細的類型提示，提高代碼的可讀性和 IDE 支持。

6. **文檔字符串**：為每個函數添加更詳細的文檔字符串，說明其功能、參數和返回值。

這些重構使代碼更加模塊化，每個模塊都有明確的單一職責，遵循了單一職責原則，提高了代碼的可讀性、可維護性和可測試性。

Human:

