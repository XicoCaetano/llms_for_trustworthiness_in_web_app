from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI

class LLMChatGPT41Mini:
    def __init__(
        self,
        api_key,
        system_rules_file: str,
    ):
        self.api_key = api_key
        self.model_name = "gpt-4.1-mini"
        self.temperature = 0.2

        # Construct model_kwargs conservatively to match your current style
        model_kwargs = {
            "top_p": 1,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }

        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model=self.model_name,  # keep model_name for drop-in parity
            temperature=self.temperature,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        # Load system rules file exactly like your current code
        with open(f"./src/llms_and_prompts/{system_rules_file}.txt", "r", encoding="utf-8") as file:
            rules_full = file.read()
        self.system_rules = SystemMessagePromptTemplate.from_template(rules_full)

    # ---- Response templates (kept identical for drop-in compatibility) ----
    def response_template_1(self, template: str, context: str):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        response = (prompt | self.llm).invoke({"content": context})
        return response.content

    def response_template_2(self, template: str, context: str):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        response = (prompt | self.llm).invoke({"content": context})
        return response.content

    def response_template_3(self, template: str, context1: str, context2: str):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        response = (prompt | self.llm).invoke({"content1": context1, "content2": context2})
        return response.content

    def response_template_4(self, template, context, list_called_methods):
        # Lista de métodos chamados
        called = [m for m in (list_called_methods or []) if isinstance(m, str) and m.strip()]
        other_content = "\n".join(f"- {m}" for m in called) if called else "Without called methods. Forget about this."
        
        user_msg = HumanMessagePromptTemplate.from_template(template)

        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
    
        filled = prompt.format(content=context, other_content=other_content)

        response = self.llm.invoke(filled)
        return response.content
    
    def response_template_individual_practices(self, template, context):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])

        filled_prompt = prompt.format(content=context)

        response = self.llm.invoke(filled_prompt)
        return response.content
