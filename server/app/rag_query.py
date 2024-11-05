import os
import logging
from dotenv import load_dotenv
from aws_lambda_powertools import Logger
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chains import RetrievalQA
from langchain_community.llms import OpenAI
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, exceptions as opensearch_exceptions

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = Logger()

# Access environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
opensearch_endpoint = os.getenv("OPENSEARCH_ENDPOINT")
region = os.getenv("AWS_REGION", "us-east-1")
service = 'aoss'

# Initialize OpenSearch authentication
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region, service)

def get_opensearch_client():
    client = OpenSearch(
        hosts=[{'host': opensearch_endpoint.replace('https://', ''), 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20
    )
    return client

def handler(event, context):
    logger.info("Received request for RAG query")
    
    query = event.get("query")
    logger.info(f"Extracted query: {query}")
    
    # Initialize OpenSearch client
    client = get_opensearch_client()
    
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(api_key=openai_api_key)
    
    # Initialize OpenSearch vector store
    vector_store = OpenSearchVectorSearch(
        embedding_function=embeddings,
        index_name='aoss-index',
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        http_compress=True,
        connection_class=RequestsHttpConnection,
        opensearch_url=opensearch_endpoint
    )
    
    # Set up retriever from OpenSearch index and run RAG pipeline
    logger.info("Setting up retriever from OpenSearch index")
    retriever = vector_store.as_retriever()
    
    logger.info("Initializing RetrievalQA chain")
    qa_chain = RetrievalQA.from_chain_type(
        llm=OpenAI(api_key=openai_api_key),
        chain_type="stuff",
        retriever=retriever
    )
    
    # Run the query and return the generated response
    logger.info("Running query through the QA chain")
    response = qa_chain.run(query)
    logger.info("Query executed successfully")
    
    return {
        'statusCode': 200,
        'body': response
    }