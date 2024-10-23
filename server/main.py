from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import openai
import boto3
from botocore.exceptions import NoCredentialsError
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Set OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logging.error("OPENAI_API_KEY environment variable is not set.")
    raise ValueError("OPENAI_API_KEY environment variable is not set.")
openai.api_key = openai_api_key

# Set AWS S3 configurations
s3_bucket_name = os.getenv("S3_BUCKET_NAME")
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

# LangChain setup: embedding and FAISS index
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
index = FAISS(embeddings)

# In-memory document store for metadata
documents_metadata = {}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Read file contents
        contents = await file.read()

        # Upload file to S3
        s3.put_object(Bucket=s3_bucket_name, Key=file.filename, Body=contents)

        # Add document to LangChain FAISS index for RAG
        text = contents.decode("utf-8")
        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = splitter.split_text(text)

        # Add to the FAISS index
        index.add_texts(docs)

        # Store metadata in local store (or could use a database)
        documents_metadata[file.filename] = {
            "num_chunks": len(docs)
        }

        return {"filename": file.filename, "message": "Document uploaded and indexed successfully"}
    except NoCredentialsError:
        logging.error("AWS credentials are missing or invalid.")
        raise HTTPException(status_code=500, detail="AWS credentials are missing or invalid.")
    except Exception as e:
        logging.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Error uploading document")

@app.post("/rag")
async def rag_query(query: str):
    try:
        # Set up the retriever
        retriever = index.as_retriever()

        # Set up LangChain RAG pipeline using OpenAI LLM
        qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(api_key=openai_api_key),
            chain_type="stuff",
            retriever=retriever
        )

        # Get the response using RAG pipeline
        response = qa_chain.run(query)
        return {"response": response}
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="Error processing query")

def retrieve_document_from_s3(filename: str) -> str:
    try:
        # Fetch the document from S3
        obj = s3.get_object(Bucket=s3_bucket_name, Key=filename)
        document_content = obj['Body'].read().decode('utf-8')
        return document_content
    except Exception as e:
        logging.error(f"Error retrieving document from S3: {e}")
        return None
