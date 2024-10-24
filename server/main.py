from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import aioboto3
from botocore.exceptions import NoCredentialsError, ClientError
import openai
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from fastapi.responses import JSONResponse
import faiss
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://d3memimioruxu.cloudfront.net",
        "http://localhost:3000",
        "http://localhost:8000"  # Allow ECS health check endpoint
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Initialize asynchronous S3 client using aioboto3
async def get_s3_client():
    session = aioboto3.Session()
    return session.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

# Initialize FAISS index for document embeddings
embedding_size = 1536  # Embedding dimension (based on OpenAI's embeddings)
index = faiss.IndexFlatL2(embedding_size)
docstore = InMemoryDocstore()
index_to_docstore_id = {}

# Initialize FAISS vector store
vectorstore = FAISS(OpenAIEmbeddings(openai_api_key=openai_api_key), index, docstore, index_to_docstore_id)

documents_metadata = {}

# Health check endpoint to ensure the API is running
@app.get("/health")
async def health_check():
    return JSONResponse(status_code=200, content={"status": "healthy"})

# Endpoint to upload and process a document
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # Split file contents and add to FAISS index for RAG
        text = contents.decode("utf-8")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_text(text)
        vectorstore.add_texts(docs)

        # Store metadata about the uploaded document
        documents_metadata[file.filename] = {
            "num_chunks": len(docs)
        }
    
    # Handle any errors during document processing
    except Exception as e:
        logging.error(f"Error processing document '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail="Error processing document")

    return {"filename": file.filename, "message": "Document uploaded and indexed successfully"}

class QueryRequest(BaseModel):
    query: str
    
@app.post("/rag")
async def rag_query(request: QueryRequest):
    try:
        # Set up retriever from FAISS index and run RAG pipeline
        retriever = vectorstore.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(api_key=openai_api_key),
            chain_type="stuff",
            retriever=retriever
        )

        # Extract query from the request body
        query = request.query
        
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
        s3_client = await get_s3_client()
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
