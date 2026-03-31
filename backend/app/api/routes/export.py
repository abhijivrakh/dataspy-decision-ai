from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Dict, List
import pandas as pd
import os
import json
from uuid import uuid4

router = APIRouter()

EXPORT_DIR = "backend/app/exports"
os.makedirs(EXPORT_DIR, exist_ok=True)


class DecisionsExportRequest(BaseModel):
    decisions: List[Dict[str, Any]]


class ForecastExportRequest(BaseModel):
    forecast: Dict[str, Any]


@router.post("/export/decisions-csv")
async def export_decisions_csv(payload: DecisionsExportRequest):
    try:
        if not payload.decisions:
            raise HTTPException(status_code=400, detail="No decisions found to export")

        rows = []
        for idx, decision in enumerate(payload.decisions, start=1):
            rows.append({
                "sr_no": idx,
                "priority": decision.get("priority"),
                "action": decision.get("action"),
                "rationale": decision.get("rationale"),
                "decision_type": decision.get("decision_type"),
                "rank_order": decision.get("rank_order"),
                "supporting_evidence": json.dumps(
                    decision.get("supporting_evidence", {}),
                    ensure_ascii=False
                )
            })

        df = pd.DataFrame(rows)

        filename = f"decisions_{uuid4().hex[:8]}.csv"
        file_path = os.path.join(EXPORT_DIR, filename)
        df.to_csv(file_path, index=False)

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/csv"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision CSV export failed: {str(e)}")


@router.post("/export/forecast-csv")
async def export_forecast_csv(payload: ForecastExportRequest):
    try:
        forecast = payload.forecast
        historical_series = forecast.get("historical_series", [])
        forecast_series = forecast.get("forecast_series", [])

        if not historical_series and not forecast_series:
            raise HTTPException(status_code=400, detail="No forecast data found to export")

        rows = []

        for row in historical_series:
            rows.append({
                "series_type": "historical",
                "date": row.get("date"),
                "value": row.get("value")
            })

        for row in forecast_series:
            rows.append({
                "series_type": "forecast",
                "date": row.get("date"),
                "value": row.get("value")
            })

        df = pd.DataFrame(rows)

        filename = f"forecast_{uuid4().hex[:8]}.csv"
        file_path = os.path.join(EXPORT_DIR, filename)
        df.to_csv(file_path, index=False)

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/csv"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast CSV export failed: {str(e)}")