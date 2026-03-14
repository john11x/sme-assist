import os
import pandas as pd
from llama_parse import LlamaParse
from llama_index.core import Document
from llama_index.readers.file import PDFReader
from config import settings

def parse_pdf_llama(file_path: str) -> list[Document]:
    """
    Parses a PDF file using LlamaParse for superior layout and table handling.
    """
    if not settings.LLAMA_CLOUD_API_KEY:
        print("⚠️ LLAMA_CLOUD_API_KEY not found. Skipping LlamaParse.")
        return []

    # Initialize LlamaParse
    parser = LlamaParse(
        api_key=settings.LLAMA_CLOUD_API_KEY,
        result_type="markdown",
        verbose=True
    )
    
    return parser.load_data(file_path)

def parse_pdf_local(file_path: str) -> list[Document]:
    """
    Parses a PDF file using the free, local PDF reader.
    Best for text-heavy documents without complex tables.
    """
    print(f"📂 Using local PDF parser for: {os.path.basename(file_path)}")
    loader = PDFReader()
    return loader.load_data(file=Path(file_path))

def parse_excel_tax_return(file_path: str) -> list[Document]:
    """
    Specifically handles the KRA Excel Tax Return by extracting field names and structure.
    """
    try:
        xl = pd.ExcelFile(file_path)
        all_text = []
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name)
            sheet_text = f"--- Sheet: {sheet_name} ---\n"
            sheet_text += df.to_string(index=False)
            all_text.append(sheet_text)
            
        combined_text = "\n\n".join(all_text)
        return [Document(text=combined_text, metadata={"file_name": os.path.basename(file_path), "source_type": "excel_tax_return"})]
    except Exception as e:
        print(f"Error parsing Excel file {file_path}: {e}")
        return []

from pathlib import Path

def get_documents_from_file(file_path: str) -> list[Document]:
    """
    Orchestrator that decides which parser to use. 
    Defaults to local/free but allows LlamaParse if configured.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        # Strategy: Use LlamaParse ONLY if key is present AND it's a small file (< 5MB)
        # Otherwise use local to save credits.
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        if settings.LLAMA_CLOUD_API_KEY and file_size_mb < 5:
            try:
                print(f"✨ LlamaParse prioritized for small/complex file: {os.path.basename(file_path)}")
                return parse_pdf_llama(file_path)
            except Exception as e:
                print(f"❌ LlamaParse failed: {e}. Falling back to local.")
        
        return parse_pdf_local(file_path)
        
    elif ext == ".txt":
        with open(file_path, "r") as f:
            text = f.read()
        return [Document(text=text, metadata={"file_name": os.path.basename(file_path), "source_type": "text"})]
    elif ext in [".xls", ".xlsx"]:
        return parse_excel_tax_return(file_path)
    else:
        print(f"Unsupported file type: {ext}")
        return []
