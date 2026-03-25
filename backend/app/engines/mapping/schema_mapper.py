from typing import Dict, List, Any
import re


ROLE_SYNONYMS = {
    "date": ["date", "order_date", "sales_date", "transaction_date", "day"],
    "product": ["product", "product_name", "item", "sku", "item_name"],
    "region": ["region", "location", "zone", "area", "territory"],
    "revenue": ["revenue", "sales", "sales_amount", "amount", "income"],
    "quantity": ["quantity", "qty", "units", "unit_sold", "volume"],
    "stock": ["stock", "inventory", "inventory_level", "available_stock"],
    "reorder_level": ["reorder_level", "reorder_point", "min_stock"],
    "lead_time": ["lead_time", "delivery_lead_time", "supplier_lead_time"],
    "order_id": ["order_id", "order_number", "invoice_id", "transaction_id"],
    "shipment_date": ["shipment_date", "ship_date", "dispatch_date"],
    "delivery_date": ["delivery_date", "delivered_date", "arrival_date"],
    "status": ["status", "delivery_status", "shipment_status", "order_status"]
}


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def similarity_score(column_name: str, candidate: str) -> float:
    """
    Lightweight rule-based similarity:
    - exact match = 1.0
    - contains match = 0.85
    - partial token overlap = 0.65
    - otherwise = 0
    """
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


def detect_schema(columns: List[str]) -> Dict[str, Any]:
    suggestions = {}

    for role, synonyms in ROLE_SYNONYMS.items():
        best_column = None
        best_score = 0.0

        for col in columns:
            for synonym in synonyms:
                score = similarity_score(col, synonym)
                if score > best_score:
                    best_score = score
                    best_column = col

        suggestions[role] = {
            "column": best_column,
            "confidence": round(best_score, 2)
        }

    return suggestions