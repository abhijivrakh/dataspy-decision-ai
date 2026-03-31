# backend/app/schemas/chat.py

from pydantic import BaseModel
from typing import Dict, Any, List


class ChatQueryRequest(BaseModel):
    question: str
    analysis_context: Dict[str, Any]


class ChatQueryResponse(BaseModel):
    answer: str
    context_used: List[str]
    answer_source: str