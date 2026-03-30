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


def limit_records(data, limit=10):
    if isinstance(data, list):
        return data[:limit]
    return data


def build_dashboard_summary(
    file_summary: Dict[str, Any],
    capabilities: Dict[str, Any],
    profile: Dict[str, Any],
    insights: Dict[str, Any],
    forecast: Dict[str, Any],
    narratives: Dict[str, Any],
    decisions: Dict[str, Any]
) -> Dict[str, Any]:
    dataset_profile = profile.get("dataset_profile", {})
    decision_summary = decisions.get("decision_summary", {})
    sales_insights = insights.get("sales", {})
    forecast_summary = forecast if forecast else {}

    top_product = None
    top_products = sales_insights.get("top_products_by_revenue", [])
    if top_products:
        first = top_products[0]
        product_key = next((k for k in first.keys() if k.lower() not in ["total_amount", "revenue", "sales", "sales_amount"]), None)
        value_key = next((k for k in first.keys() if k.lower() in ["total_amount", "revenue", "sales", "sales_amount"]), None)
        if product_key and value_key:
            top_product = {
                "name": first[product_key],
                "value": first[value_key]
            }

    enabled_capabilities = [
        cap_name for cap_name, cap_data in capabilities.items()
        if cap_data.get("enabled")
    ]

    return {
        "dataset_name": file_summary.get("saved_filename"),
        "rows": file_summary.get("rows"),
        "columns": len(file_summary.get("columns", [])),
        "duplicate_rows": dataset_profile.get("duplicate_rows", 0),
        "enabled_capabilities": enabled_capabilities,
        "top_product": top_product,
        "forecast_average": forecast_summary.get("average_forecast_value"),
        "forecast_horizon": forecast_summary.get("forecast_horizon"),
        "total_decisions": decision_summary.get("total_decisions", 0),
        "high_priority_decisions": decision_summary.get("high_priority", 0),
        "headline_summary": narratives.get("sales_summary", "")
    }


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

        schema_suggestions = detect_schema(list(df.columns), df=df)
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
            profile=profile,
            insights=insights
        )

        decisions = generate_decisions(
            capabilities=capabilities,
            insights=insights,
            forecast={"forecast": forecast} if forecast else {"forecast": {}},
            schema_suggestions=schema_suggestions
        )

        compact_insights = {
            "sales": {
                "top_products_by_revenue": limit_records(
                    insights.get("sales", {}).get("top_products_by_revenue", []), 5
                ),
                "top_regions_by_revenue": limit_records(
                    insights.get("sales", {}).get("top_regions_by_revenue", []), 5
                ),
                "revenue_trend": limit_records(
                    insights.get("sales", {}).get("revenue_trend", []), 30
                ),
                "quantity_trend": limit_records(
                    insights.get("sales", {}).get("quantity_trend", []), 30
                )
            },
            "inventory": insights.get("inventory", {}),
            "logistics": insights.get("logistics", {})
        }

        compact_forecast = {}
        if forecast:
            compact_forecast = {
                "target_role": forecast.get("target_role"),
                "target_column": forecast.get("target_column"),
                "date_column": forecast.get("date_column"),
                "model_type": forecast.get("model_type"),
                "forecast_horizon": forecast.get("forecast_horizon"),
                "historical_points": forecast.get("historical_points"),
                "forecast_points": forecast.get("forecast_points"),
                "latest_actual_value": forecast.get("latest_actual_value"),
                "average_forecast_value": forecast.get("average_forecast_value"),
                "historical_series": limit_records(forecast.get("historical_series", []), 30),
                "forecast_series": forecast.get("forecast_series", [])
            }

        compact_decisions = {
            "decision_summary": decisions.get("decision_summary", {}),
            "top_decisions": (
                decisions.get("decisions", {}).get("sales", []) +
                decisions.get("decisions", {}).get("inventory", []) +
                decisions.get("decisions", {}).get("logistics", [])
            )[:5]
        }

        dashboard_summary = build_dashboard_summary(
            file_summary=file_summary,
            capabilities=capabilities,
            profile=profile,
            insights=insights,
            forecast=forecast,
            narratives=narratives,
            decisions=decisions
        )

        return {
            "message": "Dataset analyzed successfully",
            "dashboard_summary": dashboard_summary,
            "file_summary": file_summary,
            "schema_suggestions": schema_suggestions,
            "capabilities": capabilities,
            "profile": profile,
            "insights": compact_insights,
            "forecast": compact_forecast,
            "forecast_error": forecast_error,
            "narratives": narratives,
            "decisions": compact_decisions
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline analysis failed: {str(e)}")