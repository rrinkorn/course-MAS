import os

import dotenv
import pandas as pd
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

llm = ChatOpenAI(
    base_url=os.getenv("POLZAAI_BASE_URL"),
    api_key=os.getenv("POLZAAI_API_KEY"),
    model="gpt-5-mini",
    temperature=0,
)

# Загружаем данные
df = pd.read_csv("data/sales_data.csv")

# Создаём специализированного агента для работы с DataFrame
agent = create_pandas_dataframe_agent(
    llm=llm,
    df=df,
    agent_type="tool-calling",
    verbose=True,
    allow_dangerous_code=True,  # Требуется явное подтверждение
)

# Теперь можно задавать вопросы на естественном языке
result = agent.invoke("Какой продукт принёс наибольшую выручку в Q3?")
