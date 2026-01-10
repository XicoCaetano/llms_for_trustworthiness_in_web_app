from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_LOG_SEVERITY_LEVEL"] = "ERROR"
from google.oauth2 import service_account
import json
from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions
from google.auth import load_credentials_from_file


class LLMVertexAI:
    def __init__(
        self,
        service_account_path: str,
        model_name,
        system_rules_file: str,
        location: str = "us-central1",
        temperature: float = 0.2,
    ):
        self.service_account_path = service_account_path
        self.model_name = model_name
        self.location = location
        self.temperature = temperature

        # Carregar credenciais
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Service account file not found: {service_account_path}")

        with open(service_account_path, "r") as f:
            data = json.load(f)
            project_id = data.get("project_id")
            if not project_id:
                raise ValueError("Key 'project_id' not found in service account file.")
        
        self.project_id = project_id
        
        credentials, project = load_credentials_from_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        self.project_id = project
        
        # Configurar cliente GenAI com credenciais
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
            http_options=HttpOptions(credentials=credentials)
        )

        # Carregar sistema de regras
        with open(f"./src/llms_and_prompts/{system_rules_file}.txt", "r", encoding="utf-8") as file:
            rules_full = file.read()
        self.system_rules = SystemMessagePromptTemplate.from_template(rules_full)


    def _generate(self, prompt_text: str) -> str:
        try:
            resp = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Why is the sky blue?",
                # See the SDK documentation at
                # https://googleapis.github.io/python-genai/genai.html#genai.types.GenerateContentConfig
                config=GenerateContentConfig(
                    temperature=0.2,
                    candidate_count=1,
                    response_mime_type="text/plain",
                    presence_penalty=0.0,
                    frequency_penalty=0.0,
                ),
            )
            return resp.text
        except Exception as e:
            print(f"❌ Error in GenAI generate_content: {e}")
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