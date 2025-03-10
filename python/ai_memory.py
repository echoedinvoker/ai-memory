from dotenv import load_dotenv
load_dotenv()

from .utils.process_file import process_file
from .utils.encode_chunk import encode_chunk
from langchain_core.messages import AIMessage
import os
import sys
import time


def main():
    """Main function to be called from Neovim."""
    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            file.write("System:\nAnswer like a pirate\n\nHuman:\n")
        print("INIT_FILE")
        sys.exit(0)

    stream = process_file(file_path)
    if not stream:
        print("NO_HUMAN_MESSAGE")
        sys.exit(0)

    # Print a special marker for Neovim to recognize the start
    print("START_STREAM")

    ai_response = ""
    # 發送每個 chunk，確保換行符被正確處理
    for chunk in stream:
        if isinstance(chunk[0], AIMessage):
            chunk_content = chunk[0].content

            # 處理不同類型的 chunk_content
            if isinstance(chunk_content, list):
                # 如果是列表，檢查列表中的元素類型
                processed_content = ""
                for item in chunk_content:
                    if isinstance(item, dict):
                        # 嘗試從字典中提取文本
                        # 這裡需要知道字典的確切結構
                        # 常見的鍵可能是 "text", "content", "value" 等
                        if "text" in item:
                            processed_content += item["text"]
                        elif "content" in item:
                            processed_content += item["content"]
                        # 可以根據實際情況添加更多條件
                    elif isinstance(item, str):
                        processed_content += item
                chunk_content = processed_content

            # 編碼 chunk 內容，確保換行符被保留
            encoded_chunk = encode_chunk(chunk_content)
            print("CHUNK:" + encoded_chunk, flush=True)

            ai_response += chunk_content

            # 小延遲避免緩衝區問題
            time.sleep(0.05)

    # 同樣編碼完整回應
    encoded_response = encode_chunk(ai_response)
    print("AI_RESPONSE:" + encoded_response)

    # Print a special marker for Neovim to recognize the end
    print("END_STREAM")

if __name__ == "__main__":
    main()
