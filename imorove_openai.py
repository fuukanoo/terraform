import os
import openai
import logging


# get API_KEY and ENDPOINT
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  
openai.api_type = "azure"
openai.api_version = "2023-05-15"  # version

def improve_text_with_openai(text):
    """Azure OpenAIを使って抽出したテキストを修正する"""
    prompt = (f"次のテキストはOCRを使用して画像から,もしくはドキュメントから抽出されました. "
              f"誤読された部分や間違っている部分があれば，訂正して正しいと思われる文章にして出力して. "
              f"ただし,正しい場合は特に変更を加えずにそのまま出力してください.:\n\n{text}")

    try:
        # Azure OpenAI API を使ってテキスト補正
        response = openai.chat.completions.create(
            model="gpt-35-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant "},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.3,
            top_p=0.9
        )

        message_content = response.choices[0].message.content.strip()
        return message_content

    except openai.OpenAIError as e:
        logging.error(f"Error during OpenAI request: {e}")
        return f"Error during OpenAI request: {e}"