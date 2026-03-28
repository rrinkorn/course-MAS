# %%
"""
1. Запусти сервер

uv run python ex_tool_mcp_server.py
Сервер запустится на http://127.0.0.1:8000.

2. Запусти MCP Inspector (в другом терминале)

npx @modelcontextprotocol/inspector
Это откроет веб-интерфейс инспектора (обычно на http://localhost:6274).

3. Подключись к серверу в Inspector
Transport Type: выбери Streamable HTTP
URL: введи http://127.0.0.1:8000/mcp
Нажми Connect
4. Тестируй в Inspector
- Tools:    List Tools → выбери greet или add → Run Tool
- Resources: List Resources → выбери info://about или data://users/1 → Read Resource
- Prompts:  List Prompts → выбери summarize или review_code → Get Prompt
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server", host="127.0.0.1", port=8000)


# --- Tools ---

@mcp.tool()
def greet(name: str) -> str:
    """Приветствует пользователя по имени"""
    return f"Привет, {name}!"


@mcp.tool()
def add(a: float, b: float) -> float:
    """Складывает два числа"""
    return a + b


# --- Resources ---

@mcp.resource("info://about")
def about() -> str:
    """Информация о сервере"""
    return "Это демо MCP-сервер с tools, resources и prompts."


@mcp.resource("data://users/{user_id}")
def get_user(user_id: str) -> str:
    """Возвращает данные пользователя по ID"""
    users = {
        "1": "Алиса (инженер)",
        "2": "Боб (дизайнер)",
        "3": "Ева (менеджер)",
    }
    return users.get(user_id, f"Пользователь {user_id} не найден")


# --- Prompts ---

@mcp.prompt()
def summarize(text: str) -> str:
    """Промпт для суммаризации текста"""
    return f"Кратко изложи следующий текст:\n\n{text}"


@mcp.prompt()
def review_code(code: str, language: str = "python") -> str:
    """Промпт для код-ревью"""
    return f"Сделай код-ревью следующего {language} кода. Укажи проблемы и предложи улучшения:\n\n```{language}\n{code}\n```"


# %%
# Запуск сервера
if __name__ == "__main__":
    mcp.run(transport="streamable-http")

# %%
