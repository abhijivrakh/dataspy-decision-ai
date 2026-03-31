from typing import Any, Dict


class AnalysisContextBuilder:
    @staticmethod
    def build_explainer_context(analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        schema = analysis_context.get("schema", {})
        capabilities = analysis_context.get("capabilities", {})
        profile = analysis_context.get("profile", {})
        insights = analysis_context.get("insights", {})
        forecast = analysis_context.get("forecast", {})
        decisions = analysis_context.get("decisions", {})
        decision_summary = analysis_context.get("decision_summary", "")

        safe_insights = AnalysisContextBuilder._sanitize_insights(insights)

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
            "trend_direction": forecast.get("trend_direction", "not_explicitly_available"),
            "trend_note": forecast.get(
                "trend_note",
                "Trend direction is not explicitly available unless provided by the deterministic forecast engine."
            ),
        }

        return {
            "schema": schema,
            "capabilities": capabilities,
            "profile": profile,
            "insights": safe_insights,
            "forecast": compact_forecast,
            "decisions": decisions,
            "decision_summary": decision_summary,
        }

    @staticmethod
    def _sanitize_insights(insights: Dict[str, Any]) -> Dict[str, Any]:
        safe_insights = {}

        for key, value in insights.items():
            lower_key = key.lower()

            if isinstance(value, (list, dict)):
                safe_insights[key] = value
                continue

            if "trend" in lower_key:
                safe_insights[key] = {
                    "value": value,
                    "trusted": False,
                    "note": "Trend text is available, but should be used cautiously unless explicitly validated by deterministic logic."
                }
                continue

            safe_insights[key] = value

        return safe_insights