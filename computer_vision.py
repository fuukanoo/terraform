import os
import requests
import logging

# get API_KEY and ENDPOINT
vision_key = os.getenv("COMPUTER_VISION_API_KEY")
vision_endpoint = os.getenv("COMPUTER_VISION_ENDPOINT")


def extract_text_from_image(blob_data):
    """Computer Vision APIを使って画像データから文字を抽出する"""
    ocr_url = vision_endpoint + "/vision/v3.1/ocr"
    headers = {
        'Ocp-Apim-Subscription-Key': vision_key,
        'Content-Type': 'application/octet-stream'
    }

    try:
        response = requests.post(ocr_url, headers=headers, data=blob_data)
        response.raise_for_status()
        analysis = response.json()

        # OCR結果からテキストを抽出
        extracted_text = ""
        for region in analysis.get("regions", []):
            for line in region.get("lines", []):
                line_text = " ".join([word["text"] for word in line.get("words", [])])
                extracted_text += line_text + "\n"

        return extracted_text

    except requests.exceptions.HTTPError as e:
        logging.error(f"Error processing the image: {e}")
        return f"Error processing the image: {e}"
    except Exception as e:
        logging.error(f"An error occurred while extracting text from the image: {e}")
        return f"An error occurred while extracting text from the image: {e}"
