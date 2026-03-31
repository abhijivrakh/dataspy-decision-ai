import json
from pathlib import Path
from typing import Any, Dict

from app.services.llm.llm_client import LLMClient
from app.services.llm.context_builder import AnalysisContextBuilder


class ExplanationService:
    def __init__(self) -> None:
        self.llm_client = LLMClient()
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).resolve().parents[2] / "prompts" / "analysis_explainer.txt"
        return prompt_path.read_text(encoding="utf-8")

    def explain_analysis(
        self,
        analysis_context: Dict[str, Any],
        audience: str = "management",
        tone: str = "executive",
    ) -> Dict[str, Any]:
        compact_context = AnalysisContextBuilder.build_explainer_context(analysis_context)

        user_prompt = f"""
Audience: {audience}
Tone: {tone}

Important:
- Explain only from the provided analysis context.
- Do not assume missing trends or business conditions.
- If evidence is partial, use cautious wording such as "based on available insights".
- If something is missing, say it is not explicitly available in the current analysis context.

Analysis Context:
{json.dumps(compact_context, indent=2, default=str)}

Generate the JSON response now.
""".strip()

        raw_output = self.llm_client.generate_text(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
        )

        parsed = self._safe_parse_json(raw_output)

        parsed["executive_summary"] = self._soften_overclaims(
            parsed.get("executive_summary", "")
        )
        parsed["business_explanation"] = self._soften_overclaims(
            parsed.get("business_explanation", "")
        )
        parsed["recommended_next_steps"] = [
            self._soften_overclaims(step)
            for step in parsed.get("recommended_next_steps", [])
        ]
        parsed["risk_summary"] = [
            self._soften_overclaims(risk)
            for risk in parsed.get("risk_summary", [])
        ]

        parsed["model_used"] = self.llm_client.model
        return parsed

    def _safe_parse_json(self, raw_output: str) -> Dict[str, Any]:
        try:
            cleaned = raw_output.strip()

            if cleaned.startswith("```json"):
                cleaned = cleaned.removeprefix("```json").strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.removeprefix("```").strip()
            if cleaned.endswith("```"):
                cleaned = cleaned.removesuffix("```").strip()

            parsed = json.loads(cleaned)

            return {
                "executive_summary": parsed.get("executive_summary", ""),
                "business_explanation": parsed.get("business_explanation", ""),
                "recommended_next_steps": parsed.get("recommended_next_steps", []),
                "risk_summary": parsed.get("risk_summary", []),
            }

        except Exception:
            return {
                "executive_summary": "Could not parse model output cleanly.",
                "business_explanation": raw_output,
                "recommended_next_steps": [],
                "risk_summary": [],
            }

    def _soften_overclaims(self, text: str) -> str:
        replacements = {
            "Revenue is growing": "Based on available insights, revenue appears to be performing positively",
            "Revenue is declining": "Based on available insights, revenue may be under pressure",
            "There is a strong upward trend": "The current analysis suggests a positive direction",
            "There is a strong downward trend": "The current analysis suggests a weaker direction",
            "showing an upward trend over time": "showing comparatively strong performance based on available insights",
            "showing a downward trend over time": "showing weaker performance based on available insights",
            "the revenue trend appears to be increasing": "some trend-related text suggests improving revenue performance, but this is not confirmed as deterministic output",
            "Revenue appears to be increasing": "Some trend-related text suggests improving revenue performance, but this is not confirmed as deterministic output",
        }

        cleaned = text
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        return cleaned