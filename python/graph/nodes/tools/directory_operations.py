from langchain_core.tools import tool
from pathlib import Path
from typing import Optional, List

@tool
def get_directory_tree(start_path: str, max_depth: Optional[int] = None, ignore_patterns: Optional[List[str]] = None) -> str:
    """
    Generate a tree-like structure of the directory starting from the given path.
    
    Args:
        start_path (str): The absolute path to start the directory tree from.
        max_depth (Optional[int]): Maximum depth to traverse. None means no limit.
        ignore_patterns (Optional[List[str]]): List of patterns to ignore (e.g., ['.git', '__pycache__']).
        
    Returns:
        str: A string representation of the directory tree.
        
    Raises:
        FileNotFoundError: If the start path does not exist.
        PermissionError: If a directory cannot be accessed due to permission issues.
    """
    if ignore_patterns is None:
        ignore_patterns = ['.git', '__pycache__', '.pyc', '.DS_Store', '.venv', 'node_modules']
    
    try:
        path_obj = Path(start_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"The path {start_path} does not exist.")
        
        result = [f"Directory tree for: {start_path}\n"]
        
        def should_ignore(path: Path) -> bool:
            path_str = str(path)
            return any(pattern in path_str for pattern in ignore_patterns)
        
        def add_tree(path: Path, prefix: str = "", depth: int = 0) -> None:
            if max_depth is not None and depth > max_depth:
                return
            
            if not path.is_dir():
                result.append(f"{prefix}├── {path.name}")
                return
            
            result.append(f"{prefix}├── {path.name}/")
            
            # Get all items in the directory
            try:
                items = sorted(list(path.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
            except PermissionError:
                result.append(f"{prefix}│   └── [Permission Denied]")
                return
            
            # Filter out ignored patterns
            items = [item for item in items if not should_ignore(item)]
            
            # Process each item
            for i, item in enumerate(items):
                is_last = (i == len(items) - 1)
                
                if is_last:
                    new_prefix = f"{prefix}    "
                    item_prefix = f"{prefix}└── "
                else:
                    new_prefix = f"{prefix}│   "
                    item_prefix = f"{prefix}├── "
                
                if item.is_dir():
                    result.append(f"{item_prefix}{item.name}/")
                    add_tree(item, new_prefix, depth + 1)
                else:
                    result.append(f"{item_prefix}{item.name}")
        
        # Start the recursion from the children of the start path
        try:
            items = sorted(list(path_obj.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
            items = [item for item in items if not should_ignore(item)]
            
            for i, item in enumerate(items):
                is_last = (i == len(items) - 1)
                if is_last:
                    add_tree(item, "", 1)
                else:
                    add_tree(item, "", 1)
                    
        except PermissionError:
            result.append("[Permission Denied]")
        
        return "\n".join(result)
    
    except Exception as e:
        return f"Error generating directory tree: {str(e)}"
