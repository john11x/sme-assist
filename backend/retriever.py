import os
import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from ingestion.embedding import get_embedding_model
from config import settings

def get_chroma_client() -> chromadb.PersistentClient:
    """
    Initializes and returns a persistent ChromaDB client.
    The database is saved locally in the directory defined in settings.py.
    """
    # Ensure the directory exists before trying to connect
    os.makedirs(settings.CHROMA_STORE_DIR, exist_ok=True)
    
    # Initialize the client pointing to our local storage directory
    client = chromadb.PersistentClient(path=settings.CHROMA_STORE_DIR)
    return client


def get_vector_store() -> ChromaVectorStore:
    """
    Retrieves the ChromaDB collection and wraps it in a LlamaIndex VectorStore.
    This creates the bridge between where the data is stored (Chroma)
    and the tool we use to query it (LlamaIndex).
    """
    client = get_chroma_client()
    
    # Get or create the collection where our vectors live
    collection = client.get_or_create_collection(name=settings.CHROMA_COLLECTION_NAME)
    
    # Bind the Chroma collection to a LlamaIndex VectorStore
    vector_store = ChromaVectorStore(chroma_collection=collection)
    return vector_store


def get_retriever():
    """
    Creates the retriever engine that takes in a user query and returns
    the most relevant document chunks based on semantic similarity.
    """
    vector_store = get_vector_store()
    
    Settings.embed_model = get_embedding_model()
    # Create an index from the vector store
    # Note: normally we load documents into the index here, but for retrieval 
    # we just need the empty index shell wrapped around the existing store.
    index = VectorStoreIndex.from_vector_store(vector_store)
    
    # Configure the retriever to return the top K most similar chunks
    retriever = index.as_retriever(similarity_top_k=settings.SIMILARITY_TOP_K)
    return retriever
