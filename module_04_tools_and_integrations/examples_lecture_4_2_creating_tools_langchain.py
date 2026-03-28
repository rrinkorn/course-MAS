"""
Примеры кода к Лекции 4.2: Создание инструментов в LangChain

Этот модуль демонстрирует:
1. Декоратор @tool — базовое использование
2. StructuredTool — полный контроль
3. Валидация через Pydantic
4. Обработка ошибок (handle_tool_error)
5. Асинхронные инструменты
6. Тестирование инструментов
"""

import time
from datetime import date
from functools import wraps
from typing import Literal

from pydantic import BaseModel, Field, field_validator, ValidationError


# ============================================================================
# ЧАСТЬ 1: Декоратор @tool — базовое использование
# ============================================================================

def demo_basic_tool():
    """Демонстрация базового использования декоратора @tool."""
    from langchain_core.tools import tool

    @tool
    def multiply(a: int, b: int) -> int:
        """Умножает два числа и возвращает результат."""
        return a * b

    # Исследуем созданный инструмент
    print(f"Имя: {multiply.name}")
    print(f"Описание: {multiply.description}")
    print(f"Схема аргументов: {multiply.args_schema.schema()}")

    # Вызов инструмента
    result = multiply.invoke({"a": 3, "b": 4})
    print(f"multiply(3, 4) = {result}")

    return multiply


def demo_detailed_docstring():
    """Пример инструмента с подробным docstring."""
    from langchain_core.tools import tool

    @tool
    def search_web(query: str) -> str:
        """
        Поиск информации в интернете через поисковую систему.

        Используй этот инструмент когда:
        - Пользователь спрашивает о текущих событиях или новостях
        - Нужны актуальные данные (курсы валют, погода, цены)
        - Вопрос о чём-то, что произошло после твоей даты обучения
        - Требуется проверить факт из внешнего источника

        НЕ используй когда:
        - Вопрос об общих знаниях, которые ты точно знаешь
        - Пользователь просит твоё мнение или рассуждение
        - Это математическая задача или логическая головоломка

        Args:
            query: Поисковый запрос. Формулируй кратко и конкретно.

        Returns:
            Топ-5 результатов поиска с заголовками и описаниями.
        """
        # Заглушка — в реальности здесь был бы API поиска
        return f"Результаты поиска по запросу '{query}': ..."

    return search_web


def demo_tool_with_parameters():
    """Пример с параметрами декоратора @tool."""
    from langchain_core.tools import tool

    @tool(
        name="stock_chart_generator",
        return_direct=True,  # Результат сразу пользователю, без обработки LLM
    )
    def get_stock_chart(ticker: str) -> str:
        """Генерирует график цены акции и возвращает URL картинки."""
        # В реальности — генерация графика
        url = f"https://charts.example.com/{ticker}.png"
        return f"![График {ticker}]({url})"

    print(f"return_direct: {get_stock_chart.return_direct}")
    return get_stock_chart


# ============================================================================
# ЧАСТЬ 2: StructuredTool — полный контроль
# ============================================================================

class CalculatorInput(BaseModel):
    """Входные параметры калькулятора."""
    expression: str = Field(
        description="Математическое выражение для вычисления, например '2 + 2 * 3'"
    )
    precision: int = Field(
        default=2,
        description="Количество знаков после запятой в результате",
        ge=0,
        le=10
    )


def safe_eval(expression: str, precision: int = 2) -> str:
    """
    Безопасное вычисление математического выражения.

    ВНИМАНИЕ: eval() опасен! В продакшне используйте ast.literal_eval
    или специализированные библиотеки типа sympy.
    """
    import ast
    import operator

    # Безопасный eval через AST
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](_eval(node.operand))
        else:
            raise ValueError(f"Неподдерживаемая операция: {type(node)}")

    try:
        tree = ast.parse(expression, mode='eval')
        result = _eval(tree.body)
        return str(round(result, precision))
    except Exception as e:
        return f"Ошибка вычисления: {e}"


def demo_structured_tool():
    """Демонстрация StructuredTool."""
    from langchain_core.tools import StructuredTool

    calculator = StructuredTool.from_function(
        func=safe_eval,
        name="calculator",
        description="Вычисляет математические выражения. Поддерживает +, -, *, /, **, скобки.",
        args_schema=CalculatorInput,
        return_direct=False,
    )

    # Тестируем
    result = calculator.invoke({"expression": "2 + 2 * 3", "precision": 2})
    print(f"2 + 2 * 3 = {result}")

    result = calculator.invoke({"expression": "3.14159 * 2 ** 2", "precision": 4})
    print(f"π * r² (r=2) ≈ {result}")

    return calculator


# ============================================================================
# ЧАСТЬ 3: Валидация через Pydantic
# ============================================================================

class FlightSearchInput(BaseModel):
    """Параметры поиска авиабилетов с полной валидацией."""

    origin: str = Field(
        description="Код аэропорта вылета (IATA), например 'SVO', 'LED', 'JFK'",
        min_length=3,
        max_length=3,
    )
    destination: str = Field(
        description="Код аэропорта назначения (IATA)",
        min_length=3,
        max_length=3,
    )
    departure_date: date = Field(
        description="Дата вылета в формате YYYY-MM-DD"
    )
    return_date: date | None = Field(
        default=None,
        description="Дата возвращения (для билетов туда-обратно)"
    )
    passengers: int = Field(
        default=1,
        description="Количество пассажиров",
        ge=1,
        le=9
    )
    cabin_class: Literal["economy", "business", "first"] = Field(
        default="economy",
        description="Класс обслуживания"
    )

    @field_validator("origin", "destination")
    @classmethod
    def uppercase_airport_code(cls, v: str) -> str:
        """Приводит код аэропорта к верхнему регистру."""
        return v.upper()

    @field_validator("departure_date")
    @classmethod
    def departure_not_in_past(cls, v: date) -> date:
        """Проверяет, что дата вылета не в прошлом."""
        if v < date.today():
            raise ValueError("Дата вылета не может быть в прошлом")
        return v

    @field_validator("return_date")
    @classmethod
    def return_after_departure(cls, v: date | None, info) -> date | None:
        """Проверяет, что дата возвращения после даты вылета."""
        if v is not None:
            departure = info.data.get("departure_date")
            if departure and v < departure:
                raise ValueError("Дата возвращения должна быть после даты вылета")
        return v


def demo_pydantic_validation():
    """Демонстрация валидации Pydantic."""
    # Корректный ввод
    valid_input = FlightSearchInput(
        origin="svo",  # будет приведён к SVO
        destination="led",
        departure_date=date(2025, 6, 15),
        passengers=2,
        cabin_class="business"
    )
    print(f"Валидный ввод: {valid_input}")

    # Некорректный ввод — дата в прошлом
    try:
        invalid_input = FlightSearchInput(
            origin="SVO",
            destination="LED",
            departure_date=date(2020, 1, 1),  # В прошлом!
        )
    except ValidationError as e:
        print(f"Ошибка валидации: {e.errors()}")

    # Некорректный ввод — return раньше departure
    try:
        invalid_input = FlightSearchInput(
            origin="SVO",
            destination="LED",
            departure_date=date(2025, 6, 15),
            return_date=date(2025, 6, 10),  # Раньше departure!
        )
    except ValidationError as e:
        print(f"Ошибка валидации: {e.errors()}")


def search_flights_with_validation(input_dict: dict) -> str:
    """Обёртка инструмента с безопасной валидацией."""
    try:
        validated = FlightSearchInput(**input_dict)
    except ValidationError as e:
        errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        return f"Ошибка в параметрах: {'; '.join(errors)}. Исправь и попробуй снова."

    # Если валидация прошла — выполняем поиск
    return f"Найдены рейсы {validated.origin} → {validated.destination} на {validated.departure_date}"


# ============================================================================
# ЧАСТЬ 4: Обработка ошибок (handle_tool_error)
# ============================================================================

def demo_handle_tool_error():
    """Демонстрация handle_tool_error."""
    from langchain_core.tools import tool, ToolException

    @tool(handle_tool_error=True)
    def fetch_stock_price(ticker: str) -> str:
        """Получает текущую цену акции по тикеру."""
        # Имитация ошибки API
        if ticker == "INVALID":
            raise ToolException("Тикер не найден на бирже")
        if ticker == "ERROR":
            raise ToolException("API временно недоступен (rate limit)")

        # Успешный результат
        return f"Цена {ticker}: $123.45"

    # Успешный вызов
    print(fetch_stock_price.invoke({"ticker": "AAPL"}))

    # Ошибка — будет обработана gracefully
    print(fetch_stock_price.invoke({"ticker": "INVALID"}))

    return fetch_stock_price


def smart_error_handler(error) -> str:
    """Умный обработчик ошибок с рекомендациями."""
    error_msg = str(error)

    if "rate limit" in error_msg.lower():
        return "⏳ API временно недоступен из-за превышения лимита. Подожди минуту."
    elif "not found" in error_msg.lower():
        return "❌ Не найдено. Проверь правильность написания (например, AAPL для Apple)."
    elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
        return "🌐 Проблемы с сетью. Попробуй повторить запрос позже."
    else:
        return f"⚠️ Ошибка: {error_msg}. Попробуй переформулировать запрос."


def demo_custom_error_handler():
    """Демонстрация кастомного обработчика ошибок."""
    from langchain_core.tools import tool, ToolException

    @tool(handle_tool_error=smart_error_handler)
    def unreliable_api(query: str) -> str:
        """Вызов нестабильного API."""
        raise ToolException("API rate limit exceeded")

    result = unreliable_api.invoke({"query": "test"})
    print(f"Результат с кастомным обработчиком: {result}")


# ============================================================================
# ЧАСТЬ 5: Retry с экспоненциальной задержкой
# ============================================================================

def with_retry(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Декоратор для автоматического retry с экспоненциальной задержкой.

    Формула: delay = base_delay * (2 ** attempt)
    При base_delay=1: 1s, 2s, 4s, 8s, ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"Попытка {attempt + 1} не удалась. Ждём {delay}s...")
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


@with_retry(max_attempts=3, base_delay=0.1)
def flaky_function():
    """Функция, которая иногда падает."""
    import random
    if random.random() < 0.7:
        raise ConnectionError("Сервер недоступен")
    return "Успех!"


def demo_retry():
    """Демонстрация retry."""
    try:
        result = flaky_function()
        print(f"Результат: {result}")
    except ConnectionError as e:
        print(f"Все попытки исчерпаны: {e}")


# ============================================================================
# ЧАСТЬ 6: Асинхронные инструменты
# ============================================================================

async def demo_async_tool():
    """Демонстрация асинхронного инструмента."""
    from langchain_core.tools import StructuredTool
    import asyncio

    class WeatherInput(BaseModel):
        city: str = Field(description="Название города")

    async def get_weather_async(city: str) -> str:
        """Асинхронное получение погоды."""
        await asyncio.sleep(0.1)  # Имитация задержки API
        weather_data = {
            "Moscow": "❄️ -5°C, снег",
            "Paris": "🌧️ 12°C, дождь",
            "Tokyo": "☀️ 22°C, солнечно",
        }
        return weather_data.get(city, f"Погода в {city}: данные недоступны")

    weather_tool = StructuredTool.from_function(
        coroutine=get_weather_async,  # Обратите внимание: coroutine!
        name="get_weather",
        description="Получает текущую погоду в городе",
        args_schema=WeatherInput,
    )

    # Асинхронный вызов
    result = await weather_tool.ainvoke({"city": "Tokyo"})
    print(f"Погода: {result}")

    return weather_tool


# ============================================================================
# ЧАСТЬ 7: Инструменты с контекстом выполнения
# ============================================================================

def demo_tool_with_config():
    """Демонстрация передачи контекста через RunnableConfig."""
    from langchain_core.tools import tool
    from langchain_core.runnables import RunnableConfig

    @tool
    def get_user_preferences(config: RunnableConfig) -> str:
        """
        Получает настройки текущего пользователя.

        Параметр config автоматически передаётся LangChain
        и не включается в JSON Schema.
        """
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return "Ошибка: пользователь не идентифицирован"

        # В реальности — запрос к БД
        preferences = {
            "user_123": {"theme": "dark", "language": "ru"},
            "user_456": {"theme": "light", "language": "en"},
        }
        return str(preferences.get(user_id, "Настройки не найдены"))

    # Вызов с конфигурацией
    result = get_user_preferences.invoke(
        {},  # Входные параметры пустые
        config={"configurable": {"user_id": "user_123"}}
    )
    print(f"Настройки пользователя: {result}")

    return get_user_preferences


# ============================================================================
# ЧАСТЬ 8: Тестирование инструментов
# ============================================================================

def test_calculator_tool():
    """Юнит-тесты для калькулятора."""
    from langchain_core.tools import StructuredTool

    calculator = StructuredTool.from_function(
        func=safe_eval,
        name="calculator",
        description="Калькулятор",
        args_schema=CalculatorInput,
    )

    # Тест базовой функциональности
    assert calculator.invoke({"expression": "2 + 2"}) == "4"
    assert calculator.invoke({"expression": "3 * 4"}) == "12"
    assert calculator.invoke({"expression": "10 / 4", "precision": 2}) == "2.5"

    # Тест схемы
    schema = calculator.args_schema.schema()
    assert "expression" in schema["properties"]
    assert "precision" in schema["properties"]

    print("✅ Все тесты калькулятора прошли!")


def test_flight_search_validation():
    """Тесты валидации поиска билетов."""
    from datetime import timedelta

    # Валидный ввод
    tomorrow = date.today() + timedelta(days=1)
    valid = FlightSearchInput(
        origin="svo",
        destination="led",
        departure_date=tomorrow,
    )
    assert valid.origin == "SVO"  # Uppercase applied
    assert valid.destination == "LED"
    print("✅ Валидный ввод прошёл проверку")

    # Невалидный ввод — дата в прошлом
    try:
        FlightSearchInput(
            origin="SVO",
            destination="LED",
            departure_date=date(2020, 1, 1),
        )
        assert False, "Должна была быть ошибка!"
    except ValidationError:
        print("✅ Дата в прошлом корректно отклонена")

    # Невалидный ввод — слишком много пассажиров
    try:
        FlightSearchInput(
            origin="SVO",
            destination="LED",
            departure_date=tomorrow,
            passengers=15,  # Max 9
        )
        assert False, "Должна была быть ошибка!"
    except ValidationError:
        print("✅ Превышение лимита пассажиров корректно отклонено")

    print("✅ Все тесты валидации прошли!")


# ============================================================================
# ДЕМОНСТРАЦИЯ
# ============================================================================

def demo():
    """Запуск всех демонстраций."""
    print("=" * 60)
    print("CREATING TOOLS IN LANGCHAIN (Лекция 4.2)")
    print("=" * 60)

    try:
        # --- Базовый @tool ---
        print("\n--- Базовый декоратор @tool ---")
        demo_basic_tool()

        # --- StructuredTool ---
        print("\n--- StructuredTool ---")
        demo_structured_tool()

        # --- Pydantic валидация ---
        print("\n--- Pydantic валидация ---")
        demo_pydantic_validation()

        # --- handle_tool_error ---
        print("\n--- handle_tool_error ---")
        demo_handle_tool_error()

        # --- Кастомный обработчик ошибок ---
        print("\n--- Кастомный обработчик ошибок ---")
        demo_custom_error_handler()

        # --- Retry ---
        print("\n--- Retry с экспоненциальной задержкой ---")
        demo_retry()

        # --- Контекст выполнения ---
        print("\n--- Инструмент с контекстом ---")
        demo_tool_with_config()

        # --- Тесты ---
        print("\n--- Тестирование инструментов ---")
        test_calculator_tool()
        test_flight_search_validation()

        # --- Асинхронный инструмент ---
        print("\n--- Асинхронный инструмент ---")
        import asyncio
        asyncio.run(demo_async_tool())

    except ImportError as e:
        print(f"\nДля полной демонстрации установите: pip install langchain-core")
        print(f"Ошибка импорта: {e}")

    print("\n" + "=" * 60)
    print("Демонстрация завершена!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
