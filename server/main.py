from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
import requests

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

# Replace static document store with Wikipedia API integration
def retrieve_document(query: str) -> str:
    # Fetch document from Wikipedia based on the query
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
    response = requests.get(url)
    print(response)
    if response.status_code == 200:
        data = response.json()
        return data.get("extract", "No content found")
    else:
        return None

class RequestModel(BaseModel):
    query: str

client = OpenAI()

@app.post("/rag")
async def rag_query(request: RequestModel):
    # Retrieve the document dynamically from Wikipedia
    document_content = retrieve_document(request.query)
    if document_content:
        prompt = f"I want to know about the following document: {document_content} \n\n{request.query}"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "The following is a conversation with an AI assistant."},
                {"role": "user", "content": prompt},],
            max_tokens=150
        )
        return {"response": response.choices[0].text.strip()}
    else:
        raise HTTPException(status_code=404, detail="Document not found")