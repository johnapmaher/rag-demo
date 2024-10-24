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
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from io import BytesIO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://d3memimioruxu.cloudfront.net"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
s3_bucket_name = os.getenv("S3_BUCKET_NAME")
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

if not openai_api_key or not s3_bucket_name or not aws_access_key_id or not aws_secret_access_key:
    raise ValueError("Missing required environment variables.")

# Set OpenAI API key
openai.api_key = openai_api_key

# Initialize aioboto3 S3 client for async operations
s3_client = aioboto3.client(
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
async def upload_document(file: UploadFile = File(...), s3_client=Depends(get_s3_client)):
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Invalid file format. Only .txt files are allowed.")
    if file.spool_max_size > (2 * 1024 * 1024):  # Limit to 2MB
        raise HTTPException(status_code=400, detail="File size exceeds the limit of 2MB.")
    try:
        contents = await file.read()

        async with s3_client as s3:
            await s3.put_object(Bucket=s3_bucket_name, Key=file.filename, Body=contents)

        # Add document to LangChain FAISS index for RAG
        text = contents.decode("utf-8")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_text(text)

        # Add to the FAISS index
        index.add_texts(docs)

        # Store metadata in local store
        documents_metadata[file.filename] = {
            "num_chunks": len(docs)
        }

        return {"filename": file.filename, "message": "Document uploaded and indexed successfully"}
    except NoCredentialsError:
        logging.error("AWS credentials are missing or invalid.")
        raise HTTPException(status_code=500, detail="AWS credentials are missing or invalid.")
    except ClientError as e:
        logging.error(f"S3 Client Error: {e}")
        raise HTTPException(status_code=500, detail="Error uploading document to S3.")
    except Exception as e:
        logging.error(f"General error: {e}")
        raise HTTPException(status_code=500, detail="Error uploading document")

@app.post("/rag")
async def rag_query(query: str):
    try:
        retriever = index.as_retriever()

        qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(api_key=openai_api_key),
            chain_type="stuff",
            retriever=retriever
        )

        response = qa_chain.run(query)
        logging.info(f"Query processed successfully: {query}")
        return {"response": response}
    except Exception as e:
        logging.error(f"Error processing query '{query}': {e}")
        raise HTTPException(status_code=500, detail="Error processing query")


async def retrieve_document_from_s3(filename: str) -> str:
    try:
        # Fetch the document from S3 asynchronously
        async with s3_client as s3:
            obj = await s3.get_object(Bucket=s3_bucket_name, Key=filename)
            document_content = await obj['Body'].read()
            return document_content.decode('utf-8')
    except ClientError as e:
        logging.error(f"S3 Client Error: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving document from S3.")
    except Exception as e:
        logging.error(f"General error: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving document")
