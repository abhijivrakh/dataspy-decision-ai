from app.core.config import get_settings


class LLMClient:
    def __init__(self):
        self.settings = get_settings()
        self.provider = self.settings.llm_provider.lower()

        if self.provider == "groq":
            from groq import Groq

            if not self.settings.groq_api_key:
                raise ValueError("GROQ_API_KEY is missing in .env")

            self.client = Groq(api_key=self.settings.groq_api_key)
            self.model = self.settings.groq_model

        elif self.provider == "openai":
            from openai import OpenAI

            if not self.settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is missing in .env")

            self.client = OpenAI(api_key=self.settings.openai_api_key)
            self.model = self.settings.openai_model

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "groq":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content

        elif self.provider == "openai":
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.output_text