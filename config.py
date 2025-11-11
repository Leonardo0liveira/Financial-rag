from langchain_openai import ChatOpenAI
import os


llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key="sua-chave-de-api-aqui"
)