from fastapi import FastAPI
from pydantic import BaseModel
from src.rag import ask

app = FastAPI(title="Compliance Evidence Copilot")

class AskReq(BaseModel):
    question: str

@app.post("/ask")
def ask_endpoint(req: AskReq):
    return ask(req.question)
