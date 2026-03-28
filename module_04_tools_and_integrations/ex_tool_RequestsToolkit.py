# %%
from langchain_community.utilities.openapi import OpenAPISpec

# Загрузка из файла
spec = OpenAPISpec.from_file("data/taskmanager_openapi.yaml")

# Исследуем спецификацию
print(f"API: {spec.info.title}")
print(f"Base URL: {spec.servers[0].url}")
print(f"Endpoints: {list(spec.paths.keys())}")


# %%
# Для создания tools из OpenAPI используется RequestsToolkit:
from langchain_community.agent_toolkits.openapi.toolkit import RequestsToolkit
from langchain_community.utilities.requests import TextRequestsWrapper

toolkit = RequestsToolkit(
    requests_wrapper=TextRequestsWrapper(headers={}),
    allow_dangerous_requests=True,
)
tools = toolkit.get_tools()
for t in tools:
    print(f"  {t.name}: {t.description[:60]}")
