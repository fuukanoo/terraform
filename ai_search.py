from langchain import hub
from langchain_openai import AzureChatOpenAI
from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
from langchain_openai import AzureOpenAIEmbeddings
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.vectorstores.azuresearch import AzureSearch

import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import logging
from langchain.text_splitter import  RecursiveCharacterTextSplitter


# get API_KEY and ENDPOINT
intelligence_key = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")
intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")