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
