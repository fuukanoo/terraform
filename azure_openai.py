import os
import openai
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set API key and endpoint
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  
openai.api_type = "azure"
openai.api_version = "2023-05-15"  # version

def improve_text_with_openai(text):
    """Azure OpenAIを使って抽出したテキストを修正する"""
    prompt = (f"次のテキストはOCRを使用して画像から,もしくはドキュメントから抽出されました. "
              f"誤読された部分や間違っている部分があれば，訂正して正しいと思われる文章にして出力して. "
              f"ただし,テキストの情報を損なわないように改善してください.短縮は行わず、元の情報を保持してください.:\n\n{text}")

    try:
        # Azure OpenAI API でテキスト補正を実行
        response = openai.chat.completions.create(
            model="gpt-35-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
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

def process_chunks_with_openai(chunks):
    """チャンクごとにテキスト補正を行い、結果を結合して出力する"""
    corrected_texts = []
    
    for i, chunk in enumerate(chunks):
        logging.info(f"Processing chunk {i + 1}/{len(chunks)}")
        corrected_text = improve_text_with_openai(chunk)
        
        if "Error during OpenAI request" in corrected_text:
            logging.warning(f"Skipping chunk {i + 1} due to error.")
        else:
            corrected_texts.append(corrected_text)
    
    # チャンクを順番に結合して1つのテキストにする
    combined_text = "\n".join(corrected_texts)
    logging.info("All chunks processed and combined successfully.")
    return combined_text

# Example usage:
# Assuming `chunks` is a list of text chunks obtained from previous processing
# corrected_text = process_chunks_with_openai(chunks)
# print(corrected_text) 

