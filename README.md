# Angel One Support Chatbot

A Retrieval-Augmented Generation (RAG) chatbot trained on Angel One customer support documentation to assist users by answering queries and providing relevant support information.

## Features

- Answers questions based on Angel One support documentation
- Responds with "I don't know" for questions outside its knowledge base
- User-friendly chat interface
- Retrieves information from both web pages and PDF documents

## Technology Stack

- **Backend**: FastAPI, LangChain, OpenAI, FAISS
- **Frontend**: Streamlit
- **Data Sources**: Angel One support pages and insurance PDFs

## Setup and Installation

### Prerequisites

- Python 3.8+
- OpenAI API key

### Install dependencies:
pip install -r requirements.txt

### Backend Setup

1. Navigate to the backend directory:



### Backend Setup

1. Navigate to the backend directory:
2. cd backend


3. Create a `.env` file with your OpenAI API key:


OPENAI_API_KEY=your_openai_api_key

API_URL = "http://localhost:8000"  # Change this to your backend FastAPI URL

4. Place insurance PDFs in the `insurance_pdfs` directory

5. Start the FastAPI server:
uvicorn app --host 0.0.0.0 --port 8000

### Frontend Setup

1. Navigate to the frontend directory:
2. cd frontend

3. Update the API_URL in .env to point to your backend server

4. Start the Streamlit app:
streamlit run streamlit_app.py

## Usage

1. Open the Streamlit app in your browser
2. Click "Initialize Bot" in the sidebar to load and process the documentation
3. Ask questions about Angel One services in the chat input
4. The bot will respond with relevant information or "I don't know" if the question is outside its knowledge base
