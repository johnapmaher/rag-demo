# RAG Demo Application

This application demonstrates Retrieval-Augmented Generation (RAG) using a FastAPI backend and a React frontend. It integrates with OpenAI's API for text generation and allows users to upload documents, which are stored in an S3 bucket and used to augment responses with relevant document content via LangChain.

## Features

    Document Upload to S3: Upload documents to an S3 bucket using FastAPI, which are then indexed for retrieval using LangChain and FAISS.
    RAG (Retrieval-Augmented Generation): Generates responses augmented with content retrieved from indexed documents.
    React Frontend: Provides a simple interface for document upload and querying.

## Installation

### Prerequisites

    - Node.js (for the React frontend)
    - Python 3.7+ (for the FastAPI backend)
    - AWS S3 Bucket (for document storage)
    - OpenAI API Key
    - AWS Credentials (for S3 access)

### Frontend Setup (React)

1. Navigate to the frontend directory:

    `cd frontend`

2. Install the required dependencies:
    
`npm install`

3.Start the development server:

bash

    npm start

Backend Setup (FastAPI)

    Navigate to the backend directory:

    bash

cd backend

Install the required Python dependencies:

bash

pip install -r requirements.txt

Create a .env file in the backend directory and add the following environment variables:

bash

OPENAI_API_KEY=your_openai_api_key
S3_BUCKET_NAME=your_s3_bucket_name
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

Run the FastAPI development server:

bash

    uvicorn main:app --reload

Usage
Document Upload

    Access the React frontend at http://localhost:3000/.
    Use the "Upload" feature to upload documents to S3.
    The document is automatically split into chunks, indexed using FAISS, and stored for retrieval.

Querying with RAG

    Enter a query into the input box and click "Submit".
    The system retrieves relevant content from uploaded documents using LangChain and generates a response via the OpenAI API.

API Endpoints
/upload [POST]

Uploads a document to the S3 bucket and indexes it for retrieval.

Request Body:

    file: The document to be uploaded (text files).

Response:

json

{
  "filename": "example.txt",
  "message": "Document uploaded and indexed successfully"
}

/rag [POST]

Handles queries and retrieves relevant content from the indexed documents, then generates a response using OpenAI's GPT model.

Request Body:

json

{
  "query": "Tell me about machine learning"
}

Response:

json

{
  "response": "Machine learning is a field of artificial intelligence..."
}

Environment Variables

    OPENAI_API_KEY: Your OpenAI API key.
    S3_BUCKET_NAME: The name of your S3 bucket.
    AWS_ACCESS_KEY_ID: Your AWS Access Key ID.
    AWS_SECRET_ACCESS_KEY: Your AWS Secret Access Key.

Deployment
Frontend (AWS S3 and CloudFront)

    Build the React frontend:

    bash

    npm run build

    Upload the build files to an S3 bucket.

    Set up CloudFront for global distribution.

Backend (AWS EC2 or Lambda)

    EC2: Launch an EC2 instance, install dependencies, and run the FastAPI app.
    Lambda: Deploy the FastAPI app as a Lambda function and expose it via API Gateway.
