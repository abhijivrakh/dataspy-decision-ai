from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import pandas as pd
import os
import json

from app.engines.mapping.schema_mapper import detect_schema
from app.engines.understanding.capability_detector import detect_capabilities
from app.engines.understanding.profiler import profile_dataframe
from app.engines.insights.insight_engine import generate_insights
from app.engines.insights.narrative_engine import generate_narrative
from app.engines.forecasting.forecast_engine import generate_forecast
from app.engines.decisions.decision_engine import generate_decisions

router = APIRouter()


class AnalyzeRequest(BaseModel):
    saved_filename: str
    forecast_target_role: Optional[str] = "revenue"
    forecast_horizon: Optional[int] = 7


def load_dataframe(file_path: str) -> pd.DataFrame:
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".csv":
        return pd.read_csv(file_path)
    elif extension in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)
    elif extension == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data)
    else:
        raise ValueError("Unsupported file format")


@router.post("/analyze")
def analyze_dataset(payload: AnalyzeRequest):
    file_path = os.path.join("backend/app/uploads", payload.saved_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    try:
        df = load_dataframe(file_path)
        df.columns = [str(col).strip() for col in df.columns]

        file_summary = {
            "saved_filename": payload.saved_filename,
            "rows": int(df.shape[0]),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "preview": df.head(5).fillna("").to_dict(orient="records")
        }

        schema_suggestions = detect_schema(list(df.columns))
        capabilities = detect_capabilities(schema_suggestions)
        profile = profile_dataframe(df)
        insights = generate_insights(
            df=df,
            schema_suggestions=schema_suggestions,
            capabilities=capabilities
        )

        forecast = {}
        forecast_error = None

        try:
            forecast = generate_forecast(
                df=df,
                schema_suggestions=schema_suggestions,
                target_role=payload.forecast_target_role,
                forecast_horizon=payload.forecast_horizon
            )
        except Exception as fe:
            forecast_error = str(fe)

        narratives = generate_narrative(
            schema_suggestions=schema_suggestions,
            capabilities=capabilities,
            profile=profile.get("dataset_profile", {}) and profile,
            insights=insights
        )

        decisions = generate_decisions(
            capabilities=capabilities,
            insights=insights,
            forecast={"forecast": forecast} if forecast else {"forecast": {}},
            schema_suggestions=schema_suggestions
        )

        return {
            "message": "Dataset analyzed successfully",
            "file_summary": file_summary,
            "schema_suggestions": schema_suggestions,
            "capabilities": capabilities,
            "profile": profile,
            "insights": insights,
            "forecast": forecast,
            "forecast_error": forecast_error,
            "narratives": narratives,
            "decisions": decisions
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline analysis failed: {str(e)}")