from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from src.config import API_KEY_PROF

code = """

"""

prompt_choices = {
        1: "prompt_1",
        2: "prompt_2",
        3: "prompt_3",
        4: "prompt_4",
        5: "prompt_5"
        }

llm_paths = {
    1: "gpt-3.5-turbo",
    2: "gpt-4o-mini",
    3: "gpt-4.1",
    4: "gpt-4.1-mini"
}

llm = 3
prompt = 4
practice = 2

for i in range(1):
    llm = ChatOpenAI(
        api_key=API_KEY_PROF,
        model_name=llm_paths[llm],
        temperature=0.2,
        model_kwargs={
            "top_p": 1,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
    )

    system_rules_file = f"./src/llms_and_prompts/system_roles/system_role_{prompt}/followed/a/p{practice}.txt"

    # Load system rules file exactly like your current code
    with open(system_rules_file, "r", encoding="utf-8") as file:
        rules_full = file.read()

    system_rules = SystemMessagePromptTemplate.from_template(rules_full)

    prompt_file = f"./src/llms_and_prompts/prompts/{llm_paths[llm]}/individual_practices_prompts/prompt_{prompt}/followed/a/p{practice}.txt"

    with open(prompt_file, "r", encoding="utf-8") as file:
        template = file.read()

    user_msg = HumanMessagePromptTemplate.from_template(template)
    prompt = ChatPromptTemplate.from_messages([system_rules, user_msg])

    filled_prompt = prompt.format(content=code)

    response = llm.invoke(filled_prompt)

    print("Response:", response.content)