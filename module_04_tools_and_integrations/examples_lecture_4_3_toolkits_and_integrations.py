"""
Примеры кода к Лекции 4.3: Toolkit и готовые интеграции

Этот модуль демонстрирует:
1. Поисковые интеграции (Tavily, Serper, DuckDuckGo)
2. File Management Toolkit
3. Python REPL (Code Interpreter)
4. Shell-инструменты с белым списком
5. Комбинирование Toolkit'ов
6. Создание собственного Toolkit
"""

import os
import subprocess
import shlex
from typing import List
from pydantic import BaseModel, Field


# ============================================================================
# ЧАСТЬ 1: Поисковые интеграции
# ============================================================================

def demo_tavily_search():
    """
    Tavily — AI-оптимизированный поиск.

    Возвращает извлечённый контент, готовый для LLM.
    Требуется: pip install langchain-community tavily-python
    Переменная окружения: TAVILY_API_KEY
    """
    from langchain_community.tools.tavily_search import TavilySearchResults

    search = TavilySearchResults(
        max_results=5,
        search_depth="advanced",  # "basic" или "advanced"
        include_answer=True,       # AI-генерированный ответ
        include_raw_content=True,  # Полный текст страниц
    )

    result = search.invoke({"query": "latest AI developments 2025"})
    print(f"Tavily результаты: {len(result)} элементов")
    for item in result[:2]:  # Показываем первые 2
        print(f"  - {item.get('title', 'N/A')}: {item.get('url', 'N/A')}")

    return search


def demo_serper_search():
    """
    Google Serper — бюджетный доступ к Google Search.

    Требуется: pip install langchain-community google-serper
    Переменная окружения: SERPER_API_KEY
    """
    from langchain_community.utilities import GoogleSerperAPIWrapper

    # Обычный поиск
    search = GoogleSerperAPIWrapper(
        k=10,  # Количество результатов
        type="search"  # "search", "news", "images", "places"
    )

    # Поиск новостей
    news_search = GoogleSerperAPIWrapper(type="news")

    # Пример вызова (закомментирован для демо без API key)
    # result = search.run("AI agents 2025")
    # news = news_search.run("artificial intelligence")

    return search, news_search


def demo_duckduckgo_search():
    """
    DuckDuckGo — бесплатный поиск без API ключа.

    Идеально для прототипирования!
    Требуется: pip install langchain-community duckduckgo-search
    """
    from langchain_community.tools import DuckDuckGoSearchRun

    search = DuckDuckGoSearchRun()

    result = search.invoke("что такое LangChain")
    print(f"DuckDuckGo результат: {result[:200]}...")

    return search


# ============================================================================
# ЧАСТЬ 2: File Management Toolkit
# ============================================================================

def demo_file_management_toolkit():
    """
    FileManagementToolkit — безопасная работа с файлами.

    Ключевое: root_dir ограничивает агента только этой директорией!
    """
    from langchain_community.agent_toolkits import FileManagementToolkit

    # Создаём временную рабочую директорию
    import tempfile
    workspace = tempfile.mkdtemp(prefix="agent_workspace_")

    toolkit = FileManagementToolkit(
        root_dir=workspace,
        selected_tools=[  # Выбираем только нужные операции
            "read_file",
            "write_file",
            "list_directory",
            "file_search",
        ]
        # Не включаем delete_file, move_file, copy_file — минимум привилегий!
    )

    tools = toolkit.get_tools()
    print(f"Доступные инструменты: {[t.name for t in tools]}")

    # Демонстрация использования
    write_tool = next(t for t in tools if t.name == "write_file")
    read_tool = next(t for t in tools if t.name == "read_file")
    list_tool = next(t for t in tools if t.name == "list_directory")

    # Записываем файл
    write_tool.invoke({
        "file_path": "test.txt",
        "text": "Hello from AI Agent!"
    })

    # Читаем файл
    content = read_tool.invoke({"file_path": "test.txt"})
    print(f"Содержимое файла: {content}")

    # Список файлов
    files = list_tool.invoke({"dir_path": "."})
    print(f"Файлы в директории: {files}")

    # Очистка
    import shutil
    shutil.rmtree(workspace)

    return toolkit


def demo_file_security():
    """Демонстрация защиты от path traversal."""
    from langchain_community.agent_toolkits import FileManagementToolkit
    import tempfile

    workspace = tempfile.mkdtemp()

    toolkit = FileManagementToolkit(
        root_dir=workspace,
        selected_tools=["read_file"]
    )

    read_tool = toolkit.get_tools()[0]

    # Попытка выйти за пределы root_dir
    result = read_tool.invoke({"file_path": "../../../etc/passwd"})

    if "Access denied" in result or "Error" in result:
        print(f"✅ Защита работает: {result}")
    else:
        print(f"⚠️ УЯЗВИМОСТЬ! Получен доступ: {result}")

    import shutil
    shutil.rmtree(workspace)


# ============================================================================
# ЧАСТЬ 3: Python REPL (Code Interpreter)
# ============================================================================

def demo_python_repl():
    """
    Python REPL — выполнение кода агентом.

    ВНИМАНИЕ: Это потенциально опасно! Используйте sandbox в production.
    """
    from langchain_experimental.tools import PythonREPLTool

    python_repl = PythonREPLTool()

    # Простое вычисление
    result = python_repl.invoke("""
import math
radius = 5
area = math.pi * radius ** 2
print(f"Площадь круга: {area:.2f}")
""")
    print(f"Результат: {result}")

    return python_repl


def demo_safe_python_repl():
    """
    Более безопасный Python REPL с ограниченными модулями.

    В production рекомендуется Docker sandbox!
    """
    from langchain_experimental.utilities import PythonREPL
    import math
    import statistics
    import json

    # REPL с ограниченным набором модулей
    repl = PythonREPL(
        _globals={
            "math": math,
            "statistics": statistics,
            "json": json,
            # os, subprocess, и другие опасные модули НЕ доступны!
        },
        _locals={},
    )

    # Безопасное вычисление
    result = repl.run("print(math.sqrt(16))")
    print(f"sqrt(16) = {result}")

    # Попытка импортировать os будет заблокирована
    result = repl.run("import os; print(os.getcwd())")
    print(f"Попытка импорта os: {result}")  # Ошибка!

    return repl


def demo_docker_sandbox():
    """
    Пример выполнения кода в Docker-контейнере (sandbox).

    Это рекомендуемый подход для production!
    Требуется: pip install docker
    """
    import docker

    def run_code_in_sandbox(code: str, timeout: int = 30) -> str:
        """Выполняет Python-код в изолированном Docker-контейнере."""
        client = docker.from_env()

        try:
            result = client.containers.run(
                "python:3.11-slim",
                command=["python", "-c", code],
                remove=True,           # Удалить контейнер после выполнения
                mem_limit="256m",      # Лимит памяти
                cpu_period=100000,
                cpu_quota=50000,       # 50% CPU
                network_disabled=True, # Без сети!
                timeout=timeout,
            )
            return result.decode("utf-8")
        except docker.errors.ContainerError as e:
            return f"Ошибка: {e.stderr.decode('utf-8')}"
        except docker.errors.ImageNotFound:
            return "Ошибка: Docker образ python:3.11-slim не найден"
        except Exception as e:
            return f"Ошибка: {str(e)}"

    # Пример использования (закомментирован, требует Docker)
    # result = run_code_in_sandbox("print(2 + 2)")
    # print(f"Sandbox результат: {result}")

    return run_code_in_sandbox


# ============================================================================
# ЧАСТЬ 4: Shell-инструменты с белым списком
# ============================================================================

# Белый список разрешённых команд
ALLOWED_COMMANDS = {
    "ls": {
        "args": ["-la", "-l", "-a", "-h"],
        "description": "Список файлов в директории"
    },
    "cat": {
        "args": [],
        "description": "Показать содержимое файла"
    },
    "head": {
        "args": ["-n"],
        "description": "Показать начало файла"
    },
    "tail": {
        "args": ["-n", "-f"],
        "description": "Показать конец файла"
    },
    "wc": {
        "args": ["-l", "-w", "-c"],
        "description": "Подсчёт строк/слов/символов"
    },
    "grep": {
        "args": ["-i", "-n", "-r", "-v"],
        "description": "Поиск по содержимому"
    },
    "find": {
        "args": ["-name", "-type"],
        "description": "Поиск файлов"
    },
}


def safe_shell(command: str, working_dir: str = "/tmp") -> str:
    """
    Выполняет безопасные shell-команды из белого списка.

    Args:
        command: Команда для выполнения, например "ls -la"
        working_dir: Рабочая директория

    Returns:
        Вывод команды или сообщение об ошибке
    """
    try:
        parts = shlex.split(command)
    except ValueError as e:
        return f"Ошибка парсинга команды: {e}"

    if not parts:
        return "Пустая команда"

    cmd_name = parts[0]

    # Проверка команды
    if cmd_name not in ALLOWED_COMMANDS:
        return f"❌ Команда '{cmd_name}' не разрешена. Доступны: {list(ALLOWED_COMMANDS.keys())}"

    # Проверка аргументов
    allowed_args = ALLOWED_COMMANDS[cmd_name]["args"]
    for arg in parts[1:]:
        if arg.startswith("-"):
            # Проверяем каждый флаг
            for char in arg[1:]:
                if f"-{char}" not in allowed_args and arg not in allowed_args:
                    return f"❌ Аргумент '{arg}' не разрешён для '{cmd_name}'"

    # Выполняем команду
    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=working_dir
        )
        return result.stdout or result.stderr or "Команда выполнена"
    except subprocess.TimeoutExpired:
        return "⏰ Превышено время выполнения (30 сек)"
    except Exception as e:
        return f"Ошибка: {e}"


def create_safe_shell_tool():
    """Создаёт инструмент safe_shell для LangChain."""
    from langchain_core.tools import tool

    @tool
    def shell_command(command: str) -> str:
        """
        Выполняет безопасные shell-команды.

        Доступные команды: ls, cat, head, tail, wc, grep, find.

        Примеры:
        - "ls -la" — список файлов
        - "grep -i pattern file.txt" — поиск в файле
        - "head -n 10 log.txt" — первые 10 строк
        - "wc -l *.py" — подсчёт строк в Python файлах

        Args:
            command: Команда для выполнения
        """
        return safe_shell(command)

    return shell_command


def demo_safe_shell():
    """Демонстрация безопасного shell."""
    print("--- Safe Shell Demo ---")

    # Разрешённая команда
    result = safe_shell("ls -la")
    print(f"ls -la:\n{result}")

    # Запрещённая команда
    result = safe_shell("rm -rf /")
    print(f"rm -rf /: {result}")

    # Запрещённый аргумент
    result = safe_shell("ls --color=auto")  # --color не в белом списке
    print(f"ls --color=auto: {result}")


# ============================================================================
# ЧАСТЬ 5: Git-инструменты
# ============================================================================

def create_git_tools(repo_path: str):
    """Создаёт безопасные git-инструменты для конкретного репозитория."""
    from langchain_core.tools import tool

    @tool
    def git_status() -> str:
        """Показывает статус git-репозитория (изменённые файлы, ветка)."""
        result = subprocess.run(
            ["git", "status", "--porcelain", "-b"],
            capture_output=True,
            text=True,
            cwd=repo_path
        )
        return result.stdout or "Репозиторий чист"

    @tool
    def git_diff(file_path: str = "") -> str:
        """
        Показывает diff для файла или всего репозитория.

        Args:
            file_path: Путь к файлу (пустой = весь репозиторий)
        """
        cmd = ["git", "diff"]
        if file_path:
            cmd.append(file_path)
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_path)
        return result.stdout or "Нет изменений"

    @tool
    def git_log(n: int = 5) -> str:
        """
        Показывает последние коммиты.

        Args:
            n: Количество коммитов (по умолчанию 5)
        """
        result = subprocess.run(
            ["git", "log", f"-{n}", "--oneline"],
            capture_output=True,
            text=True,
            cwd=repo_path
        )
        return result.stdout or "История пуста"

    return [git_status, git_diff, git_log]


# ============================================================================
# ЧАСТЬ 6: Комбинирование Toolkit'ов
# ============================================================================

def create_research_agent_tools():
    """
    Создаёт набор инструментов для исследовательского агента.

    Комбинирует поиск, файлы, код.
    """
    from langchain_community.tools import DuckDuckGoSearchRun
    from langchain_community.agent_toolkits import FileManagementToolkit
    from langchain_experimental.tools import PythonREPLTool
    from langchain_core.tools import tool
    import tempfile

    tools = []

    # 1. Поисковый инструмент
    tools.append(DuckDuckGoSearchRun())

    # 2. Файловые инструменты (ограниченные)
    workspace = tempfile.mkdtemp(prefix="research_")
    file_toolkit = FileManagementToolkit(
        root_dir=workspace,
        selected_tools=["read_file", "write_file", "list_directory"]
    )
    tools.extend(file_toolkit.get_tools())

    # 3. Python REPL для вычислений
    tools.append(PythonREPLTool())

    # 4. Кастомные инструменты
    @tool
    def get_current_time() -> str:
        """Возвращает текущее время и дату."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tools.append(get_current_time)

    print(f"Создано {len(tools)} инструментов:")
    for t in tools:
        print(f"  - {t.name}: {t.description[:50]}...")

    return tools, workspace


# ============================================================================
# ЧАСТЬ 7: Создание собственного Toolkit
# ============================================================================

class JiraToolkit:
    """
    Пример собственного Toolkit для работы с Jira.

    В реальности использовал бы jira-python библиотеку.
    """

    def __init__(
        self,
        base_url: str,
        api_token: str,
        project_key: str,
        selected_tools: List[str] | None = None
    ):
        self.base_url = base_url
        self.api_token = api_token
        self.project_key = project_key
        self.selected_tools = selected_tools or ["search", "get_issue"]

    def get_tools(self):
        """Возвращает список инструментов Jira."""
        from langchain_core.tools import StructuredTool

        all_tools = {
            "search": self._create_search_tool(),
            "get_issue": self._create_get_issue_tool(),
            "create_issue": self._create_create_issue_tool(),
        }

        return [all_tools[name] for name in self.selected_tools if name in all_tools]

    def _create_search_tool(self):
        from langchain_core.tools import StructuredTool

        class JiraSearchInput(BaseModel):
            jql: str = Field(description="JQL-запрос для поиска")

        def search_jira(jql: str) -> str:
            """Заглушка поиска в Jira."""
            return f"Найдено 5 задач по запросу: {jql}"

        return StructuredTool.from_function(
            func=search_jira,
            name="jira_search",
            description="Поиск задач в Jira по JQL-запросу",
            args_schema=JiraSearchInput,
        )

    def _create_get_issue_tool(self):
        from langchain_core.tools import StructuredTool

        class JiraGetInput(BaseModel):
            issue_key: str = Field(description="Ключ задачи, например PROJ-123")

        def get_issue(issue_key: str) -> str:
            """Заглушка получения задачи."""
            return f"Задача {issue_key}: В работе, Исполнитель: John Doe"

        return StructuredTool.from_function(
            func=get_issue,
            name="jira_get_issue",
            description="Получает информацию о задаче по ключу",
            args_schema=JiraGetInput,
        )

    def _create_create_issue_tool(self):
        from langchain_core.tools import StructuredTool

        class JiraCreateInput(BaseModel):
            summary: str = Field(description="Заголовок задачи")
            description: str = Field(description="Описание задачи")
            issue_type: str = Field(default="Task", description="Тип: Task, Bug, Story")

        def create_issue(summary: str, description: str, issue_type: str = "Task") -> str:
            """Заглушка создания задачи."""
            return f"Создана задача {self.project_key}-123: {summary}"

        return StructuredTool.from_function(
            func=create_issue,
            name="jira_create_issue",
            description="Создаёт новую задачу в Jira",
            args_schema=JiraCreateInput,
        )


def demo_custom_toolkit():
    """Демонстрация собственного Toolkit."""
    # Только читающие операции
    jira = JiraToolkit(
        base_url="https://example.atlassian.net",
        api_token="secret",
        project_key="PROJ",
        selected_tools=["search", "get_issue"]  # Без create!
    )

    tools = jira.get_tools()
    print(f"Jira инструменты: {[t.name for t in tools]}")

    # Тестируем
    search_tool = tools[0]
    result = search_tool.invoke({"jql": "project = PROJ AND status = Open"})
    print(f"Результат поиска: {result}")

    return jira


# ============================================================================
# ДЕМОНСТРАЦИЯ
# ============================================================================

def demo():
    """Запуск всех демонстраций."""
    print("=" * 60)
    print("TOOLKITS AND INTEGRATIONS (Лекция 4.3)")
    print("=" * 60)

    # --- DuckDuckGo (бесплатный) ---
    print("\n--- DuckDuckGo Search ---")
    try:
        demo_duckduckgo_search()
    except ImportError:
        print("duckduckgo-search не установлен")

    # --- File Management ---
    print("\n--- File Management Toolkit ---")
    try:
        demo_file_management_toolkit()
    except ImportError:
        print("langchain-community не установлен")

    # --- File Security ---
    print("\n--- File Security Demo ---")
    try:
        demo_file_security()
    except ImportError:
        print("langchain-community не установлен")

    # --- Python REPL ---
    print("\n--- Python REPL ---")
    try:
        demo_python_repl()
    except ImportError:
        print("langchain-experimental не установлен")

    # --- Safe Python REPL ---
    print("\n--- Safe Python REPL ---")
    try:
        demo_safe_python_repl()
    except ImportError:
        print("langchain-experimental не установлен")

    # --- Safe Shell ---
    print("\n--- Safe Shell ---")
    demo_safe_shell()

    # --- Custom Toolkit ---
    print("\n--- Custom Jira Toolkit ---")
    try:
        demo_custom_toolkit()
    except ImportError:
        print("langchain-core не установлен")

    # --- Combined Tools ---
    print("\n--- Research Agent Tools ---")
    try:
        tools, workspace = create_research_agent_tools()
        import shutil
        shutil.rmtree(workspace)  # Cleanup
    except ImportError as e:
        print(f"Некоторые пакеты не установлены: {e}")

    print("\n" + "=" * 60)
    print("Для полной демонстрации установите:")
    print("  pip install langchain-community langchain-experimental")
    print("  pip install duckduckgo-search tavily-python")
    print("=" * 60)


if __name__ == "__main__":
    demo()
