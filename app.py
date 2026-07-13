import os
import sys
from dotenv import load_dotenv
# Load environment variables (.env file)
load_dotenv()

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

# Add current directory to path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import rag_pipeline
import generate_faq_pdf

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

# 1. Check Google Gemini API Key configuration
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ Google API key is missing! Please set GOOGLE_API_KEY or GEMINI_API_KEY in your Render environment variables or .env file.")
    st.stop()

# Ensure both environment variables are set in os.environ for compatibility with langchain-google-genai
if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = api_key
if not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = api_key

# 2. Check & Generate FAQ PDF
if not os.path.exists(PDF_PATH):
    st.info("🔄 First Launch: Generating GigaCorp FAQ PDF document...")
    try:
        generate_faq_pdf.generate_pdf()
        st.success("✅ GigaCorp FAQ PDF successfully generated!")
    except Exception as e:
        st.error(f"Failed to generate FAQ PDF: {e}")
        st.stop()

# 3. Check & Initialize Vector Store
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
    try:
        vector_store = rag_pipeline.load_vector_store(VECTOR_STORE_DIR)
        
        # Verify the dimensions match the current embedding model to prevent downstream AssertionError
        embeddings = rag_pipeline.get_embeddings()
        sample_vector = embeddings.embed_query("test")
        if vector_store.index.d != len(sample_vector):
            raise ValueError(
                f"Vector store dimension mismatch: loaded index has {vector_store.index.d} dimensions, "
                f"but current embedding model requires {len(sample_vector)} dimensions."
            )
            
        return rag_pipeline.get_conversational_chain(vector_store), vector_store
    except Exception as e:
        st.warning(f"⚠️ Failed to load persistent vector store: {e}. Attempting to rebuild and persist index...")
        
        # Safely remove incompatible or corrupted files before rebuilding
        try:
            import shutil
            if os.path.exists(VECTOR_STORE_DIR):
                shutil.rmtree(VECTOR_STORE_DIR, ignore_errors=True)
        except Exception as delete_error:
            st.warning(f"Could not delete vector store directory: {delete_error}")
            
        try:
            vector_store = rag_pipeline.initialize_vector_store(PDF_PATH, VECTOR_STORE_DIR)
            return rag_pipeline.get_conversational_chain(vector_store), vector_store
        except Exception as rebuild_error:
            st.error(f"❌ Failed to rebuild and load FAISS Vector Store: {rebuild_error}")
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
                    import traceback
                    traceback.print_exc()
                    st.error(f"An error occurred while communicating with the model: {e}")
                    with st.expander("🔍 View Technical Details / Traceback", expanded=False):
                        st.code(traceback.format_exc())
                    st.info("Please make sure you have set a valid GOOGLE_API_KEY or GEMINI_API_KEY in your .env file and that the selected Gemini model is supported.")
                    st.stop()
            
            answer = response["answer"]
            context_docs = response.get("context", [])
            
            # Extract and compile citations from metadata
            citations = []
            seen_pages = set()
            sources_md = ""
            
            if context_docs:
                sources_md += "\n\n**Sources:**\n"
                for doc in context_docs:
                    src_file = os.path.basename(doc.metadata.get("source", "gigacorp_faq.pdf"))
                    page_num = doc.metadata.get("page", 0) + 1
                    page_key = (src_file, page_num)
                    
                    if page_key not in seen_pages:
                        seen_pages.add(page_key)
                        citations.append({
                            "source": src_file,
                            "page": page_num,
                            "text": doc.page_content
                        })
                    
                    # Extract a clean context preview or section title
                    lines = [line.strip() for line in doc.page_content.split("\n") if line.strip()]
                    first_line = lines[0] if lines else ""
                    # Clean up formatting characters
                    first_line = first_line.replace("#", "").replace("•", "").strip()
                    if len(first_line) > 100:
                        first_line = first_line[:97] + "..."
                    if not first_line:
                        first_line = "General manual excerpt"
                        
                    sources_md += f"- {src_file} (Page {page_num})\n  - Retrieved context: {first_line}\n"
            
            # Combine answer and explicitly formatted sources
            full_display_content = answer + sources_md
            
            # Render answer and sources in the main message
            st.markdown(full_display_content)
            
            # Store assistant response in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_display_content,
                "citations": citations
            })
