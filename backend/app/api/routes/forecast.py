from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.engines.forecasting.forecast_engine import generate_forecast
import pandas as pd
import os
import json

router = APIRouter()


class ForecastRequest(BaseModel):
    saved_filename: str
    schema_suggestions: Dict[str, Any]
    target_role: str = "revenue"
    forecast_horizon: int = 7


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


@router.post("/forecast")
def forecast_route(payload: ForecastRequest):
    file_path = os.path.join("backend/app/uploads", payload.saved_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    try:
        df = load_dataframe(file_path)
        df.columns = [str(col).strip() for col in df.columns]

        forecast_result = generate_forecast(
            df=df,
            schema_suggestions=payload.schema_suggestions,
            target_role=payload.target_role,
            forecast_horizon=payload.forecast_horizon
        )

        return {
            "message": "Forecast generated successfully",
            "forecast": forecast_result
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")