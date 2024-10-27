from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import openai
from langchain_openai import OpenAIEmbeddings
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

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("Missing required environment variables.")

# Set OpenAI API key for LangChain usage
openai.api_key = openai_api_key

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
        logging.info(f"Received upload request for file: {file.filename}")

        # Read file contents
        logging.info("Reading file contents")
        contents = await file.read()

        # Decode and split text for indexing
        logging.info("Decoding file contents to text")
        text = contents.decode("utf-8")
        
        logging.info("Initializing RecursiveCharacterTextSplitter for text splitting")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        
        logging.info("Splitting text into chunks")
        docs = splitter.split_text(text)
        
        logging.info(f"Adding {len(docs)} chunks to FAISS vectorstore")
        vectorstore.add_texts(docs)

        # Store metadata about the uploaded document
        logging.info(f"Storing metadata for file: {file.filename}")
        documents_metadata[file.filename] = {
            "num_chunks": len(docs)
        }

        logging.info(f"Document '{file.filename}' uploaded and indexed successfully")

    except Exception as e:
        logging.error(f"Error processing document '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail="Error processing document")

    return {"filename": file.filename, "message": "Document uploaded and indexed successfully"}

class QueryRequest(BaseModel):
    query: str
    
@app.post("/rag")
async def rag_query(request: QueryRequest):
    try:
        logging.info("Received request for RAG query")

        query = request.query
        logging.info(f"Extracted query: {query}")

        # Set up retriever from FAISS index and run RAG pipeline
        logging.info("Setting up retriever from FAISS index")
        retriever = vectorstore.as_retriever()

        logging.info("Initializing RetrievalQA chain")
        qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(api_key=openai_api_key),
            chain_type="stuff",
            retriever=retriever
        )

        # Run the query and return the generated response
        logging.info("Running query through the QA chain")
        response = qa_chain.run(query)
        
        logging.info(f"Query processed successfully with response: {response}")
        return {"response": response}

    except Exception as e:
        logging.error(f"Error processing query '{query}': {e}")
        raise HTTPException(status_code=500, detail="Error processing query")