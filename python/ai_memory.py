from typing import Tuple
from dotenv import load_dotenv
load_dotenv()

from .utils.process_file import process_file
from .utils.encode_chunk import encode_chunk
from langchain_core.messages import AIMessageChunk
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

    print("START_STREAM")

    ai_response = ""

    for chunk in stream:
        if not isinstance(chunk, Tuple) or not isinstance(chunk[0], AIMessageChunk):
            continue

        chunk_content = chunk[0].content

        processed_content = ""
        for item in chunk_content:
            if not isinstance(item, dict) or "text" not in item:
                continue
            processed_content += item["text"]
                    
        chunk_content = processed_content

        if not chunk_content:
            continue

        encoded_chunk = encode_chunk(chunk_content)
        print("CHUNK:" + encoded_chunk, flush=True)

        ai_response += chunk_content

        time.sleep(0.05)

    encoded_response = encode_chunk(ai_response)
    print("AI_RESPONSE:" + encoded_response)

    print("END_STREAM")

if __name__ == "__main__":
    main()
