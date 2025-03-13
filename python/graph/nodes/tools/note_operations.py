import os
from langchain_core.tools import tool
from typing import Optional

@tool
def get_note_content(note_id: Optional[str] = None) -> str:
    """
    Retrieve the content of a note by its ID, or return the content of the root note if no ID is provided.
    
    Args:
        note_id (Optional[str]): The ID of the note to retrieve (e.g., '1727973861-YWDK').
                                If not provided or empty, returns the content of the root note.
        
    Returns:
        str: The content of the note if found, or a message indicating the note doesn't exist.
    """
    # If note_id is None or empty, return the root note content
    if not note_id:
        root_path = "/home/matt/Github/secondbrain/root.md"
        if os.path.exists(root_path):
            try:
                with open(root_path, 'r', encoding='utf-8') as file:
                    return file.read()
            except Exception as e:
                return f"Error reading root note: {str(e)}"
        else:
            return "根筆記不存在"
    
    # Define the possible paths where the note might be located
    possible_paths = [
        f"/home/matt/Github/secondbrain/notes/fact/{note_id}.md",
        f"/home/matt/Github/secondbrain/notes/index/{note_id}.md",
        f"/home/matt/Github/secondbrain/hubs/{note_id}.md"
    ]
    
    # Check each path and return the content of the first file found
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    return file.read()
            except Exception as e:
                return f"Error reading note {note_id}: {str(e)}"
    
    # If no file is found in any of the paths
    return "此筆記不存在"
