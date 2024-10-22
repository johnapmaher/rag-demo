from fastapi import FastAPI, HTTPException
import openai
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")

# Example document store
documents = {
    "doc1": "This is the content of document 1.",
    "doc2": "This is the content of document 2."
}

def retrieve_document(query):
    # Simplified retrieval logic: return doc based on keyword match
    return next((doc for doc, content in documents.items() if query in content), None)

@app.post("/rag")
async def rag_query(query: str):
    doc = retrieve_document(query)
    if doc:
        prompt = f"Use the following document to answer: {documents[doc]} \n\n{query}"
        response = openai.Completion.create(
            model="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=150
        )
        return {"response": response.choices[0].text.strip()}
    else:
        raise HTTPException(status_code=404, detail="Document not found")