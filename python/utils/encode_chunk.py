def encode_chunk(chunk_text):
    """
    將 chunk 文本編碼，確保換行符被正確處理
    使用特殊標記 <NEWLINE> 來表示換行符
    """
    # 將換行符替換為特殊標記
    encoded_text = chunk_text.replace("\n", "<NEWLINE>")
    return encoded_text
