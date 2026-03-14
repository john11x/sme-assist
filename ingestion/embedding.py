import os
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from config import settings

def get_embedding_model() -> GoogleGenAIEmbedding:
    """
    Returns the Google GenAI embedding model for generating vector representations.
    """
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set in the environment.")
    
    # Initialize Google GenAI Embedding model
    return GoogleGenAIEmbedding(
        api_key=settings.GOOGLE_API_KEY,
        model_name="models/gemini-embedding-001"
    )
