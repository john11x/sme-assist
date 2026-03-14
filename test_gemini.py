from llama_index.llms.google_genai import GoogleGenAI
from config import settings
import os

print(f"Testing Gemini Key: {settings.GOOGLE_API_KEY[:10]}...")
try:
    llm = GoogleGenAI(api_key=settings.GOOGLE_API_KEY, model="models/gemini-flash-latest")
    response = llm.complete("Ping")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error with 'models/gemini-flash-latest': {e}")
