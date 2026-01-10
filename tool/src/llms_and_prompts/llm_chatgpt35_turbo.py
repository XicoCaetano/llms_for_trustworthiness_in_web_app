from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI

class LLMChatGPT:
    def __init__(self, api_key, model_name, system_rules_file,temperature=0.2):
        """
        Inicializa o modelo ChatGPT para integração com LLMs.
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model=self.model_name,  # keep model_name for drop-in parity
            temperature=self.temperature,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        
        with open(f"./src/llms_and_prompts/{system_rules_file}.txt", "r", encoding="utf-8") as file:
            rules_full = file.read()

        self.system_rules = SystemMessagePromptTemplate.from_template(rules_full)


    def response_template_1(self, template, context):

        user_msg = HumanMessagePromptTemplate.from_template(template)

        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        chain = prompt | self.llm
        response = chain.invoke({"content": context})
        return response.content
    
    def response_template_2(self, template, context):
        
        user_msg = HumanMessagePromptTemplate.from_template(template)

        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        chain = prompt | self.llm
        response = chain.invoke({"content": context})
        return response.content

    def response_template_3(self, template, context1, context2):

        user_msg = HumanMessagePromptTemplate.from_template(template)

        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        chain = prompt | self.llm
        response = chain.invoke({"content1": context1, "content2": context2})
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

    
    def response_template_individual_practices(self, template, content):
        user_msg = HumanMessagePromptTemplate.from_template(template)
        prompt = ChatPromptTemplate.from_messages([self.system_rules, user_msg])
        
        response = (prompt | self.llm).invoke({
            "content": content,
        })
        return response.content