import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Literal
from dataclasses import asdict
import sys

# Add project root to path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.consultant import TaxConsultant
from backend.compliance import get_compliance_deadlines

app = FastAPI(title="SME-Assist API")

# Setup directories
UPLOAD_DIR = "data/user_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Static files for the frontend
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/frontend-assets", StaticFiles(directory="frontend"), name="frontend-assets")

# Global consultant instance
consultant = TaxConsultant()

class AnalysisResponse(BaseModel):
    filename: str
    summary: str
    balance_sheet: str
    tax_return: str

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: Literal["English", "Swahili", "Sheng", "French"] = "English"
    context: str = Field(default="", max_length=4000)

class ChatResponse(BaseModel):
    reply: str

@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

@app.get("/compliance/deadlines")
async def compliance_deadlines():
    return [
        {
            **asdict(deadline),
            "due_date": deadline.due_date.isoformat(),
        }
        for deadline in get_compliance_deadlines()
    ]

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_statement(file: UploadFile = File(...)):
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Run the RAG pipeline
        print(f"🚀 Analyzing {file.filename}...")
        summary = consultant.analyze_user_data(file_path)
        balance_sheet = consultant.generate_balance_sheet(summary)
        tax_return = consultant.draft_tax_return(summary, balance_sheet)
        
        return AnalysisResponse(
            filename=file.filename,
            summary=summary,
            balance_sheet=balance_sheet,
            tax_return=tax_return
        )
    except Exception as e:
        print(f"❌ Error analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_with_consultant(request: ChatRequest):
    language_instruction = f"Respond entirely in {request.language}."
    if request.language == "Sheng":
        language_instruction = (
            "Respond entirely in natural Kenyan Sheng, while keeping tax information accurate."
        )

    try:
        reply = consultant.answer_tax_question(
            request.message,
            language_instruction,
            request.context,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=502, detail="The tax assistant could not answer right now.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
