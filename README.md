# SME-Assist

SME-Assist is an AI-powered compliance co-pilot that helps Kenyan SMEs understand regulatory requirements from organizations such as the Kenya Revenue Authority, Kenya Bureau of Standards, and county licensing authorities.

## System Architecture

The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant regulatory text and generate grounded responses.

1. **Document Ingestion**: Parsing PDFs from regulatory bodies
2. **Chunking & Embeddings**: Creating vectors with LlamaIndex
3. **Vector Database**: Storing embeddings in ChromaDB
4. **Retrieval**: Finding relevant documents via similarity search
5. **Tax Consultant**: Processing user-uploaded financial data against regulatory rules
6. **LLM Generation**: Producing answers and reports (Balance Sheets, Tax Drafts) via Groq / Gemini
7. **Frontend**: Streamlit chat interface with citations and report downloads

## Environment Setup

1. Clone the repository: `git clone <repo-url>`
2. Navigate to project: `cd sme-assist`
3. Create a virtual environment: `python -m venv venv`
4. Activate it:
   - Mac/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
5. Set up environment variables:
   - Copy the template: `cp .env.example .env`
   - Open `.env` and fill in your local database credentials and API keys.
6. Install dependencies: `pip install -r requirements.txt`
7. Run the app: `streamlit run app/streamlit_app.py`

## Developer Flow

Use feature branches only:
- `feature/ingestion`
- `feature/retrieval`
- `feature/llm`
- `feature/frontend`
- `feature/devops`

1. `git checkout main`
2. `git pull origin main`
3. `git checkout -b feature/<your-feature>`
4. Work and commit changes
5. `git push origin feature/<your-feature>`
6. Create a Pull Request to main.
