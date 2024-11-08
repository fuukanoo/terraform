import azure.functions as func
import os
import openai
from azure.storage.blob import BlobServiceClient
import logging
import mimetypes  # get file type
import requests

# import my library
from extract_docx import extract_text_from_word
from extract_pptx import extract_text_from_ppt
from extract_xlsx import extract_text_from_excel
from computer_vision import extract_text_from_image
#from document_intelligence import extract_text_from_document
from document_intelligence import extract_text_and_chunk_from_document
#from azure_openai import improve_text_with_openai
from azure_openai import process_chunks_with_openai

# get API_KEY and ENDPOINT
vision_key = os.getenv("COMPUTER_VISION_API_KEY")
vision_endpoint = os.getenv("COMPUTER_VISION_ENDPOINT")
intelligence_key = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")
intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
blob_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_container = os.getenv("BLOB_CONTAINER")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  
openai.api_type = "azure"
openai.api_version = "2023-05-15"  # version

# route setting
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="function_rag")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing a request to extract and improve text from an image or document.')

    # リクエストボディからJSONデータを取得
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON format", status_code=400)

    file_name = req_body.get("file_name")

    if not file_name:
        return func.HttpResponse("Please provide 'file_name' in the request body.", status_code=400)

    # Blobストレージからファイルを取得
    #extracted_text = extract_text_from_blob(blob_container, file_name)
    blob_url = "https://strag013.blob.core.windows.net/container-rag-dev/入力データサンプル.pdf?sv=2022-11-02&ss=bfqt&srt=co&sp=rwdlacupiytfx&se=2024-12-08T09:44:49Z&st=2024-11-08T01:44:49Z&spr=https&sig=3%2BdOw91lvdNbf9vCnbzm%2BbMp8rT%2B6Xt4nIObLmPVWrw%3D"
    chanking_extracted_text = extract_text_from_blob_url(blob_url)
    logging.info(f"chanking extracted text:\n {chanking_extracted_text}")

    if "Error" in chanking_extracted_text:
        return func.HttpResponse(chanking_extracted_text, status_code=500)

    # improved_text = process_chunks_with_openai(extracted_text)
    # logging.info(f"Improved text:\n {improved_text}")

    # return func.HttpResponse(improved_text, status_code=200)
    return func.HttpResponse(chanking_extracted_text, status_code=200)




def extract_text_from_blob_url(blob_url):
    """URLからBlobストレージ上のファイルを取得し、適切な方法でテキストを抽出"""
    try:
        # URLからファイルをダウンロード
        response = requests.get(blob_url)
        response.raise_for_status()  # ステータスコードがエラーの場合例外を発生
        return extract_text_and_chunk_from_document(blob_url)
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading the blob from URL: {e}")
        return f"Error downloading the blob from URL: {e}"
    except Exception as e:
        logging.error(f"Error processing the blob: {e}")
        return f"Error processing the blob: {e}"


def extract_text_from_blob(blob_container, blob_name):
    """ファイルの種類に応じてBlobストレージから画像、ドキュメント、Word、Excel、PowerPointを取得し、適切な方法でテキストを抽出"""
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    blob_client = blob_service_client.get_blob_client(container=blob_container, blob=blob_name)

    try:
        # Blobからファイルをダウンロード
        blob_data = blob_client.download_blob().readall()

        # MIMEタイプを取得して処理を分岐
        mime_type, _ = mimetypes.guess_type(blob_name)

        if mime_type and mime_type.startswith("image"):
            return extract_text_from_image(blob_data)
        elif mime_type == "application/pdf":
            return extract_text_and_chunk_from_document(blob_data)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            #ipdb.set_trace()
            return extract_text_from_word(blob_data)
        elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return extract_text_from_excel(blob_data)
        elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            return extract_text_from_ppt(blob_data)
        else:
            return "Error: Unsupported file type."

    except Exception as e:
        logging.error(f"Error processing the blob: {e}")
        return f"Error processing the blob: {e}"