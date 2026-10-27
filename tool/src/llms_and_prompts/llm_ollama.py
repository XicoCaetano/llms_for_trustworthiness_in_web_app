import time
import requests
from src.config import OLLAMA_ENDPOINT, OLLAMA_USERNAME, OLLAMA_PASSWORD

REQUEST_TIMEOUT = 900   # seconds; a 31B model can take several minutes per answer
MAX_ATTEMPTS = 5        # retries on timeouts, dropped connections and 5xx errors


class LLMOllama:
    """
    Drop-in replacement for LLMChatGPT that calls a self-hosted Ollama server
    instead of the OpenAI API.  Exposes the same response_template_* interface
    so it can be used anywhere LLMChatGPT is accepted.

    Credentials are loaded from the .env file via src/config.py:
        OLLAMA_ENDPOINT, OLLAMA_USERNAME, OLLAMA_PASSWORD
    """

    def __init__(self, model_name: str, system_rules_file: str):
        self.model_name = model_name

        with open(
            f"./src/llms_and_prompts/{system_rules_file}.txt", "r", encoding="utf-8"
        ) as f:
            self.system_rules = f.read()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call(self, user_content: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.system_rules},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        auth = (
            requests.auth.HTTPBasicAuth(OLLAMA_USERNAME, OLLAMA_PASSWORD)
            if OLLAMA_USERNAME
            else None
        )
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = requests.post(
                    OLLAMA_ENDPOINT,
                    json=payload,
                    auth=auth,
                    timeout=REQUEST_TIMEOUT,
                )
                if response.status_code >= 500:
                    response.raise_for_status()
                break
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
            ) as e:
                if attempt == MAX_ATTEMPTS:
                    raise
                wait = 60 * attempt
                print(f"[!] Ollama request failed ({type(e).__name__}) — retrying in {wait}s "
                      f"(attempt {attempt}/{MAX_ATTEMPTS})")
                time.sleep(wait)

        response.raise_for_status()
        return response.json()["message"]["content"]

    @staticmethod
    def _render(template: str, **kwargs) -> str:
        return template.format(**kwargs)

    # ------------------------------------------------------------------
    # Public interface (mirrors LLMChatGPT exactly)
    # ------------------------------------------------------------------

    def response_template_1(self, template: str, context: str) -> str:
        return self._call(self._render(template, content=context))

    def response_template_2(self, template: str, context: str) -> str:
        return self._call(self._render(template, content=context))

    def response_template_3(self, template: str, context1: str, context2: str) -> str:
        return self._call(self._render(template, content1=context1, content2=context2))

    def response_template_4(self, template: str, context: str, list_called_methods) -> str:
        called = [m for m in (list_called_methods or []) if isinstance(m, str) and m.strip()]
        other_content = (
            "\n".join(f"- {m}" for m in called)
            if called
            else "Without called methods. Forget about this."
        )
        return self._call(self._render(template, content=context, other_content=other_content))

    def response_template_individual_practices(self, template: str, context: str) -> str:
        return self._call(self._render(template, content=context))
