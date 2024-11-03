import os
import logging
from dotenv import load_dotenv
import pinecone
from langchain_community.vectorstores import Pinecone
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chains import RetrievalQA
from langchain_community.llms import OpenAI
from aws_lambda_powertools.utilities.validation.exceptions import ValidationException

# Load environment variables from .env file
load_dotenv()

# Access the OpenAI API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize Pinecone
pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENVIRONMENT"))

# Connect to Pinecone index
index_name = "your-index-name"
index = pinecone.Index(index_name)

# Initialize Pinecone vector store
vectorstore = Pinecone(index, OpenAIEmbeddings(openai_api_key=openai_api_key))

documents_metadata = {}

def handler(event, context):
    try:
        logging.info("Received request for RAG query")

        query = event.get("query")
        logging.info(f"Extracted query: {query}")

        # Set up retriever from Pinecone index and run RAG pipeline
        logging.info("Setting up retriever from Pinecone index")
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
        raise ValidationException(f"Error processing query: {e}")