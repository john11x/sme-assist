import os
import sys
from pathlib import Path

# Add project root to python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from ingestion.parser import get_documents_from_file
from ingestion.chunker import get_chunker
from ingestion.embedding import get_embedding_model
from backend.retriever import get_vector_store
from llama_index.core import StorageContext, VectorStoreIndex
from config import settings
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def run_ingestion(start_batch=1):
    """
    Orchestrates the entire ingestion process:
    1. Scan data/raw_docs/
    2. Parse each file
    3. Chunk text
    4. Generate embeddings
    5. Save to ChromaDB
    """
    raw_docs_path = os.path.join(settings.BASE_DIR, "data", "raw_docs")
    if not os.path.exists(raw_docs_path):
        print(f"Error: Directory {raw_docs_path} does not exist.")
        return

    files = [f for f in os.listdir(raw_docs_path) if not f.startswith(".")]
    if not files:
        print("No files found to ingest.")
        return

    print(f"🚀 Starting ingestion for {len(files)} files...")
    if start_batch > 1:
        print(f"⏩ Resuming from batch {start_batch}...")

    # Calculate approximate total size to warn user
    total_size_mb = sum(os.path.getsize(os.path.join(raw_docs_path, f)) for f in files) / (1024 * 1024)
    print(f"📊 Total Data Size: {total_size_mb:.2f} MB")
    
    if not settings.GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY is missing. Ingestion cannot proceed without an embedding model.")
        return

    # Load infrastructure components
    try:
        vector_store = get_vector_store()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        embed_model = get_embedding_model()
        node_parser = get_chunker()
    except Exception as e:
        print(f"❌ Initialization Error: {e}")
        return

    all_docs = []
    for file_name in files:
        file_path = os.path.join(raw_docs_path, file_name)
        print(f"📄 Parsing: {file_name}...")
        try:
            docs = get_documents_from_file(file_path)
            all_docs.extend(docs)
        except Exception as e:
            print(f"❌ Error parsing {file_name}: {e}")

    if not all_docs:
        print("No documents successfully parsed. Exiting.")
        return

    print(f"🔨 Converting {len(all_docs)} documents into chunks (nodes)...")
    nodes = node_parser.get_nodes_from_documents(all_docs)
    total_nodes = len(nodes)
    print(f"✨ Generated {total_nodes} nodes. Starting batched indexing...")

    # Initialize index with empty nodes
    index = VectorStoreIndex(
        nodes=[],
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True
    )

    # Insert nodes in batches with robust retry for rate limits
    import time
    from google.api_core import exceptions
    
    batch_size = 5  # More conservative batch size to avoid 429
    total_batches = (total_nodes + batch_size - 1) // batch_size
    
    start_index = (start_batch - 1) * batch_size
    
    for i in range(start_index, len(nodes), batch_size):
        current_batch_num = i // batch_size + 1
        batch = nodes[i : i + batch_size]
        print(f"📦 Indexing batch {current_batch_num} of {total_batches} ({len(batch)} nodes)...")
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                index.insert_nodes(batch)
                break
            except exceptions.ResourceExhausted as e:
                wait_time = (2 ** attempt) * 60  # Start with 60s wait
                print(f"🛑 Rate limit hit on batch {current_batch_num}. Attempt {attempt + 1}/{max_retries}. Waiting {wait_time}s...")
                time.sleep(wait_time)
            except Exception as e:
                print(f"❌ Critical error during indexing: {e}")
                raise e
        else:
            print(f"❌ Failed to index batch {current_batch_num} after {max_retries} attempts.")
            return

        if i + batch_size < len(nodes):
            time.sleep(10) # Buffer between successful batches

    print("✅ Ingestion complete! Data is now persistent in ChromaDB.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest documents into ChromaDB.")
    parser.add_argument("--start-batch", type=int, default=1, help="Batch number to resume from")
    args = parser.parse_args()
    
    run_ingestion(start_batch=args.start_batch)
