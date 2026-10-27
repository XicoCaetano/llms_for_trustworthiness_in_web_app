import time
import requests
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from src.config import OLLAMA_ENDPOINT, OLLAMA_USERNAME, OLLAMA_PASSWORD

# Network robustness only: these never change what the model receives.
REQUEST_TIMEOUT = 900   # seconds per request
MAX_ATTEMPTS = 5        # retries on timeouts, dropped connections and 5xx errors

# Context window. Ollama silently truncates prompts longer than num_ctx,
# so it is set well above the largest prompt in the experiment (~8k tokens).
NUM_CTX = 16384

# Disable reasoning/"thinking" (the GPT models in the original experiment did not reason)
THINK = False


class LLMOllama:
    """
    Ollama counterpart of LLMChatGPT (llm_gpt.py).

    To keep the experiment identical to the GPT runs, the prompts are built
    with exactly the same LangChain templates and sent with the same message
    structure as LLMChatGPT:
      - response_template_1/2/3 -> separate system + user messages
        (LLMChatGPT uses the `prompt | llm` chain)
      - response_template_4 / response_template_individual_practices ->
        a single user message containing "System: ...\\nHuman: ..."
        (LLMChatGPT calls prompt.format(...) and invokes the LLM with that string)

    Sampling matches the ChatOpenAI settings in LLMChatGPT (temperature=0.2,
    top_p=1, no penalties); Ollama-only samplers are set to neutral values.
    """

    def __init__(self, model_name, system_rules_file: str):
        self.model_name = model_name
        self.temperature = 0.2

        # Load system rules file exactly like LLMChatGPT
        with open(f"./src/llms_and_prompts/{system_rules_file}.txt", "r", encoding="utf-8") as file:
            rules_full = file.read()
        self.system_rules = SystemMessagePromptTemplate.from_template(rules_full)

    # ---- Ollama call ----
    def _chat(self, messages):
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "think": THINK,
            "options": {
                # Same as ChatOpenAI in LLMChatGPT
                "temperature": self.temperature,
                "top_p": 1,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                # Ollama-specific samplers disabled (OpenAI has no equivalent)
                "top_k": 0,
                "min_p": 0.0,
                "repeat_penalty": 1.0,
                "num_ctx": NUM_CTX,
            },
        }
        auth = (
            requests.auth.HTTPBasicAuth(OLLAMA_USERNAME, OLLAMA_PASSWORD)
            if OLLAMA_USERNAME
            else None
        )

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = requests.post(OLLAMA_ENDPOINT, json=payload, auth=auth, timeout=REQUEST_TIMEOUT)
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

        # Models without thinking support may reject the "think" field: retry once without it
        if response.status_code == 400 and "think" in response.text.lower() and "think" in payload:
            payload.pop("think")
            response = requests.post(OLLAMA_ENDPOINT, json=payload, auth=auth, timeout=REQUEST_TIMEOUT)

        response.raise_for_status()
        data = response.json()

        if data.get("message", {}).get("thinking"):
            print("[!] WARNING: the model returned reasoning ('thinking') despite think=false")

        prompt_tokens = data.get("prompt_eval_count") or 0
        if prompt_tokens >= NUM_CTX * 0.95:
            print(f"[!] WARNING: prompt used {prompt_tokens} tokens of num_ctx={NUM_CTX} — it may have been truncated")

        return data["message"]["content"]

    def _invoke_chain(self, prompt, **kwargs):
        # Equivalent of (prompt | ChatOpenAI).invoke(kwargs): one message per role
        roles = {"system": "system", "human": "user", "ai": "assistant"}
        messages = [{"role": roles[m.type], "content": m.content} for m in prompt.format_messages(**kwargs)]
        return self._chat(messages)

    def _invoke_string(self, text):
        # Equivalent of ChatOpenAI.invoke(str): the string becomes a single user message
        return self._chat([{"role": "user", "content": text}])

    # ---- Response templates (same as LLMChatGPT) ----
    def response_template_1(self, template: str, context: str):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        return self._invoke_chain(prompt, content=context)

    def response_template_2(self, template: str, context: str):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        return self._invoke_chain(prompt, content=context)

    def response_template_3(self, template: str, context1: str, context2: str):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        return self._invoke_chain(prompt, content1=context1, content2=context2)

    def response_template_4(self, template, context, list_called_methods):
        # Lista de métodos chamados
        called = [m for m in (list_called_methods or []) if isinstance(m, str) and m.strip()]
        other_content = "\n".join(f"- {m}" for m in called) if called else "Without called methods. Forget about this."

        user_msg = HumanMessagePromptTemplate.from_template(template)

        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])

        filled = prompt.format(content=context, other_content=other_content)

        return self._invoke_string(filled)

    def response_template_individual_practices(self, template, context):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])

        filled_prompt = prompt.format(content=context)

        return self._invoke_string(filled_prompt)
