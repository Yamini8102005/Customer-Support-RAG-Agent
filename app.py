import os
import sys
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

# Add current directory to path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import rag_pipeline
import generate_faq_pdf

# Load environment variables (.env file)
load_dotenv()

# Streamlit Page Configuration
st.set_page_config(
    page_title="GigaCorp Customer Support RAG Agent",
    page_icon="🤖",
    layout="wide"
)

# Custom Styling for Premium Look
st.markdown("""
<style>
    .reportview-container {
        background: #F3F4F6;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #1E3A8A;
        font-family: 'Inter', sans-serif;
    }
    .stChatInputContainer {
        padding-bottom: 1rem;
    }
    .citation-container {
        background-color: #F9FAFB;
        border-left: 3px solid #0D9488;
        padding: 0.5rem 1rem;
        margin-top: 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
        color: #4B5563;
    }
</style>
""", unsafe_allow_html=True)

# Define directories
DATA_DIR = "data"
PDF_PATH = os.path.join(DATA_DIR, "gigacorp_faq.pdf")
VECTOR_STORE_DIR = "vector_store"

# ==========================================
# BOOTSTRAPPING & SETUP
# ==========================================

# 1. Check & Generate FAQ PDF
if not os.path.exists(PDF_PATH):
    st.info("🔄 First Launch: Generating GigaCorp FAQ PDF document...")
    try:
        generate_faq_pdf.generate_pdf()
        st.success("✅ GigaCorp FAQ PDF successfully generated!")
    except Exception as e:
        st.error(f"Failed to generate FAQ PDF: {e}")
        st.stop()

# 2. Check & Initialize Vector Store
if not os.path.exists(VECTOR_STORE_DIR) or not os.path.exists(os.path.join(VECTOR_STORE_DIR, "index.faiss")):
    with st.spinner("🔄 Building local FAISS Vector database..."):
        try:
            rag_pipeline.initialize_vector_store(PDF_PATH, VECTOR_STORE_DIR)
            st.success("✅ Persistent FAISS Vector database created!")
        except Exception as e:
            st.error(f"Failed to initialize FAISS Vector Store: {e}")
            st.stop()

# Cache the loaded RAG pipeline to avoid reloading the embedding model on every interaction
@st.cache_resource
def get_rag_chain_and_store():
    """
    Loads the persistent vector store and returns the LangChain retrieval chain.
    """
    # Check if a Google API key is configured
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ Google API key is missing! Please set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file.")
        st.stop()
        
    try:
        vector_store = rag_pipeline.load_vector_store(VECTOR_STORE_DIR)
        return rag_pipeline.get_conversational_chain(vector_store), vector_store
    except Exception as e:
        st.error(f"Error loading FAISS vector database: {e}")
        st.stop()

# Load the RAG Chain and vector store
rag_chain, vector_store = get_rag_chain_and_store()

# ==========================================
# SESSION STATE & CHAT MEMORY
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# SIDEBAR INTERFACE
# ==========================================
with st.sidebar:
    st.title("🤖 GigaCorp Portal")
    st.write("Customer Support Dashboard")
    
    st.markdown("---")
    
    # Ingestion Stats
    st.subheader("📊 System Status")
    st.success("Knowledge Base: Connected")
    st.caption(f"Source Doc: `{os.path.basename(PDF_PATH)}`")
    st.caption("Embeddings: `Google text-embedding-04`")
    st.caption("Vector DB: `FAISS (Local)`")
    st.caption("LLM Engine: `Gemini 2.0 Flash`")

    st.markdown("---")
    
    # Actions
    st.subheader("⚙️ Actions")
    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.info(
        "💡 **Support Guidelines:** This AI Agent behaves strictly as a GigaCorp customer rep. "
        "It will answer queries using the official FAQ handbook and cannot address out-of-scope requests."
    )

# ==========================================
# CHAT INTERFACE
# ==========================================
st.title("🤖 GigaCorp Virtual Assistant")
st.write("Welcome to the GigaCorp Automated Support Desk. Ask me about our shipping rates, return policies, subscription protection plans, and technical device troubleshooting.")

# 1. Render Greeting if chat history is empty
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        st.markdown(
            "Hello! I am your GigaCorp Virtual Assistant. How can I help you today? "
            "Feel free to ask questions about our products, return window, shipping speeds, or account security."
        )

# 2. Render Existing Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display Citations if they exist for this message
        if message["role"] == "assistant" and "citations" in message and message["citations"]:
            with st.expander("📚 View Cited Sources", expanded=False):
                for idx, citation in enumerate(message["citations"]):
                    st.markdown(
                        f"**Source {idx+1}:** {citation['source']} (Page {citation['page']})\n"
                        f"_{citation['text'].strip()}_"
                    )

# 3. Capture User Input
if user_input := st.chat_input("Type your question here..."):
    # Display user input immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Store user message in history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Transform message log into LangChain compatible memory objects
    chat_history = []
    for msg in st.session_state.messages[:-1]: # exclude the latest user message which is passed separately
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            chat_history.append(AIMessage(content=msg["content"]))
            
    # Invoke LangChain QA chain
    with st.chat_message("assistant"):
        with st.spinner("GigaCorp Rep is writing response..."):
            try:
                response = rag_chain.invoke({
                    "input": user_input,
                    "chat_history": chat_history
                })
            except Exception as e:
                error_text = str(e).lower()
                if any(marker in error_text for marker in ["quota", "resource_exhausted", "429", "rate limit", "api key", "not found", "generatecontent"]):
                    st.info("The Gemini API is temporarily unavailable, so I’m using the local FAQ fallback.")
                    response = rag_pipeline.get_fallback_answer(vector_store, user_input, chat_history)
                else:
                    st.error(f"An error occurred while communicating with the model: {e}")
                    st.info("Please make sure you have set a valid GOOGLE_API_KEY or GEMINI_API_KEY in your .env file and that the selected Gemini model is supported.")
                    st.stop()
            
            answer = response["answer"]
            context_docs = response.get("context", [])
            
            # Render answer
            st.markdown(answer)
            
            # Extract and compile citations from metadata (deduplicating by page)
            citations = []
            seen_pages = set()
            for doc in context_docs:
                src_file = os.path.basename(doc.metadata.get("source", "gigacorp_faq.pdf"))
                # PyPDFLoader returns page numbers 0-indexed; add 1 for user-facing count
                page_num = doc.metadata.get("page", 0) + 1
                page_key = (src_file, page_num)
                if page_key not in seen_pages:
                    seen_pages.add(page_key)
                    citations.append({
                        "source": src_file,
                        "page": page_num,
                        "text": doc.page_content
                    })
            
            # Render Citations
            if citations:
                with st.expander("📚 View Cited Sources", expanded=False):
                    for idx, citation in enumerate(citations):
                        st.markdown(
                            f"**Source {idx+1}:** {citation['source']} (Page {citation['page']})\n"
                            f"_{citation['text'].strip()}_"
                        )
            
            # Store assistant response and citations in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "citations": citations
            })
