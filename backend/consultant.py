import os
import pandas as pd
from llama_index.core import VectorStoreIndex, QueryBundle, Settings
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.indices.postprocessor import SimilarityPostprocessor
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.groq import Groq
from ingestion.embedding import get_embedding_model
from backend.retriever import get_vector_store
from ingestion.parser import get_documents_from_file
from config import settings
from dotenv import load_dotenv

load_dotenv()

class TaxConsultant:
    def __init__(self):
        """
        Initializes the Tax Consultant with the regulatory knowledge base
        and the Gemini LLM for reasoning.
        """
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing from environment.")
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing from environment.")
            
        # Primary for Chat: Gemini (Better Reasoning/RAG context)
        # Fallback for Chat & Primary for Extraction: Groq (Infinite speed/Stable Quota)
        self.gemini_llm = GoogleGenAI(api_key=settings.GOOGLE_API_KEY, model="models/gemini-flash-latest")
        self.groq_llm = Groq(api_key=settings.GROQ_API_KEY, model="llama-3.3-70b-versatile")
        
        Settings.llm = self.gemini_llm # Default
        Settings.embed_model = get_embedding_model()
        
        self.llm = Settings.llm
        
        # Load the regulatory index from ChromaDB
        vector_store = get_vector_store()
        self.index = VectorStoreIndex.from_vector_store(vector_store)
        
        # Set up a query engine for the regulatory knowledge
        self.query_engine = self.index.as_query_engine(
            llm=self.llm,
            similarity_top_k=5
        )

    def chat_with_fallback(self, prompt: str):
        """
        Attempts to query Gemini for high-quality RAG reasoning first.
        If Gemini returns a 429 (Resource Exhausted), transparently falls back to Groq.
        """
        try:
            response = self.llm.complete(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("⚡ Gemini Quota Hit. Falling back to Groq Llama 3 for reasoning...")
                # Temporarily switch query engine to Groq for this turn
                response = self.groq_llm.complete(prompt)
                return response.text
            raise e

    def analyze_user_data(self, user_file_path: str):
        """
        Processes a user's financial document (e.g., bank statement) 
        and extracts structured financial data.
        """
        print(f"🕵️ Analyzing user file: {os.path.basename(user_file_path)}...")
        
        # Parse the user document (bank statements, receipts, etc.)
        user_docs = get_documents_from_file(user_file_path)
        user_content = "\n".join([d.text for d in user_docs])
        
        # 1. Retrieve relevant tax rules from common categories
        print("🧠 Consulting regulatory rules for categorization...")
        prompt = f"""
        Based on the following user financial data:
        ---
        {user_content[:4000]} # Truncate for prompt safety
        ---
        
        Please act as an Kenyan Tax Consultant. Your goal is to:
        1. Identify Income vs Expenditure.
        2. Categorize expenses into 'Business Deductible' vs 'Private' based on Kenyan Law.
        3. Identify potential VAT implications.
        
        Return a structured summary of your findings.
        """
        
        # Retrieve context from the Laws first
        context_docs = self.query_engine.query("What are the deductible business expenses and common income tax categories for Kenyan SMEs?")
        
        # Combine everything for the final reasoning
        final_prompt = f"""
        Regulatory Context: {context_docs}
        
        User Data: {user_content}
        
        Task: {prompt}
        """
        
        response = self.llm.complete(final_prompt)
        return response.text

    def generate_balance_sheet_draft(self, user_data_summary: str):
        """
        Uses the summarized user data to draft a balance sheet 
        following IFRS for SMEs standards.
        """
        prompt = f"""
        Using this financial summary:
        {user_data_summary}
        
        Draft a simple Balance Sheet following IFRS for SMEs (Kenyan standards).
        Include:
        - Assets (Current & Non-Current)
        - Liabilities
        - Equity (Profits/Losses)
        
        Ensure formatting is clean and professional.
        """
        response = self.llm.complete(prompt)
        return response.text

    def draft_tax_return(self, financial_summary: str):
        """
        Creates a draft KRA iTax Resident Individual/Company tax return.
        """
        prompt = f"""
        Using this financial summary:
        {financial_summary}
        
        Draft a KRA iTax return representation. 
        Focus on:
        - Total Taxable Income
        - Allowable Deductions
        - Tax Payable (Estimate using current Kenyan rates)
        """
        response = self.llm.complete(prompt)
        return response.text

if __name__ == "__main__":
    # Internal test check
    try:
        consultant = TaxConsultant()
        print("✅ Tax Consultant ready.")
    except Exception as e:
        print(f"❌ Could not initialize consultant: {e}")
