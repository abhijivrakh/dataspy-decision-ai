# existing imports
from fastapi import APIRouter, HTTPException
from app.schemas.explain import ExplainAnalysisRequest, ExplainAnalysisResponse
from app.services.llm.explanation_service import ExplanationService

# NEW imports
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.llm.chat_service import generate_chat_answer

router = APIRouter(prefix="/api/chat", tags=["Chat / LLM"])

explanation_service = ExplanationService()

# Phase A
@router.post("/explain-analysis", response_model=ExplainAnalysisResponse)
def explain_analysis(payload: ExplainAnalysisRequest):
    try:
        result = explanation_service.explain_analysis(
            analysis_context=payload.analysis_context,
            audience=payload.audience or "management",
            tone=payload.tone or "executive",
        )
        return ExplainAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM explanation failed: {str(e)}")


# Phase B (NEW)
@router.post("/query", response_model=ChatQueryResponse)
def query_chat(payload: ChatQueryRequest):
    try:
        result = generate_chat_answer(
            question=payload.question,
            analysis_context=payload.analysis_context
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat query failed: {str(e)}")