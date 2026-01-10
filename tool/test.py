from langchain_openai import ChatOpenAI
from src.config import OPENAI_API_KEY_PROF
llm = ChatOpenAI(model="gpt-4.1-mini", api_key=OPENAI_API_KEY_PROF)
print(llm.invoke("Hello"))