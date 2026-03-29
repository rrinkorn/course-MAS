"""
Примеры кода к Лекции 4.4: SQL и базы данных — Text-to-SQL

Этот модуль демонстрирует:
1. Базовая настройка SQLDatabase
2. SQL Toolkit и агент
3. Обогащение контекста (sample values, descriptions, few-shot)
4. Безопасность: защита от SQL injection
5. Оптимизация производительности
6. Multi-turn SQL диалог
"""

import json
import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field

# ============================================================================
# ЧАСТЬ 1: Настройка SQLDatabase
# ============================================================================


def create_demo_database():
    """
    Создаёт демо-базу данных SQLite с тестовыми данными.

    Returns:
        Путь к созданной базе данных
    """
    import os
    import sqlite3
    import tempfile

    db_path = os.path.join(tempfile.gettempdir(), "demo_company.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создаём таблицы
    cursor.executescript("""
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            region VARCHAR(50),
            customer_type VARCHAR(10),  -- 'B2B' или 'B2C'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            price DECIMAL(10,2) NOT NULL
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            total_amount DECIMAL(10,2),
            status VARCHAR(20),  -- pending, confirmed, shipped, delivered, cancelled
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER,
            price DECIMAL(10,2)
        );

        -- Тестовые данные
        INSERT INTO customers (name, email, region, customer_type) VALUES
            ('Иван Петров', 'ivan@example.com', 'Москва', 'B2C'),
            ('ООО "Рога и Копыта"', 'info@rogakopyta.ru', 'СПб', 'B2B'),
            ('Мария Сидорова', 'maria@example.com', 'Сибирь', 'B2C'),
            ('ИП Козлов', 'kozlov@example.com', 'Урал', 'B2B'),
            ('Анна Иванова', 'anna@example.com', 'Москва', 'B2C');

        INSERT INTO products (name, category, price) VALUES
            ('Ноутбук Pro', 'Электроника', 89990.00),
            ('Смартфон X', 'Электроника', 49990.00),
            ('Наушники Wireless', 'Аксессуары', 7990.00),
            ('Клавиатура Mech', 'Аксессуары', 12990.00),
            ('Монитор 27"', 'Электроника', 34990.00);

        INSERT INTO orders (customer_id, total_amount, status, created_at) VALUES
            (1, 89990.00, 'delivered', '2025-01-15'),
            (2, 157970.00, 'delivered', '2025-01-20'),
            (1, 7990.00, 'shipped', '2025-02-01'),
            (3, 49990.00, 'pending', '2025-02-10'),
            (4, 112980.00, 'delivered', '2025-02-15'),
            (5, 34990.00, 'cancelled', '2025-02-20'),
            (2, 89990.00, 'delivered', '2025-03-01');

        INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
            (1, 1, 1, 89990.00),
            (2, 1, 1, 89990.00),
            (2, 2, 1, 49990.00),
            (2, 3, 1, 7990.00),
            (2, 4, 1, 12990.00),
            (3, 3, 1, 7990.00),
            (4, 2, 1, 49990.00),
            (5, 1, 1, 89990.00),
            (5, 3, 3, 7990.00),
            (6, 5, 1, 34990.00),
            (7, 1, 1, 89990.00);
    """)

    conn.commit()
    conn.close()

    return db_path


def demo_sql_database_setup():
    """
    Базовая настройка SQLDatabase из LangChain.

    Требуется: pip install langchain-community
    """
    from langchain_community.utilities import SQLDatabase

    db_path = create_demo_database()

    # Создаём подключение
    db = SQLDatabase.from_uri(
        f"sqlite:///{db_path}",
        include_tables=["customers", "orders", "products"],  # Ограничиваем таблицы
        sample_rows_in_table_info=3,  # Показывать 3 примера строк
    )

    # Получаем информацию о схеме
    print("=== Схема базы данных ===")
    print(db.get_table_info())

    # Выполняем запрос
    result = db.run("SELECT name, region FROM customers LIMIT 3")
    print(f"\n=== Результат запроса ===\n{result}")

    return db


# ============================================================================
# ЧАСТЬ 2: SQL Toolkit и создание агента
# ============================================================================


def demo_sql_toolkit():
    """
    SQL Toolkit — набор инструментов для работы с БД.

    Включает:
    - sql_db_query: выполнение SELECT
    - sql_db_schema: получение схемы таблиц
    - sql_db_list_tables: список таблиц
    - sql_db_query_checker: проверка SQL перед выполнением
    """
    import os

    from langchain_community.agent_toolkits import SQLDatabaseToolkit
    from langchain_community.utilities import SQLDatabase
    from langchain_openai import ChatOpenAI

    db_path = create_demo_database()
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

    toolkit = SQLDatabaseToolkit(
        db=db,
        llm=ChatOpenAI(
            model="gpt-5-mini",
            temperature=0,
            base_url=os.getenv("POLZAAI_BASE_URL"),
            api_key=os.getenv("POLZAAI_API_KEY"),
        ),
    )

    tools = toolkit.get_tools()

    print("=== Доступные SQL инструменты ===")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")

    return toolkit, db


def demo_sql_agent():
    """
    Создание SQL-агента с полным ReAct циклом.

    Агент автоматически:
    1. Получает список таблиц
    2. Запрашивает схему нужных таблиц
    3. Генерирует SQL
    4. Проверяет и выполняет запрос
    """
    from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
    from langchain_community.utilities import SQLDatabase
    from langchain_openai import ChatOpenAI

    db_path = create_demo_database()
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

    toolkit = SQLDatabaseToolkit(
        db=db, llm=ChatOpenAI(model="gpt-5-mini", temperature=0)
    )

    agent = create_sql_agent(
        llm=ChatOpenAI(model="gpt-5-mini", temperature=0),
        toolkit=toolkit,
        verbose=True,  # Показывать рассуждения
        agent_type="openai-tools",
    )

    # Пример вызова
    # result = agent.invoke({"input": "Покажи топ-3 клиентов по сумме заказов"})
    # print(result["output"])

    return agent


# ============================================================================
# ЧАСТЬ 3: Обогащение контекста
# ============================================================================

# Кастомные описания таблиц для лучшего понимания моделью
CUSTOM_TABLE_INFO = {
    "orders": """
    Таблица заказов клиентов.

    Колонки:
    - id: уникальный идентификатор заказа
    - customer_id: ID клиента (FK → customers.id)
    - total_amount: итоговая сумма заказа в рублях, ВКЛЮЧАЯ НДС
    - status: статус заказа. Возможные значения:
        * 'pending' — ожидает обработки
        * 'confirmed' — подтверждён
        * 'shipped' — отгружен
        * 'delivered' — доставлен (только эти считать выручкой!)
        * 'cancelled' — отменён
    - created_at: дата и время СОЗДАНИЯ заказа

    ВАЖНО: для расчёта выручки используй ТОЛЬКО заказы со статусом 'delivered'.
    """,
    "customers": """
    Таблица клиентов.

    Колонки:
    - region: регион клиента. Значения: 'Москва', 'СПб', 'Сибирь', 'Урал', 'Юг'
    - customer_type: тип клиента:
        * 'B2B' — юридические лица (корпоративные клиенты)
        * 'B2C' — физические лица (розничные клиенты)

    Для анализа крупных клиентов фильтруй по customer_type = 'B2B'.
    """,
    "products": """
    Таблица товаров.

    Колонки:
    - category: категория товара. Значения: 'Электроника', 'Аксессуары'
    - price: цена в рублях, включая НДС
    """,
}

# Few-shot примеры для обучения модели
FEW_SHOT_EXAMPLES = [
    {
        "input": "Сколько заказов было вчера?",
        "query": "SELECT COUNT(*) FROM orders WHERE DATE(created_at) = DATE('now', '-1 day')",
    },
    {
        "input": "Покажи выручку по месяцам за этот год",
        "query": """
            SELECT
                strftime('%Y-%m', created_at) as month,
                SUM(total_amount) as revenue
            FROM orders
            WHERE status = 'delivered'
                AND created_at >= DATE('now', 'start of year')
            GROUP BY month
            ORDER BY month
        """,
    },
    {
        "input": "Какой средний чек у B2B клиентов?",
        "query": """
            SELECT AVG(o.total_amount) as avg_check
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE c.customer_type = 'B2B'
                AND o.status = 'delivered'
        """,
    },
    {
        "input": "Топ-5 клиентов по сумме заказов",
        "query": """
            SELECT c.name, SUM(o.total_amount) as total_spent
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            WHERE o.status = 'delivered'
            GROUP BY c.id, c.name
            ORDER BY total_spent DESC
            LIMIT 5
        """,
    },
]


def create_enriched_prompt():
    """Создаёт обогащённый промпт с few-shot примерами."""
    examples_text = "\n\n".join(
        [f"Вопрос: {ex['input']}\nSQL: {ex['query']}" for ex in FEW_SHOT_EXAMPLES]
    )

    prompt = f"""
Ты — эксперт по SQL. Генерируй корректные SQL-запросы для SQLite.

ВАЖНЫЕ ПРАВИЛА:
1. Для выручки учитывай ТОЛЬКО заказы со статусом 'delivered'
2. Все суммы в рублях, включая НДС
3. Всегда добавляй LIMIT, если не уверен в объёме данных
4. Используй явные JOIN вместо подзапросов где возможно

ПРИМЕРЫ ЗАПРОСОВ ДЛЯ НАШЕЙ БАЗЫ:

{examples_text}

Теперь ответь на следующий вопрос:
"""

    return prompt


# ============================================================================
# ЧАСТЬ 4: Безопасность — защита от SQL Injection
# ============================================================================


class SQLQueryValidator:
    """Валидатор SQL-запросов для защиты от инъекций."""

    # Запрещённые ключевые слова
    DANGEROUS_KEYWORDS = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
        "CREATE",
        "EXEC",
        "EXECUTE",
        "xp_",
        "sp_",
        "--",
        ";--",
        "/*",
        "*/",
    ]

    # Разрешённые таблицы
    ALLOWED_TABLES = ["customers", "orders", "products", "order_items"]

    # Запрещённые колонки (чувствительные данные)
    BLOCKED_COLUMNS = {
        "customers": ["password", "password_hash", "credit_card"],
        "users": ["password", "salt", "api_key"],
    }

    def validate(self, query: str) -> tuple[bool, str]:
        """
        Проверяет SQL-запрос на безопасность.

        Returns:
            (is_valid, error_message)
        """
        query_upper = query.upper().strip()

        # 1. Проверка: только SELECT
        if not query_upper.startswith("SELECT"):
            return False, "Разрешены только SELECT-запросы"

        # 2. Проверка на опасные ключевые слова
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword.upper() in query_upper:
                return False, f"Запрещённое ключевое слово: {keyword}"

        # 3. Проверка на множественные statements (;)
        # Удаляем строки в кавычках для корректной проверки
        cleaned = re.sub(r"'[^']*'", "", query)
        cleaned = re.sub(r'"[^"]*"', "", cleaned)
        if ";" in cleaned:
            return False, "Множественные SQL-statements запрещены"

        # 4. Проверка на UNION-based injection
        if "UNION" in query_upper:
            # Разрешаем UNION только если нет подозрительных паттернов
            if re.search(r"UNION\s+(ALL\s+)?SELECT\s+\d", query_upper):
                return False, "Подозрительный UNION-паттерн"

        return True, ""


def safe_query_tool(query: str, db) -> str:
    """
    Безопасное выполнение SQL с валидацией.

    Args:
        query: SQL-запрос
        db: SQLDatabase instance
    """
    validator = SQLQueryValidator()

    # Валидация
    is_valid, error = validator.validate(query)
    if not is_valid:
        return f"❌ Запрос отклонён: {error}"

    # Принудительный LIMIT
    if "LIMIT" not in query.upper():
        query = query.rstrip(";") + " LIMIT 100"

    # Выполнение
    try:
        result = db.run(query)
        return result
    except Exception as e:
        return f"❌ Ошибка выполнения: {e}"


def demo_sql_security():
    """Демонстрация защиты от SQL injection."""
    from langchain_community.utilities import SQLDatabase

    db_path = create_demo_database()
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

    validator = SQLQueryValidator()

    # Тесты безопасности
    test_queries = [
        # Легитимные запросы
        ("SELECT * FROM customers", True),
        ("SELECT name, region FROM customers WHERE region = 'Москва'", True),
        # Опасные запросы
        ("DROP TABLE customers", False),
        ("SELECT * FROM customers; DROP TABLE orders", False),
        ("DELETE FROM orders WHERE id = 1", False),
        ("SELECT * FROM customers WHERE name = '' OR 1=1 --", False),
        ("SELECT * FROM customers UNION SELECT 1,2,3,4,5,6", False),
    ]

    print("=== Тесты безопасности SQL ===")
    for query, should_pass in test_queries:
        is_valid, error = validator.validate(query)
        status = "✅" if is_valid == should_pass else "❌"
        result_text = "OK" if is_valid else f"Blocked: {error}"
        print(f"{status} {query[:50]}... → {result_text}")


# ============================================================================
# ЧАСТЬ 5: Оптимизация производительности
# ============================================================================


class QueryOptimizer:
    """Анализатор и оптимизатор SQL-запросов."""

    # Функции, убивающие индексы
    INDEX_KILLING_FUNCTIONS = [
        "YEAR(",
        "MONTH(",
        "DATE(",
        "LOWER(",
        "UPPER(",
        "SUBSTR(",
    ]

    # Известные большие таблицы
    LARGE_TABLES = ["orders", "order_items", "logs", "events"]

    def analyze(self, query: str) -> List[str]:
        """
        Анализирует запрос на потенциальные проблемы производительности.

        Returns:
            Список предупреждений
        """
        issues = []
        query_upper = query.upper()

        # 1. Функции в WHERE убивают индексы
        if "WHERE" in query_upper:
            for func in self.INDEX_KILLING_FUNCTIONS:
                if func in query_upper:
                    issues.append(
                        f"⚠️ Функция {func[:-1]} в WHERE может замедлить запрос. "
                        "Используй диапазон дат вместо YEAR()/MONTH()."
                    )

        # 2. SELECT * на больших таблицах
        if "SELECT *" in query_upper or "SELECT  *" in query_upper:
            issues.append(
                "⚠️ SELECT * возвращает все колонки. "
                "Укажи конкретные колонки для экономии ресурсов."
            )

        # 3. Отсутствие LIMIT на больших таблицах
        if "LIMIT" not in query_upper:
            for table in self.LARGE_TABLES:
                if table.upper() in query_upper:
                    issues.append(
                        f"⚠️ Запрос к большой таблице '{table}' без LIMIT. "
                        "Добавь LIMIT для защиты от перегрузки."
                    )
                    break

        # 4. Картезианово произведение (JOIN без условия)
        if query_upper.count(" JOIN ") > 0:
            if " ON " not in query_upper and " USING " not in query_upper:
                issues.append(
                    "❌ JOIN без условия ON/USING создаёт декартово произведение!"
                )

        # 5. Подзапрос в WHERE (часто можно заменить JOIN)
        if re.search(r"WHERE.*\(\s*SELECT", query_upper):
            issues.append(
                "💡 Подзапрос в WHERE. Рассмотри замену на JOIN для оптимизации."
            )

        return issues


def demo_query_optimization():
    """Демонстрация анализа запросов."""
    optimizer = QueryOptimizer()

    test_queries = [
        # Проблемные запросы
        "SELECT * FROM orders WHERE YEAR(created_at) = 2025",
        "SELECT * FROM orders",
        "SELECT * FROM customers, orders",  # Картезианово произведение
        # Оптимальные запросы
        "SELECT id, total_amount FROM orders WHERE created_at >= '2025-01-01' LIMIT 100",
    ]

    print("=== Анализ производительности запросов ===")
    for query in test_queries:
        print(f"\nЗапрос: {query}")
        issues = optimizer.analyze(query)
        if issues:
            for issue in issues:
                print(f"  {issue}")
        else:
            print("  ✅ Запрос оптимален")


# ============================================================================
# ЧАСТЬ 6: Аудит и логирование
# ============================================================================


class SQLAuditLogger:
    """Логгер для аудита SQL-запросов."""

    def __init__(self, log_file: str = None):
        self.logger = logging.getLogger("sql_audit")
        self.logger.setLevel(logging.INFO)

        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()

        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        self.logger.addHandler(handler)

    def log_query(
        self,
        query: str,
        user_id: str,
        original_question: str,
        status: str,
        duration_ms: float,
        result_rows: int = 0,
        error: str = None,
    ):
        """Логирует выполненный запрос."""
        log_data = {
            "user_id": user_id,
            "question": original_question[:100],
            "query": query[:200],
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "result_rows": result_rows,
        }

        if error:
            log_data["error"] = error
            self.logger.warning(json.dumps(log_data, ensure_ascii=False))
        else:
            self.logger.info(json.dumps(log_data, ensure_ascii=False))


def audited_query(db, query: str, user_id: str, question: str) -> str:
    """Выполняет запрос с полным аудитом."""
    logger = SQLAuditLogger()
    start = datetime.now()

    try:
        result = db.run(query)
        duration = (datetime.now() - start).total_seconds() * 1000

        # Считаем строки (упрощённо)
        result_rows = result.count("\n") if result else 0

        logger.log_query(
            query=query,
            user_id=user_id,
            original_question=question,
            status="success",
            duration_ms=duration,
            result_rows=result_rows,
        )

        return result

    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000

        logger.log_query(
            query=query,
            user_id=user_id,
            original_question=question,
            status="error",
            duration_ms=duration,
            error=str(e),
        )

        raise


# ============================================================================
# ЧАСТЬ 7: Multi-turn SQL диалог
# ============================================================================


class SQLConversationManager:
    """
    Менеджер для ведения диалога с контекстом предыдущих запросов.

    Позволяет:
    - "Теперь разбей это по месяцам"
    - "Исключи отменённые заказы"
    - "Добавь колонку с регионом"
    """

    def __init__(self, db, llm=None):
        self.db = db
        self.llm = llm
        self.history: List[Dict[str, str]] = []

    def add_to_history(self, question: str, sql: str, result: str):
        """Добавляет запрос в историю."""
        self.history.append(
            {
                "question": question,
                "sql": sql,
                "result": result[:500],  # Ограничиваем размер
            }
        )

        # Храним только последние 5 запросов
        if len(self.history) > 5:
            self.history.pop(0)

    def get_context_prompt(self) -> str:
        """Формирует контекст из истории запросов."""
        if not self.history:
            return ""

        context = "Предыдущие запросы в этой сессии:\n\n"
        for i, h in enumerate(self.history[-3:], 1):  # Последние 3
            context += f"{i}. Вопрос: {h['question']}\n"
            context += f"   SQL: {h['sql']}\n\n"

        context += """
Если новый вопрос ссылается на предыдущие ("разбей это", "добавь", "исключи", "теперь"),
модифицируй последний SQL-запрос соответственно.
"""
        return context

    def process(self, question: str) -> str:
        """
        Обрабатывает вопрос с учётом контекста.

        В реальной реализации здесь был бы вызов LLM.
        """
        context = self.get_context_prompt()

        full_prompt = f"""
{context}

Новый вопрос: {question}

Сгенерируй SQL-запрос:
"""
        print(f"Промпт для LLM:\n{full_prompt}")

        # Здесь был бы вызов LLM для генерации SQL
        # sql = self.llm.invoke(full_prompt)

        return "SQL будет сгенерирован LLM..."


def demo_multi_turn():
    """Демонстрация multi-turn диалога."""
    from langchain_community.utilities import SQLDatabase

    db_path = create_demo_database()
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

    manager = SQLConversationManager(db)

    # Симулируем диалог
    manager.add_to_history(
        question="Покажи топ-10 товаров по продажам",
        sql="SELECT p.name, SUM(oi.quantity) as sold FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id ORDER BY sold DESC LIMIT 10",
        result="[результат...]",
    )

    # Следующий вопрос ссылается на предыдущий
    result = manager.process("Теперь разбей это по месяцам")
    print(result)


# ============================================================================
# ДЕМОНСТРАЦИЯ
# ============================================================================


def demo():
    """Запуск всех демонстраций."""
    print("=" * 60)
    print("SQL AND DATABASES (Лекция 4.4)")
    print("=" * 60)

    # --- Создание базы данных ---
    print("\n--- Создание демо-базы данных ---")
    db_path = create_demo_database()
    print(f"База данных создана: {db_path}")

    # --- SQLDatabase setup ---
    print("\n--- SQLDatabase setup ---")
    try:
        demo_sql_database_setup()
    except ImportError:
        print("langchain-community не установлен")

    # --- Безопасность ---
    print("\n--- SQL Security ---")
    try:
        demo_sql_security()
    except ImportError:
        print("langchain-community не установлен")

    # --- Оптимизация ---
    print("\n--- Query Optimization ---")
    demo_query_optimization()

    # --- Enriched Prompt ---
    print("\n--- Enriched Prompt Example ---")
    prompt = create_enriched_prompt()
    print(prompt[:500] + "...")

    # --- Multi-turn ---
    print("\n--- Multi-turn Dialogue ---")
    try:
        demo_multi_turn()
    except ImportError:
        print("langchain-community не установлен")

    # --- SQL Toolkit ---
    print("\n--- SQL Toolkit ---")
    try:
        toolkit, db = demo_sql_toolkit()
    except ImportError:
        print("langchain-community или langchain-openai не установлены")

    print("\n" + "=" * 60)
    print("Для полной демонстрации установите:")
    print("  pip install langchain-community langchain-openai")
    print("=" * 60)


if __name__ == "__main__":
    demo()
