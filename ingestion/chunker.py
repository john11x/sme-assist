from llama_index.core.node_parser import SentenceSplitter

def get_chunker(chunk_size: int = 1024, chunk_overlap: int = 128) -> SentenceSplitter:
    """
    Returns a LlamaIndex SentenceSplitter configured for the SME-Assist project.
    We use a larger chunk size to ensure complex legal sections stay together.
    """
    return SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        secondary_chunking_regex="[^,.;。？！]+[,.;。？！]?"
    )
