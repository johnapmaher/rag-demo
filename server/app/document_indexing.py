import boto3
from aws_lambda_powertools import Logger
from langchain_community.vectorstores import  OpenSearchVectorSearch
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain.schema import Document
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

from dotenv import load_dotenv
import os

load_dotenv()

s3 = boto3.client('s3')
logger = Logger()

bucket_name = os.environ.get("S3_BUCKET_NAME")

def get_opensearch_client():
    s3 = boto3.client('s3')
    
    bucket_name = os.environ.get("S3_BUCKET_NAME")
    
    host = os.getenv('OPENSEARCH_ENDPOINT')
    region = 'us-east-1'
    service = 'es'
    
    credentials = boto3.Session().get_credentials()
    logger.debug("Credentials retrieved: %s", credentials)
    credentials = credentials.get_frozen_credentials()
    logger.debug("Frozen credentials: %s", credentials)
    
    auth = AWSV4SignerAuth(credentials, region, service)
    
    client = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = auth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection,
        pool_maxsize = 20
    )
    return client

def read_document_from_s3(bucket_name, document_key):
    response = s3.get_object(Bucket=bucket_name, Key=document_key)
    document_content = response['Body'].read().decode('utf-8')
    return document_content

def index_document(document_content):
     # Initialize the text splitter
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    
    # Create a Document object
    doc = Document(page_content=document_content)
    
    # Split the document into chunks
    docs = text_splitter.split_documents([doc])
    
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Initialize OpenSearch vector store
    vector_store = OpenSearchVectorSearch(
        embedding_function=embeddings
        index_name='aoss-index',
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        http_compress=True,
        connection_class=RequestsHttpConnection,
        opensearch_url=os.getenv('OPENSEARCH_ENDPOINT'),
    )
    
    # Index the documents
    vector_store.add_documents(docs)

@logger.inject_lambda_context
def handler(event, context):
    logger.info(f"Received event: {event}")
    
    client = get_opensearch_client()
    
    index_body = {
        'settings': {
            "index.knn": True
        },
        "mappings": {
            "properties": {
            "osha_vector": {
                "type": "knn_vector",
                "dimension": 1536,
                "method": {
                "engine": "faiss",
                "name": "hnsw",
                "space_type": "l2"
                }
            }
            }
        }
        }

    response = client.indices.create('aoss-index', body=index_body)
    logger.debug("Index creation response: %s", response)
    
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_image = record['dynamodb']['NewImage']
            files_list = new_image.get('files', {}).get('L', [])

            for file_entry in files_list:
                document_key = file_entry.get('S')
                if document_key:
                    document = read_document_from_s3(bucket_name, document_key)
                    index_document(document)
                else:
                    logger.error('No document key found in file entry.')
