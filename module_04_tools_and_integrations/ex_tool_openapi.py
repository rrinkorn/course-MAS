# %%
import os

import dotenv
import yaml
from langchain_community.agent_toolkits.openapi.planner import create_openapi_agent
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_community.utilities.requests import TextRequestsWrapper
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

llm = ChatOpenAI(
    base_url=os.getenv("POLZAAI_BASE_URL"),
    api_key=os.getenv("POLZAAI_API_KEY"),
    model="gpt-5-mini",
    temperature=0,
)

# Загружаем и преобразуем спецификацию
with open("data/taskmanager_openapi.yaml") as f:
    raw_spec = yaml.safe_load(f)
spec = reduce_openapi_spec(raw_spec)

# Создаём обёртку для HTTP-запросов с авторизацией
API_TOKEN = os.getenv("TASKMANAGER_API_TOKEN", "demo-token")
requests_wrapper = TextRequestsWrapper(headers={"Authorization": f"Bearer {API_TOKEN}"})

# Создаём агента для работы с OpenAPI
agent = create_openapi_agent(
    api_spec=spec,
    requests_wrapper=requests_wrapper,
    llm=llm,
    allow_dangerous_requests=True,  # Требуется для POST/PUT/DELETE
    verbose=True,
)

print("OpenAPI agent создан успешно")
print(f"Servers: {spec.servers}")
print(f"Endpoints: {[ep[0] for ep in spec.endpoints]}")
