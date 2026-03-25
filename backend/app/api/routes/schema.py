from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.engines.mapping.schema_mapper import detect_schema

router = APIRouter()


class SchemaDetectRequest(BaseModel):
    columns: List[str]


@router.post("/schema/detect")
def detect_schema_route(payload: SchemaDetectRequest):
    suggestions = detect_schema(payload.columns)
    return {
        "message": "Schema detection completed",
        "suggestions": suggestions
    }