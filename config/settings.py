import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# --- Base Paths ---
# Get the absolute path to the project root directory (sme-assist/)
BASE_DIR = Path(__file__).resolve().parent.parent

# --- API Keys ---
# Load from .env file
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Vector Database Configuration ---
# Absolute path to the directory where ChromaDB will store its SQLite file
CHROMA_STORE_DIR = os.path.join(BASE_DIR, "vector_db", "chroma_store")

# The name of the collection inside ChromaDB where we store our document vectors
CHROMA_COLLECTION_NAME = "sme_regulatory_docs"

# Configuration for the retriever
SIMILARITY_TOP_K = 3  # The number of most relevant chunks to return for each query
