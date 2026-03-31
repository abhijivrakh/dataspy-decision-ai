# backend/app/services/llm/chat_service.py

import json
from typing import Dict, Any, List

from app.services.llm.llm_client import LLMClient


SYSTEM_PROMPT = """
You are a Decision Intelligence Assistant.

STRICT RULES:
- Use ONLY the provided analysis context.
- Do NOT calculate new values.
- Do NOT assume anything that is not explicitly present.
- Do NOT hallucinate.
- If something is missing, say: "This is not available in the current analysis."
- Keep the answer business-friendly, concise, and clear.
- Base the answer only on analysis sections such as insights, forecast, decisions, capabilities, schema, and profile.
"""


def detect_context_used(question: str) -> List[str]:
    q = question.lower()
    used = []

    if any(word in q for word in ["product", "region", "revenue", "insight", "strongest", "top"]):
        used.append("insights")

    if any(word in q for word in ["forecast", "trend", "future", "prediction"]):
        used.append("forecast")

    if any(word in q for word in ["decision", "action", "priority", "urgent", "focus"]):
        used.append("decisions")

    if any(word in q for word in ["logistics", "sales", "inventory", "capability", "enabled", "disabled"]):
        used.append("capabilities")

    if any(word in q for word in ["schema", "column", "field", "mapped"]):
        used.append("schema")

    if any(word in q for word in ["profile", "quality", "missing", "null", "dataset", "rows", "columns"]):
        used.append("profile")

    return used if used else ["general"]


def soften_overclaims(text: str) -> str:
    replacements = {
        "definitely": "likely",
        "certainly": "based on the available analysis",
        "will surely": "may",
        "guaranteed": "likely",
    }

    cleaned = text
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    return cleaned


def apply_answer_policy(text: str, question: str) -> str:
    cleaned = text.strip()

    if not cleaned:
        return "This is not available in the current analysis."

    lower_text = cleaned.lower()

    if "not available in the current analysis" in lower_text:
        return "This is not available in the current analysis."

    unwanted_starts = [
        "based on the provided analysis context,",
        "based on the analysis context,",
        "according to the analysis context,",
        "from the analysis context,",
    ]

    for phrase in unwanted_starts:
        if lower_text.startswith(phrase):
            cleaned = cleaned[len(phrase):].strip(" ,.-")
            break

    cleaned = cleaned.replace("\n\n", "\n").strip()

    if len(cleaned) > 350:
        cleaned = cleaned[:350].rsplit(" ", 1)[0].strip() + "..."

    if "why" in question.lower() and not cleaned.endswith("."):
        cleaned += "."

    return cleaned


def build_chat_analysis_context(analysis_context: Dict[str, Any]) -> str:
    compact_context = {
        "schema": analysis_context.get("schema", {}),
        "capabilities": analysis_context.get("capabilities", {}),
        "profile": analysis_context.get("profile", {}),
        "insights": analysis_context.get("insights", {}),
        "forecast": analysis_context.get("forecast", {}),
        "decisions": analysis_context.get("decisions", {}),
    }

    return json.dumps(compact_context, indent=2, default=str)


def try_direct_answer(question: str, analysis_context: Dict[str, Any]):
    q = question.lower()

    insights = analysis_context.get("insights", {})
    forecast = analysis_context.get("forecast", {})
    decisions = analysis_context.get("decisions", {})
    capabilities = analysis_context.get("capabilities", {})
    profile = analysis_context.get("profile", {})
    schema = analysis_context.get("schema", {})

    if "strongest product" in q or ("product" in q and "strongest" in q):
        top_product = insights.get("top_product")
        if top_product:
            return {
                "answer": f"Based on the current analysis, {top_product} appears to be the strongest product.",
                "context_used": ["insights"]
            }

    if "top region" in q or ("region" in q and "top" in q):
        top_region = insights.get("top_region")
        if top_region:
            return {
                "answer": f"Based on the current analysis, {top_region} appears to be the top-performing region.",
                "context_used": ["insights"]
            }

    if "urgent decision" in q or "most urgent decision" in q or "priority" in q:
        priority = decisions.get("priority")
        if priority:
            return {
                "answer": f"The most urgent decision area is: {priority}",
                "context_used": ["decisions"]
            }

    if "recommended action" in q or "recommended actions" in q or "next step" in q or "next steps" in q:
        actions = decisions.get("recommended_actions", [])
        if actions:
            return {
                "answer": "The recommended next actions are: " + "; ".join(actions),
                "context_used": ["decisions"]
            }

    if "management focus" in q or "what should management focus on" in q:
        priority = decisions.get("priority")
        if priority:
            return {
                "answer": f"Management should focus on: {priority}",
                "context_used": ["decisions"]
            }

        actions = decisions.get("recommended_actions", [])
        if actions:
            return {
                "answer": "Management should focus on these actions: " + "; ".join(actions),
                "context_used": ["decisions"]
            }

    if "forecast" in q and "available" in q:
        available = forecast.get("available")
        if available is True:
            return {
                "answer": "Yes, forecast information is available in the current analysis.",
                "context_used": ["forecast"]
            }
        if available is False:
            return {
                "answer": "No, forecast information is not available in the current analysis.",
                "context_used": ["forecast"]
            }

    if "forecast trend" in q or ("trend" in q and "forecast" in q):
        trend = forecast.get("trend_direction")
        if trend and trend != "not_explicitly_available":
            return {
                "answer": f"The forecast trend direction is: {trend}.",
                "context_used": ["forecast"]
            }
        return {
            "answer": "This is not available in the current analysis.",
            "context_used": ["forecast"]
        }

    if "logistics" in q and ("enabled" in q or "disabled" in q):
        logistics_enabled = capabilities.get("logistics_enabled")
        if logistics_enabled is True:
            return {
                "answer": "Logistics capability is enabled in the current analysis.",
                "context_used": ["capabilities"]
            }
        if logistics_enabled is False:
            return {
                "answer": "Logistics capability is disabled in the current analysis.",
                "context_used": ["capabilities"]
            }

    if "sales" in q and ("enabled" in q or "disabled" in q):
        sales_enabled = capabilities.get("sales_enabled")
        if sales_enabled is True:
            return {
                "answer": "Sales capability is enabled in the current analysis.",
                "context_used": ["capabilities"]
            }
        if sales_enabled is False:
            return {
                "answer": "Sales capability is disabled in the current analysis.",
                "context_used": ["capabilities"]
            }

    if "inventory" in q and ("enabled" in q or "disabled" in q):
        inventory_enabled = capabilities.get("inventory_enabled")
        if inventory_enabled is True:
            return {
                "answer": "Inventory capability is enabled in the current analysis.",
                "context_used": ["capabilities"]
            }
        if inventory_enabled is False:
            return {
                "answer": "Inventory capability is disabled in the current analysis.",
                "context_used": ["capabilities"]
            }

    if "missing values" in q or "null values" in q or "data quality" in q:
        missing_values = profile.get("missing_values")
        if missing_values is not None:
            return {
                "answer": f"The dataset contains {missing_values} missing values.",
                "context_used": ["profile"]
            }

    if "row count" in q or "how many rows" in q:
        row_count = profile.get("row_count")
        if row_count is not None:
            return {
                "answer": f"The dataset contains {row_count} rows.",
                "context_used": ["profile"]
            }

    if "column count" in q or "how many columns" in q:
        column_count = profile.get("column_count")
        if column_count is not None:
            return {
                "answer": f"The dataset contains {column_count} columns.",
                "context_used": ["profile"]
            }

    if "dataset summary" in q or "summarize the dataset" in q:
        row_count = profile.get("row_count")
        column_count = profile.get("column_count")
        date_column = schema.get("date_column")
        target_column = schema.get("target_column")

        parts = []
        if row_count is not None:
            parts.append(f"{row_count} rows")
        if column_count is not None:
            parts.append(f"{column_count} columns")
        if date_column:
            parts.append(f"date column: {date_column}")
        if target_column:
            parts.append(f"target column: {target_column}")

        if parts:
            return {
                "answer": "The current dataset summary is: " + ", ".join(parts) + ".",
                "context_used": ["profile", "schema"]
            }

    if "main insight" in q or "top insight" in q or "key insight" in q:
        summary = insights.get("summary")
        if summary:
            return {
                "answer": summary,
                "context_used": ["insights"]
            }

    return None


def generate_chat_answer(question: str, analysis_context: Dict[str, Any]) -> Dict[str, Any]:

    direct_result = try_direct_answer(question, analysis_context)
    if direct_result:
        return {
            "answer": direct_result["answer"],
            "context_used": direct_result["context_used"],
            "answer_source": "Direct From Data"
        }

    compact_context = build_chat_analysis_context(analysis_context)

    user_prompt = f"""
User Question:
{question}

Analysis Context:
{compact_context}

Task:
Answer the user's question using only the analysis context above.

Answer policy:
- Give a direct answer first.
- Keep the answer concise and business-friendly.
- Use only information present in the context.
- Do not speculate.
- If the answer is missing, say exactly: "This is not available in the current analysis."
- Do not mention sections unless needed.
"""

    llm_client = LLMClient()
    llm_response = llm_client.generate_text(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

    final_answer = soften_overclaims(llm_response.strip())
    final_answer = apply_answer_policy(final_answer, question)

    return {
        "answer": final_answer,
        "context_used": detect_context_used(question),
        "answer_source": "Data Through LLM"
    }