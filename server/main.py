from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import aioboto3
from botocore.exceptions import NoCredentialsError, ClientError
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from fastapi.responses import JSONResponse
from fastapi import Depends

# Set up logging with timestamp, logger name, and log level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# CORS setup to allow requests from specific origin (CloudFront distribution URL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://d3memimioruxu.cloudfront.net"],  # Replace with your actual origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Validate required environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
s3_bucket_name = os.getenv("S3_BUCKET_NAME")
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

# Raise an error if any of the required environment variables are missing
if not openai_api_key or not s3_bucket_name or not aws_access_key_id or not aws_secret_access_key:
    raise ValueError("Missing required environment variables.")

# Set OpenAI API key for LangChain usage
openai.api_key = openai_api_key

# Initialize S3 client using aioboto3 for asynchronous operations
s3_client = aioboto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

# Initialize LangChain components: embeddings and FAISS index for RAG
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
index = FAISS(embeddings)
documents_metadata = {}

# Health check endpoint to ensure the API is running
@app.get("/health")
async def health_check():
    return JSONResponse(status_code=200, content={"status": "healthy"})

# Endpoint to upload and process a document
@app.post("/upload")
async def upload_document(file: UploadFile = File(...), s3_client=Depends(get_s3_client)):
    # Validate file extension and size
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Invalid file format. Only .txt files are allowed.")
    if file.spool_max_size > (2 * 1024 * 1024):  # Limit file size to 2MB
        raise HTTPException(status_code=400, detail="File size exceeds the limit of 2MB.")
    
    try:
        # Read file contents asynchronously
        contents = await file.read()

        # Upload file to S3 bucket
        async with s3_client as s3:
            await s3.put_object(Bucket=s3_bucket_name, Key=file.filename, Body=contents)

        # Split file contents and add to FAISS index for RAG
        text = contents.decode("utf-8")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_text(text)
        index.add_texts(docs)

        # Store metadata about the uploaded document
        documents_metadata[file.filename] = {   
            "num_chunks": len(docs)
        }

        return {"filename": file.filename, "message": "Document uploaded and indexed successfully"}
    
    # Handle AWS credential-related errors
    except NoCredentialsError:
        logging.error("AWS credentials are missing or invalid.")
        raise HTTPException(status_code=500, detail="AWS credentials are missing or invalid.")
    
    # Handle S3 client errors
    except ClientError as e:
        logging.error(f"S3 Client Error: {e}")
        raise HTTPException(status_code=500, detail="Error uploading document to S3.")
    
    # Handle general exceptions
    except Exception as e:
        logging.error(f"General error: {e}")
        raise HTTPException(status_code=500, detail="Error uploading document")

# Endpoint for querying with RAG (Retrieval-Augmented Generation)
@app.post("/rag")
async def rag_query(query: str):
    try:
        # Set up retriever from FAISS index and run RAG pipeline
        retriever = index.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(api_key=openai_api_key),
            chain_type="stuff",
            retriever=retriever
        )

        # Run the query and return the generated response
        response = qa_chain.run(query)
        logging.info(f"Query processed successfully: {query}")
        return {"response": response}
    
    # Handle any errors during query processing
    except Exception as e:
        logging.error(f"Error processing query '{query}': {e}")
        raise HTTPException(status_code=500, detail="Error processing query")

# Helper function to retrieve a document from S3
async def retrieve_document_from_s3(filename: str) -> str:
    try:
        # Retrieve document from S3 asynchronously
        async with s3_client as s3:
            obj = await s3.get_object(Bucket=s3_bucket_name, Key=filename)
            document_content = await obj['Body'].read()
            return document_content.decode('utf-8')
    
    # Handle S3 client errors
    except ClientError as e:
        logging.error(f"S3 Client Error: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving document from S3.")
    
    # Handle general exceptions
    except Exception as e:
        logging.error(f"General error: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving document")
