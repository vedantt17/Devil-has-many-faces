# Written by V
from fastapi import APIRouter
from pydantic import BaseModel
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from pipeline.rag import answer

router = APIRouter()

class AskRequest(BaseModel):
    question: str
    corpus: str = None

@router.post("/")
def ask_question(request: AskRequest):
    result = answer(request.question, corpus=request.corpus)
    return result