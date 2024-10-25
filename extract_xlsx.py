import logging
import pandas as pd
from io import BytesIO


def extract_text_from_excel(blob_data):
    """Excelファイルのバイナリデータからテキストを抽出"""
    try:
        # BytesIOを使用してメモリ上でExcelファイルを処理
        df = pd.read_excel(BytesIO(blob_data))
        
        # DataFrameを文字列形式に変換
        extracted_text = df.to_string(index=False)
        
        return extracted_text

    except Exception as e:
        logging.error(f"Error processing the Excel document: {e}")
        return f"Error processing the Excel document: {e}"