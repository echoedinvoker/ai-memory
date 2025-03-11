from .parse_history_file import parse_history_file
from ..graph.graph import graph
from langchain_core.messages import HumanMessage


def process_file(file_path: str):
    """Process the file and return AI response chunks for streaming."""
    messages = parse_history_file(file_path)
    
    has_valid_last_message = (messages and 
                             isinstance(messages[-1], HumanMessage) and 
                             isinstance(messages[-1].content, str) and 
                             messages[-1].content.strip())
    
    if not has_valid_last_message:
        messages = []
    
    return graph.stream(
        { "messages": messages },
        stream_mode="messages"
    )
