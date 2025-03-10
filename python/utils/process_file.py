from .parse_history_file import parse_history_file
from ..graph.graph import graph
from langchain_core.messages import HumanMessage


def process_file(file_path: str):
    """Process the file and return AI response chunks for streaming."""
    messages = parse_history_file(file_path)
    
    if not messages or not isinstance(messages[-1], HumanMessage) or not messages[-1].content.strip():
        return None
    
    return graph.stream(messages, stream_mode="messages")
