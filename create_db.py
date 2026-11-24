import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.vectorstores import VectorStoreRetriever

load_dotenv()

DEFAULT_CHROMA_DIR = os.getenv("CHROMA_DB_PATH", "chroma_db")

# Singleton cache for embedding model to avoid reloading on every request
_EMBEDDINGS_INSTANCE = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Initialize and cache HuggingFaceEmbeddings instance."""
    global _EMBEDDINGS_INSTANCE
    if _EMBEDDINGS_INSTANCE is None:
        _EMBEDDINGS_INSTANCE = HuggingFaceEmbeddings()
    return _EMBEDDINGS_INSTANCE


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Return text splitter with project-standard chunk size and overlap."""
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )


def get_vectorstore(
    collection_name: str = "langchain",
    persist_directory: Optional[str] = None
) -> Chroma:
    """
    Get or initialize a Chroma vectorstore for a specific collection.
    """
    db_path = persist_directory or DEFAULT_CHROMA_DIR
    os.makedirs(db_path, exist_ok=True)
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=db_path
    )


def process_pdf(
    pdf_path: str,
    collection_name: str,
    persist_directory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load an uploaded PDF, split it into chunks, generate embeddings,
    and persist them into a Chroma collection.
    
    Args:
        pdf_path: Absolute or relative path to the PDF file.
        collection_name: Unique collection identifier for document/user.
        persist_directory: Directory where Chroma vectors are stored.
        
    Returns:
        Dictionary containing processing stats: chunks_count, pages_count, collection_name.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # 1. Load document using PyPDFLoader
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    if not docs:
        raise ValueError("The uploaded PDF is empty or could not be parsed.")

    # 2. Split into chunks using project standard RecursiveCharacterTextSplitter
    splitter = get_text_splitter()
    chunks = splitter.split_documents(docs)

    # Ensure metadata has human-readable page number (1-based) and filename
    doc_name = os.path.basename(pdf_path)
    for chunk in chunks:
        chunk.metadata["document_name"] = doc_name
        if "page" in chunk.metadata:
            chunk.metadata["display_page"] = chunk.metadata["page"] + 1

    # 3. Store in isolated Chroma collection
    db_path = persist_directory or DEFAULT_CHROMA_DIR
    os.makedirs(db_path, exist_ok=True)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=collection_name,
        persist_directory=db_path
    )

    return {
        "success": True,
        "collection_name": collection_name,
        "pages_count": len(docs),
        "chunks_count": len(chunks),
        "filename": doc_name
    }


def get_document_retriever(
    collection_name: str,
    persist_directory: Optional[str] = None,
    k: int = 4,
    fetch_k: int = 10,
    lambda_mult: float = 0.5
) -> VectorStoreRetriever:
    """
    Initialize and return an MMR retriever for the specified collection,
    using the exact parameters from the existing pipeline.
    """
    vectorstore = get_vectorstore(
        collection_name=collection_name,
        persist_directory=persist_directory
    )
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": k,
            "fetch_k": fetch_k,
            "lambda_mult": lambda_mult
        }
    )


def delete_document_collection(
    collection_name: str,
    persist_directory: Optional[str] = None
) -> bool:
    """
    Delete a document collection from ChromaDB.
    """
    db_path = persist_directory or DEFAULT_CHROMA_DIR
    try:
        vectorstore = get_vectorstore(
            collection_name=collection_name,
            persist_directory=db_path
        )
        vectorstore.delete_collection()
        return True
    except Exception as e:
        print(f"Error deleting collection {collection_name}: {e}")
        return False


if __name__ == "__main__":
    # Test script with existing sample PDF
    sample_pdf = os.path.join("document loaders", "deeplearning.pdf")
    if os.path.exists(sample_pdf):
        print(f"Testing process_pdf on {sample_pdf}...")
        res = process_pdf(sample_pdf, collection_name="test_collection")
        print("Result:", res)
        retriever = get_document_retriever("test_collection")
        test_docs = retriever.invoke("deep learning")
        print(f"Retrieved {len(test_docs)} chunks successfully.")
    else:
        print("Sample PDF not found.")
