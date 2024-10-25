from docx import Document
from io import BytesIO
import logging


def extract_text_from_word(blob_data):
    """Wordファイルのバイナリデータからテキストを抽出"""
    try:
        # BytesIOを使ってバイナリデータをメモリ上で処理
        doc = Document(BytesIO(blob_data))
        
        # 文書内のすべての段落を抽出し、改行で結合
        extracted_text = "\n".join([para.text for para in doc.paragraphs])
        
        return extracted_text

    except Exception as e:
        logging.error(f"Error processing the Word document: {e}")
        return f"Error processing the Word document: {e}"