from langchain_core.tools import tool

@tool
def get_file_content_by_absolute_path(file_path: str) -> str:
    """
    Read and return the content of a file as a string.
    
    Args:
        file_path (str): The absolute path to the file to be read.
        
    Returns:
        str: The content of the file as a string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read due to permission issues.
        IOError: If there's an error reading the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        raise FileNotFoundError(f"The file at {file_path} was not found.")
    except PermissionError:
        raise PermissionError(f"Permission denied when trying to read {file_path}.")
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {str(e)}")
