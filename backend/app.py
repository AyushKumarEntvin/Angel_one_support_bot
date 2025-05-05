from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import requests
from bs4 import BeautifulSoup
import urllib.parse
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store the conversation chain
vectorstore = None
conversation_chain = None

class Query(BaseModel):
    question: str

def get_pdf_text(pdf_path):
    text = ""
    pdf_reader = PdfReader(pdf_path)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main content (adjust selectors based on the website structure)
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if main_content:
            return main_content.get_text(separator='\n', strip=True)
        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def crawl_support_site(base_url):
    visited = set()
    to_visit = [base_url]
    all_text = ""
    
    while to_visit and len(visited) < 100:  # Limit to prevent infinite crawling
        url = to_visit.pop(0)
        if url in visited or not url.startswith(base_url):
            continue
            
        print(f"Crawling: {url}")
        visited.add(url)
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content
            content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if content:
                all_text += f"\n\nPAGE: {url}\n" + content.get_text(separator='\n', strip=True)
            
            # Find more links
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urllib.parse.urljoin(url, href)
                if full_url.startswith(base_url) and full_url not in visited and full_url not in to_visit:
                    to_visit.append(full_url)
        except Exception as e:
            print(f"Error processing {url}: {e}")
    
    return all_text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vectorstore):
    llm = ChatOpenAI(temperature=0)
    
    # Create memory with output_key specified
    memory = ConversationBufferMemory(
        memory_key='chat_history',
        return_messages=True,
        output_key='answer'  
    )
    
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        return_source_documents=True,
        verbose=True
    )
    
    return conversation_chain

@app.post("/initialize")
async def initialize_bot():
    global vectorstore, conversation_chain
    
    # Collect text from Angel One support pages
    support_text = crawl_support_site("https://www.angelone.in/support")
    
    # Process insurance PDFs (assuming they're in a directory)
    pdf_dir = "insurance_pdfs"
    pdf_text = ""
    if os.path.exists(pdf_dir):
        for filename in os.listdir(pdf_dir):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(pdf_dir, filename)
                pdf_text += get_pdf_text(pdf_path)
    
    # Combine all text
    all_text = support_text + "\n\n" + pdf_text
    
    # Process text
    text_chunks = get_text_chunks(all_text)
    vectorstore = get_vectorstore(text_chunks)
    conversation_chain = get_conversation_chain(vectorstore)
    
    return {"status": "success", "message": "Bot initialized successfully"}

@app.post("/query")
async def query_bot(query: Query):
    global conversation_chain
    
    if not conversation_chain:
        raise HTTPException(status_code=400, detail="Bot not initialized. Call /initialize first.")
    
    try:
        response = conversation_chain({"question": query.question})
        
        # Check if the answer is based on retrieved documents
        if not response.get("source_documents") or len(response["source_documents"]) == 0:
            return {"answer": "I don't know the answer to that question. Please ask something related to Angel One support documentation."}
        
        # Get the answer from the response
        answer = response.get("answer", "I couldn't find a specific answer to your question.")
        
        sources = []
        if response.get("source_documents"):
            for i, doc in enumerate(response["source_documents"]):
                if hasattr(doc, "metadata") and doc.metadata.get("source"):
                    sources.append(doc.metadata["source"])
        
        return {
            "answer": answer,
            "sources": sources[:3] if sources else []  # Return up to 3 sources
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"answer": f"Error processing your question: {str(e)}"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}