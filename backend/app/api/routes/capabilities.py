from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.engines.understanding.capability_detector import detect_capabilities

router = APIRouter()


class CapabilityDetectionRequest(BaseModel):
    suggestions: Dict[str, Any]


@router.post("/capabilities/detect")
def detect_capabilities_route(payload: CapabilityDetectionRequest):
    capabilities = detect_capabilities(payload.suggestions)
    return {
        "message": "Capability detection completed",
        "capabilities": capabilities
    }