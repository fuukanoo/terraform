import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import logging

# get API_KEY and ENDPOINT
intelligence_key = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")
intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")


def extract_text_from_document(blob_data):
    """Document Intelligence APIを使ってドキュメントから文字を抽出する"""
    document_analysis_client = DocumentAnalysisClient(
        endpoint=intelligence_endpoint, 
        credential=AzureKeyCredential(intelligence_key)
    )

    try:
        # Document Intelligence API に送信
        poller = document_analysis_client.begin_analyze_document("prebuilt-document", blob_data)
        result = poller.result()

        # 結果からテキストを抽出
        extracted_text = ""
        for page in result.pages:
            for line in page.lines:
                extracted_text += line.content + "\n"
        return extracted_text

    except Exception as e:
        logging.error(f"Error processing the document: {e}")
        return f"Error processing the document: {e}"