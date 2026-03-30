from typing import Dict, List, Any
import re
import pandas as pd


ROLE_SYNONYMS = {
    "date": ["date", "order_date", "sales_date", "transaction_date", "day", "invoice_date"],
    "product": ["product", "product_name", "item", "sku", "item_name"],
    "region": ["region", "location", "zone", "area", "territory", "city", "state", "country"],
    "revenue": ["revenue", "sales", "sales_amount", "amount", "income", "total_amount", "net_total", "gross_total"],
    "quantity": ["quantity", "qty", "units", "unit_sold", "volume"],
    "stock": ["stock", "inventory", "inventory_level", "available_stock"],
    "reorder_level": ["reorder_level", "reorder_point", "min_stock"],
    "lead_time": ["lead_time", "delivery_lead_time", "supplier_lead_time", "turnaround_time"],
    "order_id": ["order_id", "order_number", "invoice_id", "transaction_id", "po_number"],
    "shipment_date": ["shipment_date", "ship_date", "dispatch_date", "shipped_date"],
    "delivery_date": ["delivery_date", "delivered_date", "arrival_date", "received_date"],
    "status": ["status", "delivery_status", "shipment_status", "order_status", "payment_status"]
}


STRICT_ROLES = {"status", "shipment_date", "lead_time"}


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def similarity_score(column_name: str, candidate: str) -> float:
    col = normalize_text(column_name)
    cand = normalize_text(candidate)

    if col == cand:
        return 1.0

    if cand in col or col in cand:
        return 0.85

    col_tokens = set(col.split("_"))
    cand_tokens = set(cand.split("_"))

    if not col_tokens or not cand_tokens:
        return 0.0

    overlap = len(col_tokens.intersection(cand_tokens))
    if overlap > 0:
        return 0.65 * (overlap / max(len(cand_tokens), 1))

    return 0.0


def looks_like_datetime(series: pd.Series) -> bool:
    try:
        converted = pd.to_datetime(series, errors="coerce")
        valid_ratio = converted.notna().mean()
        return valid_ratio >= 0.6
    except Exception:
        return False


def looks_like_numeric(series: pd.Series) -> bool:
    try:
        converted = pd.to_numeric(series, errors="coerce")
        valid_ratio = converted.notna().mean()
        return valid_ratio >= 0.8
    except Exception:
        return False


def looks_like_status(series: pd.Series) -> bool:
    try:
        sample = series.dropna().astype(str).str.lower().head(20).tolist()
        if not sample:
            return False
        status_keywords = {"pending", "delivered", "shipped", "cancelled", "processing", "completed", "failed", "returned"}
        score = sum(1 for val in sample if val in status_keywords or any(k in val for k in status_keywords))
        return score >= max(1, len(sample) // 4)
    except Exception:
        return False


def detect_schema(columns: List[str], df: pd.DataFrame | None = None) -> Dict[str, Any]:
    suggestions = {}

    for role, synonyms in ROLE_SYNONYMS.items():
        best_column = None
        best_score = 0.0

        for col in columns:
            base_score = 0.0

            for synonym in synonyms:
                score = similarity_score(col, synonym)
                if score > base_score:
                    base_score = score

            heuristic_bonus = 0.0
            penalty = 0.0

            if df is not None and col in df.columns:
                series = df[col]

                if role in {"date", "shipment_date", "delivery_date"}:
                    if looks_like_datetime(series):
                        heuristic_bonus += 0.15
                    elif role in STRICT_ROLES:
                        penalty += 0.25

                if role in {"revenue", "quantity", "stock", "reorder_level", "lead_time"}:
                    if looks_like_numeric(series):
                        heuristic_bonus += 0.12
                    elif role in STRICT_ROLES:
                        penalty += 0.25

                if role == "status":
                    if looks_like_status(series):
                        heuristic_bonus += 0.2
                    else:
                        penalty += 0.35

                if role == "lead_time":
                    if looks_like_datetime(series):
                        penalty += 0.4

                if role == "status" and looks_like_numeric(series):
                    penalty += 0.4

                if role == "order_id" and looks_like_numeric(series):
                    heuristic_bonus += 0.1

                if role == "region":
                    normalized = normalize_text(col)
                    if normalized in {"city", "state", "country"}:
                        heuristic_bonus += 0.2

            final_score = max(0.0, min(1.0, base_score + heuristic_bonus - penalty))

            if final_score > best_score:
                best_score = final_score
                best_column = col

        minimum_confidence = 0.5 if role in STRICT_ROLES else 0.3

        if best_score < minimum_confidence:
            suggestions[role] = {
                "column": None,
                "confidence": 0.0
            }
        else:
            suggestions[role] = {
                "column": best_column,
                "confidence": round(best_score, 2)
            }

    return suggestions