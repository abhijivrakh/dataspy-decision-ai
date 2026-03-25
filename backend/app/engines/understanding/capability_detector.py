from typing import Dict, Any


CAPABILITY_RULES = {
    "sales": {
        "roles": ["date", "product", "revenue", "quantity", "region"],
        "min_required": 3,
        "must_have": []
    },
    "inventory": {
        "roles": ["product", "stock", "reorder_level", "lead_time", "region"],
        "min_required": 2,
        "must_have": ["stock"]
    },
    "logistics": {
        "roles": ["order_id", "shipment_date", "delivery_date", "status", "region"],
        "min_required": 3,
        "must_have": ["order_id"]
    }
}


def detect_capabilities(
    schema_suggestions: Dict[str, Any],
    confidence_threshold: float = 0.6
) -> Dict[str, Any]:
    detected = {}

    for capability, config in CAPABILITY_RULES.items():
        roles = config["roles"]
        min_required = config["min_required"]
        must_have = config["must_have"]

        matched_roles = []

        for role in roles:
            role_data = schema_suggestions.get(role, {})
            confidence = role_data.get("confidence", 0)
            column = role_data.get("column")

            if column is not None and confidence >= confidence_threshold:
                matched_roles.append(role)

        must_have_ok = all(required_role in matched_roles for required_role in must_have)
        coverage = len(matched_roles) / len(roles) if roles else 0.0
        enabled = must_have_ok and len(matched_roles) >= min_required

        detected[capability] = {
            "enabled": enabled,
            "coverage": round(coverage, 2),
            "matched_roles": matched_roles,
            "missing_roles": [role for role in roles if role not in matched_roles]
        }

    return detected