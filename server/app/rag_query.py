import os
import logging
import boto3
from dotenv import load_dotenv
from aws_lambda_powertools import Logger
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
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
    
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))

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
    docs = vector_store.similarity_search_by_vector(
            "What is the standard height where fall protection is required?",
            vector_field="uploads_vector",
            text_field="text",
            metadata_field="metadata",
            )
    
    docs_dict = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    data = ""
    for doc in docs_dict:
        data += doc['page_content'] + "\n\n"

    
    llm = OpenAI()
    prompt = PromptTemplate(
    input_variables=["question", "data"],
    template="""Using the data below, answer the question provided.
    question: {question}
    data: {data}
    """,
    )


    chain = LLMChain(llm=llm, prompt=prompt)
    llm_return_data = chain.run({'question': query, 'data': data})
    
    return {
        'statusCode': 200,
        'body': llm_return_data
    }