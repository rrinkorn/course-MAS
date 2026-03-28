# %%
from openai import OpenAI
import dotenv
import os

dotenv.load_dotenv()

client = OpenAI(
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# %%
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Получить текущую погоду в указанном городе",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Город, например 'Москва' или 'Paris'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Единица измерения температуры"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

messages = [
    {"role": "user", "content": "Какая сейчас погода в Токио?"}
]

response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=messages,
    tools=tools,
    tool_choice="auto",  # Модель сама решает, вызывать ли функцию
    response_format="json_object"
)
# %%
print(response)