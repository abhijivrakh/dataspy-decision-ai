from typing import Dict, Any, List
import pandas as pd


def safe_group_sum(df: pd.DataFrame, group_col: str, value_col: str, top_n: int = 5) -> List[Dict[str, Any]]:
    if group_col not in df.columns or value_col not in df.columns:
        return []

    grouped = (
        df.groupby(group_col, dropna=False)[value_col]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )

    return grouped.to_dict(orient="records")


def safe_group_count(df: pd.DataFrame, group_col: str, top_n: int = 10) -> List[Dict[str, Any]]:
    if group_col not in df.columns:
        return []

    grouped = (
        df[group_col]
        .astype(str)
        .value_counts(dropna=False)
        .head(top_n)
        .reset_index()
    )
    grouped.columns = [group_col, "count"]
    return grouped.to_dict(orient="records")


def safe_time_series_sum(df: pd.DataFrame, date_col: str, value_col: str) -> List[Dict[str, Any]]:
    if date_col not in df.columns or value_col not in df.columns:
        return []

    temp_df = df.copy()
    temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors="coerce")
    temp_df = temp_df.dropna(subset=[date_col])

    if temp_df.empty:
        return []

    grouped = (
        temp_df.groupby(temp_df[date_col].dt.date)[value_col]
        .sum()
        .reset_index()
    )
    grouped[date_col] = grouped[date_col].astype(str)

    return grouped.to_dict(orient="records")


def detect_delivery_delays(df: pd.DataFrame, shipment_col: str, delivery_col: str) -> Dict[str, Any]:
    if shipment_col not in df.columns or delivery_col not in df.columns:
        return {}

    temp_df = df.copy()
    temp_df[shipment_col] = pd.to_datetime(temp_df[shipment_col], errors="coerce")
    temp_df[delivery_col] = pd.to_datetime(temp_df[delivery_col], errors="coerce")
    temp_df = temp_df.dropna(subset=[shipment_col, delivery_col])

    if temp_df.empty:
        return {}

    temp_df["delivery_delay_days"] = (temp_df[delivery_col] - temp_df[shipment_col]).dt.days

    return {
        "average_delivery_days": round(float(temp_df["delivery_delay_days"].mean()), 2),
        "max_delivery_days": int(temp_df["delivery_delay_days"].max()),
        "min_delivery_days": int(temp_df["delivery_delay_days"].min())
    }


def generate_insights(
    df: pd.DataFrame,
    schema_suggestions: Dict[str, Any],
    capabilities: Dict[str, Any]
) -> Dict[str, Any]:
    insights = {
        "sales": {},
        "inventory": {},
        "logistics": {}
    }

    role_to_column = {}
    for role, data in schema_suggestions.items():
        column = data.get("column")
        confidence = data.get("confidence", 0)

        if column and confidence >= 0.6 and column in df.columns:
            role_to_column[role] = column

    # SALES INSIGHTS
    if capabilities.get("sales", {}).get("enabled"):
        date_col = role_to_column.get("date")
        product_col = role_to_column.get("product")
        region_col = role_to_column.get("region")
        revenue_col = role_to_column.get("revenue")
        quantity_col = role_to_column.get("quantity")

        insights["sales"] = {
            "top_products_by_revenue": safe_group_sum(df, product_col, revenue_col) if product_col and revenue_col else [],
            "top_regions_by_revenue": safe_group_sum(df, region_col, revenue_col) if region_col and revenue_col else [],
            "revenue_trend": safe_time_series_sum(df, date_col, revenue_col) if date_col and revenue_col else [],
            "quantity_trend": safe_time_series_sum(df, date_col, quantity_col) if date_col and quantity_col else []
        }

    # INVENTORY INSIGHTS
    if capabilities.get("inventory", {}).get("enabled"):
        product_col = role_to_column.get("product")
        stock_col = role_to_column.get("stock")
        reorder_col = role_to_column.get("reorder_level")

        low_stock_items = []
        if product_col and stock_col and reorder_col and all(col in df.columns for col in [product_col, stock_col, reorder_col]):
            temp_df = df.copy()
            temp_df = temp_df.dropna(subset=[stock_col, reorder_col])
            temp_df = temp_df[temp_df[stock_col] <= temp_df[reorder_col]]

            low_stock_items = temp_df[[product_col, stock_col, reorder_col]].head(10).to_dict(orient="records")

        insights["inventory"] = {
            "low_stock_items": low_stock_items
        }

    # LOGISTICS INSIGHTS
    if capabilities.get("logistics", {}).get("enabled"):
        status_col = role_to_column.get("status")
        shipment_col = role_to_column.get("shipment_date")
        delivery_col = role_to_column.get("delivery_date")
        region_col = role_to_column.get("region")

        insights["logistics"] = {
            "status_distribution": safe_group_count(df, status_col) if status_col else [],
            "region_distribution": safe_group_count(df, region_col) if region_col else [],
            "delivery_delay_summary": detect_delivery_delays(df, shipment_col, delivery_col) if shipment_col and delivery_col else {}
        }

    return insights