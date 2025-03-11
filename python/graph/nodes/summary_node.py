from ..state import AgentState
from langchain_core.messages import HumanMessage
from ..utils.message_utils import convert_messages_to_str, extract_integrated_question
from ..chains.summary_chain import summary_chain


def summary_node(state: AgentState) -> AgentState:
    """處理消息並進行智能歷史摘要。
    
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

    return {"messages": [HumanMessage(content=integrated_question)]}
