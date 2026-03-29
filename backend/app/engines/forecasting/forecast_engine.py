from typing import Dict, Any, List
import pandas as pd


def prepare_time_series(
    df: pd.DataFrame,
    date_col: str,
    target_col: str
) -> pd.DataFrame:
    temp_df = df.copy()

    temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors="coerce")
    temp_df[target_col] = pd.to_numeric(temp_df[target_col], errors="coerce")

    temp_df = temp_df.dropna(subset=[date_col, target_col])

    if temp_df.empty:
        return pd.DataFrame(columns=["ds", "y"])

    ts_df = (
        temp_df.groupby(temp_df[date_col].dt.date)[target_col]
        .sum()
        .reset_index()
    )

    ts_df.columns = ["ds", "y"]
    ts_df["ds"] = pd.to_datetime(ts_df["ds"])
    ts_df = ts_df.sort_values("ds").reset_index(drop=True)

    return ts_df


def moving_average_forecast(
    ts_df: pd.DataFrame,
    horizon: int = 7,
    window: int = 7
) -> pd.DataFrame:
    if ts_df.empty:
        return pd.DataFrame(columns=["ds", "yhat"])

    working_values = ts_df["y"].tolist()
    last_date = ts_df["ds"].max()

    forecasts = []

    effective_window = min(window, len(working_values))
    if effective_window == 0:
        return pd.DataFrame(columns=["ds", "yhat"])

    for step in range(1, horizon + 1):
        forecast_value = sum(working_values[-effective_window:]) / effective_window
        forecast_date = last_date + pd.Timedelta(days=step)

        forecasts.append({
            "ds": forecast_date,
            "yhat": round(float(forecast_value), 2)
        })

        working_values.append(forecast_value)

    return pd.DataFrame(forecasts)


def generate_forecast(
    df: pd.DataFrame,
    schema_suggestions: Dict[str, Any],
    target_role: str = "revenue",
    forecast_horizon: int = 7
) -> Dict[str, Any]:
    date_role = schema_suggestions.get("date", {})
    target_role_data = schema_suggestions.get(target_role, {})

    date_col = date_role.get("column")
    date_confidence = date_role.get("confidence", 0)

    target_col = target_role_data.get("column")
    target_confidence = target_role_data.get("confidence", 0)

    if not date_col or date_confidence < 0.6:
        raise ValueError("No reliable date column available for forecasting")

    if not target_col or target_confidence < 0.6:
        raise ValueError(f"No reliable target column mapped for role: {target_role}")

    if date_col not in df.columns or target_col not in df.columns:
        raise ValueError("Mapped columns not found in dataset")

    ts_df = prepare_time_series(df, date_col, target_col)

    if len(ts_df) < 3:
        raise ValueError("Not enough time series data points for forecasting")

    forecast_df = moving_average_forecast(
        ts_df=ts_df,
        horizon=forecast_horizon,
        window=7
    )

    historical_series = [
        {
            "ds": row["ds"].strftime("%Y-%m-%d"),
            "y": round(float(row["y"]), 2)
        }
        for _, row in ts_df.iterrows()
    ]

    forecast_series = [
        {
            "ds": row["ds"].strftime("%Y-%m-%d"),
            "yhat": round(float(row["yhat"]), 2)
        }
        for _, row in forecast_df.iterrows()
    ]

    latest_actual = historical_series[-1]["y"] if historical_series else None
    avg_forecast = round(float(forecast_df["yhat"].mean()), 2) if not forecast_df.empty else None

    return {
        "target_role": target_role,
        "target_column": target_col,
        "date_column": date_col,
        "model_type": "moving_average_baseline",
        "forecast_horizon": forecast_horizon,
        "historical_points": len(historical_series),
        "forecast_points": len(forecast_series),
        "latest_actual_value": latest_actual,
        "average_forecast_value": avg_forecast,
        "historical_series": historical_series,
        "forecast_series": forecast_series
    }