import streamlit as st
import requests
import json
from dotenv import load_dotenv
import os 

load_dotenv()

API_URL = os.getenv("API_URL") # Change this to your backend FastAPI URL

st.set_page_config(
    page_title="Angel One Support Bot",
    page_icon="💬",
    layout="centered"
)

st.markdown("""
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e
}
.chat-message.bot {
    background-color: #475063
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize session state for bot status
if "bot_initialized" not in st.session_state:
    st.session_state.bot_initialized = False

# App title
st.title("Angel One Support Assistant")

# Sidebar for initialization
with st.sidebar:
    st.header("About")
    st.info("This chatbot is trained on Angel One support documentation to help answer your queries.")
    
    if not st.session_state.bot_initialized:
        if st.button("Initialize Bot"):
            with st.spinner("Initializing the bot... This may take a few minutes."):
                response = requests.post(f"{API_URL}/initialize")
                if response.status_code == 200:
                    st.session_state.bot_initialized = True
                    st.success("Bot initialized successfully!")
                else:
                    st.error(f"Failed to initialize bot: {response.text}")
    else:
        st.success("Bot is ready to answer your questions!")
    
    st.markdown("---")
    st.markdown("Powered by LangChain and OpenAI")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about Angel One services..."):
    if not st.session_state.bot_initialized:
        st.error("Please initialize the bot first using the button in the sidebar.")
    else:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = requests.post(
                    f"{API_URL}/query",
                    json={"question": prompt}
                )
                
                if response.status_code == 200:
                    answer = response.json().get("answer", "I encountered an error processing your question.")
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = f"Error: {response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})