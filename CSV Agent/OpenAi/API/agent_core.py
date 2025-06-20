import os
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

apiKey = os.environ["open_ai_key"]

def load_csvs():
    folder_path = "../../202401_NFs"
    dataframes = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            df_name = os.path.splitext(filename)[0]
            try:
                df = pd.read_csv(os.path.join(folder_path, filename))
                dataframes[df_name] = df
                print(f"Carregado: {filename} com {len(df)} linhas.")
            except Exception as e:
                print(f"Erro ao carregar {filename}: {e}")
    return dataframes

dataframes = load_csvs()

def generate_context(dataframes):
    context = ""
    for name, df in dataframes.items():
        context += f"Dataset: {name}\n"
        context += f"Colunas: {', '.join(df.columns)}\n"
        context += f"Total de linhas: {len(df)}\n\n"
    return context

template = """
Você é um assistente Python que ajuda a responder perguntas sobre múltiplos datasets carregados como DataFrames Pandas.

Aqui está um resumo dos datasets disponíveis:

{dataset_context}

Pergunta do usuário:
{user_question}
"""

prompt_template = PromptTemplate.from_template(template)

llm = ChatOpenAI(model="gpt-4o",api_key=apiKey)

def ask_question(user_question):
    context = generate_context(dataframes)
    dataset_names = ", ".join(dataframes.keys())

    return prompt_template.format(
        dataset_context=context,
        user_question=user_question
    )

def user_question(question):
    pergunta = ask_question(question)

    response = llm.invoke(pergunta).content

    return response