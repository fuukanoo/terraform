# coding: utf-8

import os
import logging
import ipdb

from langchain import hub
from langchain_openai import AzureChatOpenAI
from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
from langchain_openai import AzureOpenAIEmbeddings
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.vectorstores import AzureSearch
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult, ContentFormat

# get API_KEY and ENDPOINT
intelligence_key = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")
intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
vector_store_password = os.getenv("AZURE_SEARCH_ADMIN_KEY")
vector_store_address = os.getenv("AZURE_SEARCH_ENDPOINT")

def extract_text_and_chunk_from_document(blob_url):
    """Document Intelligence APIを使ってドキュメントから文字を抽出し、セマンティックに細かくチャンク分割する"""
    try:
        # Initiate Azure AI Document Intelligence to load the document. You can either specify file_path or url_path to load the document.
        loader = AzureAIDocumentIntelligenceLoader(url_path=blob_url, api_key = intelligence_key, api_endpoint = intelligence_endpoint, api_model="prebuilt-layout")
        docs = loader.load()

        # Split the document into chunks base on markdown headers.
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

        docs_string = docs[0].page_content
        splits = text_splitter.split_text(docs_string)
        ipdb.set_trace()

        logging.info(f"Length of splits:{len(splits)}") #Length of splits:34

        # [END analyze_documents_output_in_markdown]

        #Azure OpenAIの埋め込みモデルを使用して、テキストの意味的なベクトル表現を生成
        aoai_embeddings = AzureOpenAIEmbeddings(
            azure_deployment="text-embedding-ada-002", 
            openai_api_version="2023-05-15",  
        )

        index_name: str = "idx-rag-dev" # # Azure AI Search上に作成するIndex名
        #Azure Searchのベクトルストアインスタンスの作成
        vector_store: AzureSearch = AzureSearch(
            azure_search_endpoint=vector_store_address,
            azure_search_key=vector_store_password,
            index_name=index_name,
            embedding_function=aoai_embeddings.embed_query,
        )

        # 先程チャンク化した情報を格納する
        # 格納するタイミングでベクトル 化も行われる
        vector_store.add_documents(documents=splits)

        # Retrieve relevant chunks based on the question
        # 先ほど作成したベクトルストアをRetrieverとして定義
        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

        retrieved_docs = retriever.get_relevant_documents(
            "この文章で説明したいことは何ですか？"
        )
        #質問に関連するドキュメントを表示
        logging.info(f"retrieved document:{retrieved_docs[0].page_content}")

        # Use a prompt for RAG that is checked into the LangChain prompt hub (https://smith.langchain.com/hub/rlm/rag-prompt?organizationId=989ad331-949f-4bac-9694-660074a208a7)
        prompt = hub.pull("rlm/rag-prompt")
        llm = AzureChatOpenAI(
            openai_api_version="2023-05-15",  # e.g., "2023-12-01-preview"
            azure_deployment="gpt-35-turbo",
            temperature=0,
        )

        #取得した関連チャンクを整形し、1つの文字列にまとめる
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        #RAGの処理チェーン構築
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )



    except Exception as e:
        logging.error(f"Error processing the document: {e}")
        return f"Error processing the document: {e}"

    

