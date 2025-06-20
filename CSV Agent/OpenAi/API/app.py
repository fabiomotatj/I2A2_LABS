# app.py

from fastapi import FastAPI, UploadFile, File, Form
from agent_core import load_csvs, user_question
import shutil
import os

app = FastAPI(title="CSV AI Agent API", description="API para perguntas sobre múltiplos CSVs usando LLM", version="1.0")

@app.post("/ask/")
async def ask(question: str = Form(...)):
    result = user_question(question)
    return result
