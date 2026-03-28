"""
Примеры кода к Лекции 4.1: Function Calling — Когда слова обретают силу действия

Этот модуль демонстрирует:
1. OpenAI Function Calling API
2. Anthropic Tool Use
3. Конвертация Python-функций в JSON Schema
4. Параллельный вызов функций
5. Полный ReAct-цикл
"""

import json
from typing import Literal
from pydantic import BaseModel, Field


# ============================================================================
# ЧАСТЬ 1: OpenAI Function Calling
# ============================================================================

def demo_openai_function_calling():
    """
    Демонстрация базового Function Calling с OpenAI API.

    Требуется: pip install openai
    """
    from openai import OpenAI

    client = OpenAI()

    # Определяем инструменты (tools)
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

    # Первый вызов — модель решает, вызывать ли функцию
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"  # Модель сама решает
    )

    return response


def demo_full_react_cycle():
    """
    Полный цикл Thought-Action-Observation (ReAct).

    Показывает, как обработать вызов функции и вернуть результат модели.
    """
    from openai import OpenAI

    client = OpenAI()

    # Определение инструментов
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Получает текущую погоду в городе",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "Название города"}
                    },
                    "required": ["city"]
                }
            }
        }
    ]

    # Реализация функции
    def get_weather(city: str) -> dict:
        """Заглушка для демонстрации. В реальности — вызов API погоды."""
        weather_data = {
            "Tokyo": {"temp": 22, "condition": "sunny"},
            "Moscow": {"temp": -5, "condition": "snowy"},
            "Paris": {"temp": 15, "condition": "cloudy"},
        }
        return weather_data.get(city, {"temp": 20, "condition": "unknown"})

    messages = [
        {"role": "user", "content": "Какая погода в Токио?"}
    ]

    # Шаг 1: Первый вызов — модель решает вызвать функцию
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message

    # Проверяем, вызвала ли модель функцию
    if assistant_message.tool_calls:
        # Шаг 2: Выполняем функцию
        tool_call = assistant_message.tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        # Вызываем реальную функцию
        result = get_weather(**function_args)

        # Шаг 3: Добавляем сообщения в историю
        messages.append(assistant_message)  # Сообщение ассистента с tool_calls
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })

        # Шаг 4: Финальный вызов — модель формулирует ответ
        final_response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
            tools=tools
        )

        return final_response.choices[0].message.content

    return assistant_message.content


# ============================================================================
# ЧАСТЬ 2: Anthropic Tool Use
# ============================================================================

def demo_anthropic_tool_use():
    """
    Демонстрация Tool Use с Anthropic Claude.

    Требуется: pip install anthropic
    """
    import anthropic

    client = anthropic.Anthropic()

    tools = [
        {
            "name": "get_stock_price",
            "description": "Получить текущую цену акции по тикеру",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Биржевой тикер акции, например 'AAPL'"
                    }
                },
                "required": ["ticker"]
            }
        }
    ]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=tools,
        messages=[
            {"role": "user", "content": "Сколько стоит акция Tesla?"}
        ]
    )

    # Claude может одновременно писать текст и вызывать функцию!
    for block in response.content:
        if block.type == "text":
            print(f"Текст: {block.text}")
        elif block.type == "tool_use":
            print(f"Вызов функции: {block.name}({block.input})")

    return response


# ============================================================================
# ЧАСТЬ 3: Конвертация Python-функций в JSON Schema
# ============================================================================

def calculate_mortgage(
    principal: float,
    annual_rate: float,
    years: int,
    down_payment: float = 0.0
) -> dict:
    """
    Рассчитать ежемесячный платёж по ипотеке.

    Используй эту функцию, когда пользователь спрашивает о расчёте
    ипотечного кредита, ежемесячных платежей или сравнении условий.

    Args:
        principal: Стоимость недвижимости в рублях
        annual_rate: Годовая процентная ставка (например, 12.5 для 12.5%)
        years: Срок кредита в годах
        down_payment: Первоначальный взнос в рублях (по умолчанию 0)

    Returns:
        Словарь с суммой кредита, ежемесячным платежом и общей переплатой
    """
    loan_amount = principal - down_payment
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12

    # Формула аннуитетного платежа
    if monthly_rate > 0:
        monthly_payment = loan_amount * (
            monthly_rate * (1 + monthly_rate)**num_payments
        ) / ((1 + monthly_rate)**num_payments - 1)
    else:
        monthly_payment = loan_amount / num_payments

    total_paid = monthly_payment * num_payments

    return {
        "loan_amount": round(loan_amount, 2),
        "monthly_payment": round(monthly_payment, 2),
        "total_paid": round(total_paid, 2),
        "overpayment": round(total_paid - loan_amount, 2)
    }


def convert_function_to_schema():
    """
    Автоматическая конвертация Python-функции в JSON Schema.

    Требуется: pip install langchain-core
    """
    from langchain_core.utils.function_calling import convert_to_openai_function

    # Магическое превращение
    openai_function = convert_to_openai_function(calculate_mortgage)

    print("Результат конвертации:")
    print(json.dumps(openai_function, indent=2, ensure_ascii=False))

    return openai_function


# ============================================================================
# ЧАСТЬ 4: Pydantic для сложных схем
# ============================================================================

class PropertyType(str):
    """Типы недвижимости."""
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"


class MortgageInput(BaseModel):
    """Входные параметры для расчёта ипотеки."""

    principal: float = Field(
        ...,
        description="Стоимость недвижимости в рублях",
        gt=0,
        examples=[5000000, 10000000]
    )
    annual_rate: float = Field(
        ...,
        description="Годовая процентная ставка в процентах",
        ge=0,
        le=100
    )
    years: int = Field(
        ...,
        description="Срок кредита в годах",
        ge=1,
        le=30
    )
    down_payment: float = Field(
        default=0.0,
        description="Первоначальный взнос в рублях",
        ge=0
    )
    property_type: Literal["apartment", "house", "commercial"] = Field(
        default="apartment",
        description="Тип недвижимости"
    )


def demo_pydantic_schema():
    """Демонстрация генерации JSON Schema из Pydantic-модели."""
    schema = MortgageInput.model_json_schema()
    print("Pydantic JSON Schema:")
    print(json.dumps(schema, indent=2, ensure_ascii=False))
    return schema


# ============================================================================
# ЧАСТЬ 5: Параллельный вызов функций
# ============================================================================

def demo_parallel_function_calls():
    """
    Демонстрация параллельного вызова функций.

    Модель может вернуть несколько tool_calls за один запрос.
    """
    from openai import OpenAI

    client = OpenAI()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Получает погоду в городе",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"}
                    },
                    "required": ["city"]
                }
            }
        }
    ]

    # Запрос, требующий нескольких вызовов
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": "Сравни погоду в Москве, Париже и Токио"}
        ],
        tools=tools,
        tool_choice="auto"
    )

    # Модель вернёт три tool_calls!
    if response.choices[0].message.tool_calls:
        for call in response.choices[0].message.tool_calls:
            print(f"Вызов: {call.function.name}({call.function.arguments})")

    return response


async def execute_parallel_tool_calls(tool_calls: list) -> list:
    """
    Параллельное выполнение вызовов функций с asyncio.

    Args:
        tool_calls: Список tool_calls от модели

    Returns:
        Список результатов с id вызовов
    """
    import asyncio

    async def get_weather_async(city: str) -> dict:
        """Асинхронная заглушка для погоды."""
        await asyncio.sleep(0.1)  # Имитация задержки API
        weather_data = {
            "Moscow": {"temp": -5, "condition": "snowy"},
            "Paris": {"temp": 15, "condition": "cloudy"},
            "Tokyo": {"temp": 22, "condition": "sunny"},
        }
        return weather_data.get(city, {"temp": 20, "condition": "unknown"})

    # Создаём задачи для всех вызовов
    tasks = []
    for call in tool_calls:
        args = json.loads(call.function.arguments)
        if call.function.name == "get_weather":
            tasks.append(get_weather_async(**args))

    # Выполняем параллельно
    results = await asyncio.gather(*tasks)

    # Возвращаем с привязкой к id
    return [
        {"tool_call_id": call.id, "result": result}
        for call, result in zip(tool_calls, results)
    ]


# ============================================================================
# ЧАСТЬ 6: Обработка ошибок и валидация
# ============================================================================

class FunctionCallValidator:
    """Валидатор вызовов функций от LLM."""

    def __init__(self, allowed_functions: list[str]):
        self.allowed_functions = allowed_functions

    def validate_tool_call(self, tool_call) -> tuple[bool, str]:
        """
        Проверяет вызов функции на корректность.

        Returns:
            (is_valid, error_message)
        """
        # Проверка имени функции
        if tool_call.function.name not in self.allowed_functions:
            return False, f"Функция '{tool_call.function.name}' не разрешена"

        # Проверка JSON аргументов
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            return False, f"Невалидный JSON в аргументах: {e}"

        return True, ""

    def safe_execute(self, tool_call, functions_map: dict):
        """
        Безопасное выполнение вызова с обработкой ошибок.

        Args:
            tool_call: Вызов функции от модели
            functions_map: Словарь {имя: функция}
        """
        is_valid, error = self.validate_tool_call(tool_call)
        if not is_valid:
            return {"error": error}

        func = functions_map.get(tool_call.function.name)
        if not func:
            return {"error": f"Функция не найдена: {tool_call.function.name}"}

        try:
            args = json.loads(tool_call.function.arguments)
            result = func(**args)
            return {"result": result}
        except TypeError as e:
            return {"error": f"Неверные аргументы: {e}"}
        except Exception as e:
            return {"error": f"Ошибка выполнения: {e}"}


# ============================================================================
# ЧАСТЬ 7: Сравнение API разных провайдеров
# ============================================================================

PROVIDER_COMPARISON = """
┌───────────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Характеристика        │ OpenAI (GPT-5)   │ Anthropic Claude │ Llama 4/Mistral  │
├───────────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Название механизма    │ Tools/Functions  │ Tool Use         │ Varies           │
│ Параллельные вызовы   │ ✓                │ ✓                │ Depends          │
│ Текст + вызов вместе  │ ✗ (только вызов) │ ✓                │ Varies           │
│ Структур. вывод       │ JSON Mode        │ Tool Use         │ Varies           │
│ Max функций           │ ~128             │ ~20-50           │ Varies           │
│ Стриминг              │ ✓                │ ✓                │ Varies           │
└───────────────────────┴──────────────────┴──────────────────┴──────────────────┘
"""


# ============================================================================
# ДЕМОНСТРАЦИЯ
# ============================================================================

def demo():
    """Демонстрация всех примеров."""
    print("=" * 60)
    print("FUNCTION CALLING EXAMPLES (Лекция 4.1)")
    print("=" * 60)

    # --- Конвертация функции ---
    print("\n--- Конвертация Python → JSON Schema ---")
    try:
        schema = convert_function_to_schema()
    except ImportError:
        print("langchain-core не установлен, пропускаем...")

    # --- Pydantic Schema ---
    print("\n--- Pydantic Model Schema ---")
    demo_pydantic_schema()

    # --- Расчёт ипотеки ---
    print("\n--- Расчёт ипотеки ---")
    result = calculate_mortgage(
        principal=10_000_000,
        annual_rate=12.5,
        years=20,
        down_payment=2_000_000
    )
    print(f"Сумма кредита: {result['loan_amount']:,.2f} ₽")
    print(f"Ежемесячный платёж: {result['monthly_payment']:,.2f} ₽")
    print(f"Переплата: {result['overpayment']:,.2f} ₽")

    # --- Валидатор ---
    print("\n--- Валидатор вызовов ---")
    validator = FunctionCallValidator(["get_weather", "calculate_mortgage"])
    print(f"Разрешённые функции: {validator.allowed_functions}")

    # --- Сравнение провайдеров ---
    print("\n--- Сравнение API провайдеров ---")
    print(PROVIDER_COMPARISON)

    print("\n" + "=" * 60)
    print("Для полной демонстрации с API вызовами установите:")
    print("  pip install openai anthropic langchain-core")
    print("=" * 60)


if __name__ == "__main__":
    demo()
