import boto3
import logging
from langchain_community.vectorstores import  OpenSearchVectorSearch
from langchain_community.embeddings import OpenAIEmbeddings
import os

s3 = boto3.client('s3')
logger = Logger()

def read_document_from_s3(bucket_name, document_key):
    response = s3.get_object(Bucket=bucket_name, Key=document_key)
    document_content = response['Body'].read().decode('utf-8')
    return document_content

def index_document(document_content):
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))

    # Initialize OpenSearch vector store
    vector_store = OpenSearchVectorSearch(
        endpoint=os.getenv('OPENSEARCH_ENDPOINT'),
        index_name='documents',
        embedding_function=embeddings.embed
    )

    # Index the document
    vector_store.index_document(document_content)

@logger.inject_lambda_context
def handler(event, context):
    logger.info(f"Received event: {event}")

    document_content = read_document_from_s3(bucket_name, document_key)
    index_document(document_content)