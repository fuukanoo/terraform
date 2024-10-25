import azure.functions as func
import os
import openai
import requests
import logging
from make_prompt import generate_prompt

# 環境変数からAPIキーとエンドポイントを取得
vision_key = os.getenv("COMPUTER_VISION_SUBSCRIPTION_KEY")
vision_endpoint = os.getenv("COMPUTER_VISION_ENDPOINT")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  # OpenAIのエンドポイント
openai.api_type = "azure"
openai.api_version = "2023-05-15"  # バージョン指定

# 関数アプリのルート設定
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="function_rag")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing a request to extract and improve text from image.')

    # リクエストからimage_urlを取得
    image_url = req.params.get('image_url')
    if not image_url:
        try:
            req_body = req.get_json()
            image_url = req_body.get('image_url')
        except ValueError:
            pass

    if not image_url:
        return func.HttpResponse("Please pass an image_url in the query string or in the request body", status_code=400)

    # ステップ1: 画像から文字を抽出（OCR）
    extracted_text = extract_text_from_image(image_url)
    logging.info(f"Extracted text: {extracted_text}")

    #プロンプトを生成
    user_prompt = (f"次のテキストはOCRを使用して画像から抽出されました. "
              f"誤読された部分や間違っている部分を訂正してください."
              f"ただし,文章を勝手に追加したりしないでください.:\n\n{extracted_text}")
    
    prompt = generate_prompt(user_prompt)

    # ステップ2: OpenAIでテキストを補正
    improved_text = improve_text_with_openai(prompt)
    logging.info(f"Improved text:\n {improved_text}")

    return func.HttpResponse(improved_text, status_code=200)

def extract_text_from_image(image_url):
    """Azure Computer Vision APIを使って画像から文字を抽出する"""
    ocr_url = vision_endpoint+ "/vision/v3.1/ocr"
    headers = {'Ocp-Apim-Subscription-Key': vision_key}
    data = {'url': image_url}

    try:
        # OCRのリクエストを送信
        response = requests.post(ocr_url, headers=headers, json=data)
        response.raise_for_status()  # ステータスコードがエラーの場合は例外を発生
        analysis = response.json()
        # OCR結果からテキストを抽出
        extracted_text = ""
        for region in analysis["regions"]:
            for line in region["lines"]:
                line_text = " ".join([word["text"] for word in line["words"]])
                extracted_text += line_text + "\n"

    except requests.exceptions.HTTPError as e:
        # 詳細なエラーメッセージをログに出力
        logging.error(f"Error processing the image: {e}")
        #logging.error(f"Response content: {response.text}")  # レスポンス内容をログに出力
        return func.HttpResponse(f"Error processing the image: {response.text}", status_code=500)
    
    return extracted_text



def improve_text_with_openai(prompt):
    """Azure OpenAIを使って抽出したテキストを修正する"""

    try:
        # Azure OpenAI API を使ってテキスト補正
        response = openai.chat.completions.create(
            model="gpt-35-turbo",  # GPT-3.5 または GPT-4 を使用
            messages=[
                {"role": "system", "content": "You are a helpful assistant "},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,  # 生成する最大トークン数
            temperature=0.4,  # 応答の多様性を制御するパラメータ
            top_p=0.9  # トークン選択の範囲を広げる
        )

        ## ChatCompletionの結果にアクセス
        message_content = response.choices[0].message.content.strip()

        return message_content

    except openai.OpenAIError as e:
        # エラーハンドリング
        print(f"An error occurred: {e}")
        return f"Error during OpenAI request: {e}"


