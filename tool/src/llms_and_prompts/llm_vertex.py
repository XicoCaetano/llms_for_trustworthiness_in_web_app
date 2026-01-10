from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
import warnings
import os
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_LOG_SEVERITY_LEVEL"] = "ERROR"
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.oauth2 import service_account
import json


class LLMVertexAI:
    def __init__(
        self,
        service_account_path: str,
        model_name,
        system_rules_file: str,
        location: str = "us-central1",
        temperature: float = 0.2,
        max_output_tokens: int = 8192,
    ):
        self.service_account_path = service_account_path
        self.model_name = model_name
        self.location = location
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

        # --- Load credentials and project ---
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Service account file not found: {service_account_path}")

        with open(service_account_path, "r") as f:
            data = json.load(f)
            self.project_id = data.get("project_id")
            if not self.project_id:
                raise ValueError("Key 'project_id' not found in service account file.")

        self.credentials = service_account.Credentials.from_service_account_file(service_account_path)

        # --- Init Vertex AI ---
        vertexai.init(project=self.project_id, location=self.location, credentials=self.credentials)

        # --- Load the model ---
        print(f"🔹 Loading Vertex AI model: {self.model_name}")
        self.model = GenerativeModel(self.model_name)

        # --- Load the system rules file ---
        with open(f"./src/llms_and_prompts/{system_rules_file}.txt", "r", encoding="utf-8") as file:
            rules_full = file.read()

        self.system_rules = SystemMessagePromptTemplate.from_template(rules_full)

    # --- Internal utility to generate text ---
    def _generate(self, prompt_text: str) -> str:
        try:
            generation_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
            )
            response = self.model.generate_content(
                prompt_text,
                generation_config=generation_config,
            )
            print(response)
            if response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
            else:
                print("⚠️ Empty response (possibly filtered).")
                return ""
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return ""

    # ---- Response templates (identical signatures to GPT version) ----
    def response_template_1(self, template: str, context: str):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        filled = prompt.format(content=context)
        return self._generate(filled)

    def response_template_2(self, template: str, context: str):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        filled = prompt.format(content=context)
        return self._generate(filled)

    def response_template_3(self, template: str, context1: str, context2: str):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        filled = prompt.format(content1=context1, content2=context2)
        return self._generate(filled)

    def response_template_4(self, template, context, list_called_methods):
        called = [m for m in (list_called_methods or []) if isinstance(m, str) and m.strip()]
        other_content = "\n".join(f"- {m}" for m in called) if called else "Without called methods. Forget about this."

        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        filled = prompt.format(content=context, other_content=other_content)
        return self._generate(filled)

    def response_template_individual_practices(self, template, context):
        # Texto adicional de reforço
        strict_instruction = (
            "\n\n⚠️ If you include anything other than \"1. Yes;\" or \"1. No;\", "
            "your answer will be considered invalid.\n"
            "Do not explain or add reasoning. Output exactly one line only."
        )

        # Adicionar o reforço diretamente ao template
        user_msg = HumanMessagePromptTemplate.from_template(template + strict_instruction)

        # Construir prompt como antes
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        filled = prompt.format(content=context)

        return self._generate(filled)
