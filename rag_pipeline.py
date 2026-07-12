import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.embeddings import HuggingFaceEmbeddings

# Use Google API-based embeddings when available; otherwise fall back to a local model.
EMBEDDING_MODEL_NAME = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
LLM_MODEL_NAME = os.getenv("GEMINI_LLM_MODEL", "gemini-2.0-flash")
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "auto")


def get_google_api_key() -> str:
    """Return a Google API key from either supported environment variable name."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Google API key is missing. Set GOOGLE_API_KEY or GEMINI_API_KEY in your environment.")
    return api_key


class FallbackEmbeddings(Embeddings):
    """Use Google embeddings when available and fall back to a local model on failure."""

    def __init__(self):
        self._google_embeddings = None
        self._local_embeddings = None

    def _get_google_embeddings(self):
        if self._google_embeddings is None:
            self._google_embeddings = GoogleGenerativeAIEmbeddings(
                model=EMBEDDING_MODEL_NAME,
                google_api_key=get_google_api_key(),
            )
        return self._google_embeddings

    def _get_local_embeddings(self):
        if self._local_embeddings is None:
            self._local_embeddings = HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)
        return self._local_embeddings

    def embed_documents(self, texts, **kwargs):
        if EMBEDDING_BACKEND.lower() == "local":
            return self._get_local_embeddings().embed_documents(texts, **kwargs)

        try:
            return self._get_google_embeddings().embed_documents(texts, **kwargs)
        except Exception as exc:
            print(f"Google embeddings failed during document embedding, falling back to local embeddings: {exc}")
            return self._get_local_embeddings().embed_documents(texts, **kwargs)

    def embed_query(self, text, **kwargs):
        if EMBEDDING_BACKEND.lower() == "local":
            return self._get_local_embeddings().embed_query(text, **kwargs)

        try:
            return self._get_google_embeddings().embed_query(text, **kwargs)
        except Exception as exc:
            print(f"Google embeddings failed during query embedding, falling back to local embeddings: {exc}")
            return self._get_local_embeddings().embed_query(text, **kwargs)


def get_embeddings():
    """Create embedding object with automatic Google-to-local fallback."""
    return FallbackEmbeddings()

def initialize_vector_store(pdf_path: str, store_path: str):
    """
    Reads the PDF, splits it into chunks, generates embeddings,
    and saves the persistent FAISS index locally.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Source PDF not found at: {pdf_path}")
        
    print(f"Loading PDF from {pdf_path}...")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    print("Splitting document text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(documents)
    
    print("Initializing embeddings...")
    embeddings = get_embeddings()
    
    print("Building FAISS index and adding chunks...")
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    print(f"Saving persistent vector store to {store_path}...")
    vector_store.save_local(store_path)
    return vector_store

def load_vector_store(store_path: str):
    """
    Loads the persistent FAISS vector store from disk.
    """
    embeddings = get_embeddings()
    return FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)


def get_fallback_answer(vector_store, user_input: str, chat_history=None):
    """Return a local FAQ-based answer when the Gemini API is unavailable."""
    docs = vector_store.similarity_search(user_input, k=3)
    if docs:
        snippets = []
        for idx, doc in enumerate(docs, 1):
            excerpt = " ".join(doc.page_content.split())
            snippets.append(f"{idx}. {excerpt[:700]}")
        answer = (
            "The Gemini API is currently unavailable or rate-limited, so I’m answering from the local FAQ instead.\n\n"
            "Relevant information:\n"
            + "\n\n".join(snippets)
        )
        return {"answer": answer, "context": docs}

    return {
        "answer": "The Gemini API is currently unavailable or rate-limited. Please try again shortly or check your API quota.",
        "context": []
    }


def get_conversational_chain(vector_store):
    """
    Creates a conversational retrieval RAG chain using LangChain.
    - Condenses follow-up questions using chat history.
    - Retrieves top matches from the FAISS database.
    - Answers using a professional customer support persona with Gemini.
    """
    # Initialize the Gemini LLM
    # ChatGoogleGenerativeAI automatically reads GEMINI_API_KEY from environment variables
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL_NAME,
        temperature=0.0,
        google_api_key=get_google_api_key(),
    )
    
    # 1. contextualize_q_chain: Reformulates the user's follow-up questions
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    # Retrieve top 3 relevant sections
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )
    
    # 2. qa_chain: Answers the reformulated question using context
    system_prompt = (
        "You are a professional, helpful, and friendly customer support assistant for GigaCorp.\n"
        "Your task is to answer the customer's question using ONLY the provided context below. "
        "If the answer cannot be found in the context, respond politely stating that you do not "
        "have that information in your system, and offer to help with other GigaCorp product or support queries. "
        "Do not invent facts or answer questions unrelated to GigaCorp.\n\n"
        "Context:\n"
        "{context}"
    )
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # Combine the history-aware retriever and question-answering chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    return rag_chain
