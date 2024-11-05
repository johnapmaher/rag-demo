import boto3
from aws_lambda_powertools import Logger
from langchain_community.vectorstores import  OpenSearchVectorSearch
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from dotenv import load_dotenv
import os

load_dotenv()

s3 = boto3.client('s3')
logger = Logger()

bucket_name = os.environ.get("S3_BUCKET_NAME")

def read_document_from_s3(bucket_name, document_key):
    response = s3.get_object(Bucket=bucket_name, Key=document_key)
    document_content = response['Body'].read().decode('utf-8')
    return document_content

def index_document(document_content):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(document_content)
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))

    # Initialize OpenSearch vector store
    vector_store = OpenSearchVectorSearch(
        endpoint=os.getenv('OPENSEARCH_ENDPOINT'),
        index_name='documents',
        embedding_function=embeddings.embed
    )

    # Index the document
    vector_store.add_texts(docs)

@logger.inject_lambda_context
def handler(event, context):
    logger.info(f"Received event: {event}")
    
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_image = record['dynamodb']['NewImage']
            files_list = new_image.get('files', {}).get('L', [])

            for file_entry in files_list:
                document_key = file_entry.get('S')
                if document_key:
                    document_content = read_document_from_s3(bucket_name, document_key)
                    index_document(document_content)
                else:
                    logger.error('No document key found in file entry.')
