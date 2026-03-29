"""
Примеры к лекции 4.7: Model Context Protocol (MCP)

Демонстрация архитектуры MCP:
- Host, Client, Server
- Tools, Resources, Prompts
- Транспорты (stdio, Streamable HTTP)
- Создание MCP сервера

Автор: AI Assistant
Лекция: 4.7 Model Context Protocol (MCP)
"""

import json
import asyncio
from typing import Optional, List, Dict, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
import uuid


# ============================================================================
# ЧАСТЬ 1: ОСНОВНЫЕ КОНЦЕПЦИИ MCP
# ============================================================================

print("=" * 70)
print("ЧАСТЬ 1: ОСНОВНЫЕ КОНЦЕПЦИИ MCP")
print("=" * 70)

print("""
Model Context Protocol (MCP) - открытый протокол для стандартизации
взаимодействия между AI-приложениями и источниками данных/инструментами.

Архитектура MCP:

┌─────────────────────────────────────────────────────┐
│                         HOST                        │
│        (Claude Desktop, IDE, AI Application)        │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   CLIENT    │  │   CLIENT    │  │   CLIENT    │  │
│  │  (Session)  │  │  (Session)  │  │  (Session)  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
└─────────┼────────────────┼────────────────┼─────────┘
          │                │                │
          ▼                ▼                ▼
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │  SERVER   │    │  SERVER   │    │  SERVER   │
    │ (Files)   │    │ (GitHub)  │    │ (Database)│
    └───────────┘    └───────────┘    └───────────┘

Три типа примитивов:
1. Tools   - функции, которые LLM может вызывать
2. Resources - данные, которые можно читать
3. Prompts - готовые шаблоны промптов
""")


# ============================================================================
# ЧАСТЬ 2: БАЗОВЫЕ ТИПЫ MCP
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 2: БАЗОВЫЕ ТИПЫ MCP")
print("=" * 70)


@dataclass
class MCPTool:
    """Определение инструмента MCP"""
    name: str
    description: str
    input_schema: dict
    handler: Optional[Callable] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class MCPResource:
    """Определение ресурса MCP"""
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"

    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


@dataclass
class MCPResourceTemplate:
    """Шаблон URI для динамических ресурсов"""
    uri_template: str
    name: str
    description: str
    mime_type: str = "text/plain"

    def to_dict(self) -> dict:
        return {
            "uriTemplate": self.uri_template,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


@dataclass
class MCPPrompt:
    """Определение промпта MCP"""
    name: str
    description: str
    arguments: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments
        }


@dataclass
class MCPMessage:
    """Сообщение MCP протокола"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[dict] = None
    result: Optional[Any] = None
    error: Optional[dict] = None

    def to_dict(self) -> dict:
        msg = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            msg["id"] = self.id
        if self.method is not None:
            msg["method"] = self.method
        if self.params is not None:
            msg["params"] = self.params
        if self.result is not None:
            msg["result"] = self.result
        if self.error is not None:
            msg["error"] = self.error
        return msg

    @classmethod
    def request(cls, method: str, params: dict = None, id: str = None) -> "MCPMessage":
        return cls(
            id=id or str(uuid.uuid4()),
            method=method,
            params=params or {}
        )

    @classmethod
    def response(cls, id: str, result: Any) -> "MCPMessage":
        return cls(id=id, result=result)

    @classmethod
    def error_response(cls, id: str, code: int, message: str) -> "MCPMessage":
        return cls(id=id, error={"code": code, "message": message})


# Демонстрация типов
print("\nПример MCPTool:")
weather_tool = MCPTool(
    name="get_weather",
    description="Получить текущую погоду в городе",
    input_schema={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Название города"},
            "units": {"type": "string", "enum": ["metric", "imperial"]}
        },
        "required": ["city"]
    }
)
print(json.dumps(weather_tool.to_dict(), indent=2, ensure_ascii=False))

print("\nПример MCPResource:")
config_resource = MCPResource(
    uri="file:///config/settings.json",
    name="Application Settings",
    description="Конфигурация приложения",
    mime_type="application/json"
)
print(json.dumps(config_resource.to_dict(), indent=2, ensure_ascii=False))

print("\nПример MCPPrompt:")
code_review_prompt = MCPPrompt(
    name="code_review",
    description="Промпт для ревью кода",
    arguments=[
        {"name": "language", "description": "Язык программирования", "required": True},
        {"name": "focus", "description": "На что обратить внимание", "required": False}
    ]
)
print(json.dumps(code_review_prompt.to_dict(), indent=2, ensure_ascii=False))


# ============================================================================
# ЧАСТЬ 3: MCP SERVER
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 3: MCP SERVER")
print("=" * 70)


class MCPServer:
    """
    Базовая реализация MCP сервера.
    Обрабатывает JSON-RPC сообщения и предоставляет tools, resources, prompts.
    """

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = ""
    ):
        self.name = name
        self.version = version
        self.description = description

        self._tools: Dict[str, MCPTool] = {}
        self._resources: Dict[str, MCPResource] = {}
        self._resource_templates: List[MCPResourceTemplate] = []
        self._prompts: Dict[str, MCPPrompt] = {}

        # Обработчики
        self._tool_handlers: Dict[str, Callable] = {}
        self._resource_handlers: Dict[str, Callable] = {}
        self._prompt_handlers: Dict[str, Callable] = {}

    # === Регистрация инструментов ===

    def tool(self, name: str = None, description: str = ""):
        """Декоратор для регистрации инструмента"""
        def decorator(func):
            tool_name = name or func.__name__

            # Извлекаем схему из аннотаций функции
            input_schema = self._extract_schema(func)

            tool = MCPTool(
                name=tool_name,
                description=description or func.__doc__ or "",
                input_schema=input_schema,
                handler=func
            )

            self._tools[tool_name] = tool
            self._tool_handlers[tool_name] = func
            return func

        return decorator

    def _extract_schema(self, func: Callable) -> dict:
        """Извлечение JSON Schema из аннотаций функции"""
        import inspect
        sig = inspect.signature(func)

        properties = {}
        required = []

        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_type = param.annotation
            json_type = type_mapping.get(param_type, "string")

            properties[param_name] = {"type": json_type}

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    # === Регистрация ресурсов ===

    def resource(self, uri: str, name: str = "", mime_type: str = "text/plain"):
        """Декоратор для регистрации ресурса"""
        def decorator(func):
            resource_name = name or func.__name__
            resource = MCPResource(
                uri=uri,
                name=resource_name,
                description=func.__doc__ or "",
                mime_type=mime_type
            )
            self._resources[uri] = resource
            self._resource_handlers[uri] = func
            return func
        return decorator

    def resource_template(
        self,
        uri_template: str,
        name: str = "",
        mime_type: str = "text/plain"
    ):
        """Декоратор для регистрации шаблона ресурса"""
        def decorator(func):
            template = MCPResourceTemplate(
                uri_template=uri_template,
                name=name or func.__name__,
                description=func.__doc__ or "",
                mime_type=mime_type
            )
            self._resource_templates.append(template)
            # Храним обработчик с шаблоном как ключом
            self._resource_handlers[uri_template] = func
            return func
        return decorator

    # === Регистрация промптов ===

    def prompt(self, name: str = None, arguments: List[dict] = None):
        """Декоратор для регистрации промпта"""
        def decorator(func):
            prompt_name = name or func.__name__
            prompt = MCPPrompt(
                name=prompt_name,
                description=func.__doc__ or "",
                arguments=arguments or []
            )
            self._prompts[prompt_name] = prompt
            self._prompt_handlers[prompt_name] = func
            return func
        return decorator

    # === Обработка запросов ===

    async def handle_message(self, message: dict) -> dict:
        """Обработка входящего JSON-RPC сообщения"""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")

        try:
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_list_tools()
            elif method == "tools/call":
                result = await self._handle_call_tool(params)
            elif method == "resources/list":
                result = await self._handle_list_resources()
            elif method == "resources/read":
                result = await self._handle_read_resource(params)
            elif method == "prompts/list":
                result = await self._handle_list_prompts()
            elif method == "prompts/get":
                result = await self._handle_get_prompt(params)
            else:
                return MCPMessage.error_response(
                    msg_id, -32601, f"Method not found: {method}"
                ).to_dict()

            return MCPMessage.response(msg_id, result).to_dict()

        except Exception as e:
            return MCPMessage.error_response(
                msg_id, -32603, str(e)
            ).to_dict()

    async def _handle_initialize(self, params: dict) -> dict:
        """Обработка initialize"""
        return {
            "protocolVersion": "2025-11-25",
            "serverInfo": {
                "name": self.name,
                "version": self.version
            },
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True}
            }
        }

    async def _handle_list_tools(self) -> dict:
        """Получить список инструментов"""
        return {
            "tools": [tool.to_dict() for tool in self._tools.values()]
        }

    async def _handle_call_tool(self, params: dict) -> dict:
        """Вызов инструмента"""
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name not in self._tool_handlers:
            raise ValueError(f"Tool not found: {name}")

        handler = self._tool_handlers[name]

        # Вызываем обработчик
        if asyncio.iscoroutinefunction(handler):
            result = await handler(**arguments)
        else:
            result = handler(**arguments)

        return {
            "content": [
                {"type": "text", "text": str(result)}
            ]
        }

    async def _handle_list_resources(self) -> dict:
        """Получить список ресурсов"""
        resources = [r.to_dict() for r in self._resources.values()]
        templates = [t.to_dict() for t in self._resource_templates]

        return {
            "resources": resources,
            "resourceTemplates": templates
        }

    async def _handle_read_resource(self, params: dict) -> dict:
        """Чтение ресурса"""
        uri = params.get("uri")

        # Сначала ищем точное совпадение
        if uri in self._resource_handlers:
            handler = self._resource_handlers[uri]
            if asyncio.iscoroutinefunction(handler):
                content = await handler()
            else:
                content = handler()

            return {
                "contents": [
                    {"uri": uri, "text": content}
                ]
            }

        # Потом проверяем шаблоны
        for template in self._resource_templates:
            # Простой matching (в реальности нужен URI template parser)
            if self._match_template(template.uri_template, uri):
                handler = self._resource_handlers[template.uri_template]
                # Извлекаем параметры из URI
                params = self._extract_params(template.uri_template, uri)

                if asyncio.iscoroutinefunction(handler):
                    content = await handler(**params)
                else:
                    content = handler(**params)

                return {
                    "contents": [
                        {"uri": uri, "text": content}
                    ]
                }

        raise ValueError(f"Resource not found: {uri}")

    def _match_template(self, template: str, uri: str) -> bool:
        """Проверка соответствия URI шаблону"""
        # Упрощённая реализация
        import re
        pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', template)
        return bool(re.match(f"^{pattern}$", uri))

    def _extract_params(self, template: str, uri: str) -> dict:
        """Извлечение параметров из URI по шаблону"""
        import re
        pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', template)
        match = re.match(f"^{pattern}$", uri)
        return match.groupdict() if match else {}

    async def _handle_list_prompts(self) -> dict:
        """Получить список промптов"""
        return {
            "prompts": [p.to_dict() for p in self._prompts.values()]
        }

    async def _handle_get_prompt(self, params: dict) -> dict:
        """Получить промпт"""
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name not in self._prompt_handlers:
            raise ValueError(f"Prompt not found: {name}")

        handler = self._prompt_handlers[name]

        if asyncio.iscoroutinefunction(handler):
            messages = await handler(**arguments)
        else:
            messages = handler(**arguments)

        return {"messages": messages}


# ============================================================================
# ЧАСТЬ 4: ПРИМЕР MCP СЕРВЕРА - FILE SYSTEM
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 4: ПРИМЕР MCP СЕРВЕРА - FILE SYSTEM")
print("=" * 70)


# Создаём сервер
fs_server = MCPServer(
    name="filesystem-server",
    version="1.0.0",
    description="MCP сервер для работы с файловой системой"
)


# Регистрируем инструменты
@fs_server.tool(name="read_file", description="Читает содержимое файла")
def read_file(path: str) -> str:
    """Читает файл по указанному пути"""
    # Симуляция чтения файла
    return f"[Simulated content of {path}]"


@fs_server.tool(name="write_file", description="Записывает данные в файл")
def write_file(path: str, content: str) -> str:
    """Записывает контент в файл"""
    return f"Written {len(content)} bytes to {path}"


@fs_server.tool(name="list_directory", description="Получает список файлов в директории")
def list_directory(path: str) -> str:
    """Список файлов в директории"""
    # Симуляция
    files = ["file1.txt", "file2.py", "folder/"]
    return json.dumps(files)


# Регистрируем ресурсы
@fs_server.resource(
    uri="file:///workspace/README.md",
    name="README",
    mime_type="text/markdown"
)
def get_readme():
    """Содержимое README файла"""
    return "# Project\n\nThis is a sample project."


@fs_server.resource_template(
    uri_template="file:///workspace/{filename}",
    name="Workspace File",
    mime_type="text/plain"
)
def get_workspace_file(filename: str):
    """Чтение файла из workspace"""
    return f"[Content of {filename}]"


# Регистрируем промпты
@fs_server.prompt(
    name="summarize_file",
    arguments=[
        {"name": "path", "description": "Путь к файлу", "required": True}
    ]
)
def summarize_file_prompt(path: str):
    """Промпт для суммаризации файла"""
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"Пожалуйста, прочитай файл {path} и создай краткое описание его содержимого."
            }
        }
    ]


# Тестирование сервера
async def test_fs_server():
    print("\nТестирование FileSystem сервера:")

    # Initialize
    init_response = await fs_server.handle_message({
        "jsonrpc": "2.0",
        "id": "1",
        "method": "initialize",
        "params": {"protocolVersion": "2025-11-25"}
    })
    print(f"\n1. Initialize: {init_response['result']['serverInfo']}")

    # List tools
    tools_response = await fs_server.handle_message({
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/list"
    })
    tools = tools_response['result']['tools']
    print(f"\n2. Tools ({len(tools)}):")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")

    # Call tool
    call_response = await fs_server.handle_message({
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tools/call",
        "params": {
            "name": "read_file",
            "arguments": {"path": "/etc/config.json"}
        }
    })
    print(f"\n3. Call read_file: {call_response['result']['content'][0]['text']}")

    # List resources
    resources_response = await fs_server.handle_message({
        "jsonrpc": "2.0",
        "id": "4",
        "method": "resources/list"
    })
    resources = resources_response['result']
    print(f"\n4. Resources: {len(resources['resources'])} static, {len(resources['resourceTemplates'])} templates")

    # Read resource
    read_response = await fs_server.handle_message({
        "jsonrpc": "2.0",
        "id": "5",
        "method": "resources/read",
        "params": {"uri": "file:///workspace/README.md"}
    })
    print(f"\n5. Read README: {read_response['result']['contents'][0]['text'][:50]}...")

    # List prompts
    prompts_response = await fs_server.handle_message({
        "jsonrpc": "2.0",
        "id": "6",
        "method": "prompts/list"
    })
    prompts = prompts_response['result']['prompts']
    print(f"\n6. Prompts: {[p['name'] for p in prompts]}")


# Запускаем тест
asyncio.run(test_fs_server())


# ============================================================================
# ЧАСТЬ 5: MCP CLIENT
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 5: MCP CLIENT")
print("=" * 70)


class MCPClient:
    """
    Клиент MCP для подключения к серверам.
    """

    def __init__(self, server: MCPServer):
        self.server = server
        self.server_info = None
        self.capabilities = None
        self._request_id = 0

    def _next_id(self) -> str:
        self._request_id += 1
        return str(self._request_id)

    async def connect(self) -> dict:
        """Подключение к серверу"""
        response = await self.server.handle_message({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "clientInfo": {
                    "name": "example-client",
                    "version": "1.0.0"
                }
            }
        })

        result = response.get("result", {})
        self.server_info = result.get("serverInfo")
        self.capabilities = result.get("capabilities")

        return result

    async def list_tools(self) -> List[dict]:
        """Получить список доступных инструментов"""
        response = await self.server.handle_message({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list"
        })
        return response.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: dict = None) -> dict:
        """Вызвать инструмент"""
        response = await self.server.handle_message({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments or {}
            }
        })
        return response.get("result", {})

    async def list_resources(self) -> dict:
        """Получить список ресурсов"""
        response = await self.server.handle_message({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "resources/list"
        })
        return response.get("result", {})

    async def read_resource(self, uri: str) -> dict:
        """Прочитать ресурс"""
        response = await self.server.handle_message({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "resources/read",
            "params": {"uri": uri}
        })
        return response.get("result", {})

    async def list_prompts(self) -> List[dict]:
        """Получить список промптов"""
        response = await self.server.handle_message({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "prompts/list"
        })
        return response.get("result", {}).get("prompts", [])

    async def get_prompt(self, name: str, arguments: dict = None) -> dict:
        """Получить промпт"""
        response = await self.server.handle_message({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "prompts/get",
            "params": {
                "name": name,
                "arguments": arguments or {}
            }
        })
        return response.get("result", {})


# Демонстрация клиента
async def demo_client():
    print("\nДемонстрация MCP Client:")

    client = MCPClient(fs_server)

    # Подключаемся
    info = await client.connect()
    print(f"\n1. Подключено к серверу: {info['serverInfo']['name']}")

    # Получаем и вызываем инструмент
    tools = await client.list_tools()
    print(f"\n2. Доступные инструменты: {[t['name'] for t in tools]}")

    result = await client.call_tool("list_directory", {"path": "/home"})
    print(f"\n3. Результат list_directory: {result['content'][0]['text']}")

    # Читаем ресурс
    resources = await client.list_resources()
    print(f"\n4. Ресурсов: {len(resources.get('resources', []))}")

    content = await client.read_resource("file:///workspace/README.md")
    print(f"\n5. README содержимое: {content['contents'][0]['text'][:30]}...")


asyncio.run(demo_client())


# ============================================================================
# ЧАСТЬ 6: ПРИМЕР - АНАЛИТИЧЕСКИЙ MCP СЕРВЕР
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 6: ПРИМЕР - АНАЛИТИЧЕСКИЙ MCP СЕРВЕР")
print("=" * 70)


# Создаём аналитический сервер
analytics_server = MCPServer(
    name="analytics-server",
    version="1.0.0",
    description="MCP сервер для аналитики данных"
)

# Симуляция данных
SAMPLE_DATA = {
    "sales": [
        {"month": "Jan", "revenue": 10000, "units": 100},
        {"month": "Feb", "revenue": 12000, "units": 120},
        {"month": "Mar", "revenue": 15000, "units": 150},
    ],
    "users": [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False},
        {"id": 3, "name": "Charlie", "active": True},
    ]
}


@analytics_server.tool(
    name="query_data",
    description="Выполняет запрос к данным"
)
def query_data(dataset: str, filter_field: str = None, filter_value: str = None) -> str:
    """Запрос к датасету с опциональной фильтрацией"""
    if dataset not in SAMPLE_DATA:
        return json.dumps({"error": f"Dataset not found: {dataset}"})

    data = SAMPLE_DATA[dataset]

    if filter_field and filter_value:
        data = [
            row for row in data
            if str(row.get(filter_field)) == filter_value
        ]

    return json.dumps(data, ensure_ascii=False)


@analytics_server.tool(
    name="calculate_stats",
    description="Вычисляет статистику по числовому полю"
)
def calculate_stats(dataset: str, field: str) -> str:
    """Вычисление min, max, avg, sum по полю"""
    if dataset not in SAMPLE_DATA:
        return json.dumps({"error": f"Dataset not found: {dataset}"})

    values = [row.get(field, 0) for row in SAMPLE_DATA[dataset] if isinstance(row.get(field), (int, float))]

    if not values:
        return json.dumps({"error": f"No numeric values in field: {field}"})

    stats = {
        "field": field,
        "count": len(values),
        "sum": sum(values),
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values)
    }

    return json.dumps(stats)


@analytics_server.tool(
    name="run_python",
    description="Выполняет Python код для анализа данных"
)
def run_python(code: str) -> str:
    """Выполнение Python кода в sandbox"""
    # ВАЖНО: В реальности нужен безопасный sandbox!
    # Это симуляция для демонстрации

    safe_globals = {
        "data": SAMPLE_DATA,
        "sum": sum,
        "len": len,
        "min": min,
        "max": max,
        "sorted": sorted,
        "list": list,
        "dict": dict,
    }

    try:
        # Очень упрощённое выполнение
        result = eval(code, safe_globals)
        return json.dumps({"result": result}, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@analytics_server.resource(
    uri="data://datasets",
    name="Available Datasets",
    mime_type="application/json"
)
def list_datasets():
    """Список доступных датасетов"""
    return json.dumps({
        "datasets": list(SAMPLE_DATA.keys()),
        "schemas": {
            name: list(data[0].keys()) if data else []
            for name, data in SAMPLE_DATA.items()
        }
    })


@analytics_server.prompt(
    name="analyze_dataset",
    arguments=[
        {"name": "dataset", "description": "Название датасета", "required": True},
        {"name": "question", "description": "Вопрос для анализа", "required": True}
    ]
)
def analyze_prompt(dataset: str, question: str):
    """Промпт для анализа данных"""
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Проанализируй датасет "{dataset}" и ответь на вопрос: {question}

Используй доступные инструменты:
1. query_data - для получения данных
2. calculate_stats - для статистики
3. run_python - для сложных вычислений

Предоставь структурированный ответ с выводами."""
            }
        }
    ]


# Тестирование аналитического сервера
async def test_analytics():
    print("\nТестирование Analytics сервера:")

    client = MCPClient(analytics_server)
    await client.connect()

    # Список датасетов
    datasets = await client.read_resource("data://datasets")
    print(f"\n1. Датасеты: {datasets['contents'][0]['text']}")

    # Запрос данных
    result = await client.call_tool("query_data", {"dataset": "sales"})
    print(f"\n2. Sales данные: {result['content'][0]['text']}")

    # Статистика
    stats = await client.call_tool("calculate_stats", {
        "dataset": "sales",
        "field": "revenue"
    })
    print(f"\n3. Статистика revenue: {stats['content'][0]['text']}")

    # Python код
    python_result = await client.call_tool("run_python", {
        "code": "sum([row['revenue'] for row in data['sales']])"
    })
    print(f"\n4. Python расчёт: {python_result['content'][0]['text']}")

    # Промпт
    prompt = await client.get_prompt("analyze_dataset", {
        "dataset": "sales",
        "question": "Какой месяц был самым прибыльным?"
    })
    print(f"\n5. Промпт создан: {len(prompt['messages'])} сообщений")


asyncio.run(test_analytics())


# ============================================================================
# ЧАСТЬ 7: ТРАНСПОРТЫ MCP
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 7: ТРАНСПОРТЫ MCP")
print("=" * 70)


class Transport(ABC):
    """Абстрактный транспорт для MCP"""

    @abstractmethod
    async def send(self, message: dict) -> None:
        """Отправка сообщения"""
        pass

    @abstractmethod
    async def receive(self) -> dict:
        """Получение сообщения"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Закрытие соединения"""
        pass


class StdioTransport(Transport):
    """
    Транспорт через stdin/stdout.
    Используется для локальных MCP серверов.
    """

    def __init__(self):
        self._buffer = []

    async def send(self, message: dict) -> None:
        """Отправка в stdout"""
        json_str = json.dumps(message)
        # В реальности: print(json_str, flush=True)
        print(f"  [STDIO OUT] {json_str[:50]}...")
        self._buffer.append(message)

    async def receive(self) -> dict:
        """Чтение из stdin"""
        # В реальности: line = sys.stdin.readline()
        if self._buffer:
            return self._buffer.pop(0)
        return {}

    async def close(self) -> None:
        """Закрытие"""
        self._buffer.clear()


class StreamableHTTPTransport(Transport):
    """
    Транспорт через Streamable HTTP.
    Используется для удалённых MCP серверов.
    """

    def __init__(self, url: str):
        self.url = url
        self._messages = []

    async def send(self, message: dict) -> None:
        """Отправка POST запроса"""
        print(f"  [HTTP POST] {self.url}")
        print(f"  [HTTP DATA] {json.dumps(message)[:50]}...")
        # В реальности: httpx POST request

    async def receive(self) -> dict:
        """Получение через HTTP stream"""
        # В реальности: async for chunk in response.aiter_lines()
        print(f"  [HTTP RECEIVE] Waiting for response...")
        return {}

    async def close(self) -> None:
        """Закрытие соединения"""
        print(f"  [HTTP CLOSE] {self.url}")


print("\nПримеры транспортов:")

print("\n1. Stdio транспорт (локальный):")
stdio = StdioTransport()
asyncio.run(stdio.send({"jsonrpc": "2.0", "method": "initialize"}))

print("\n2. Streamable HTTP транспорт (удалённый):")
http_transport = StreamableHTTPTransport("http://localhost:3000/mcp")
asyncio.run(http_transport.send({"jsonrpc": "2.0", "method": "tools/list"}))


# ============================================================================
# ЧАСТЬ 8: ИНТЕГРАЦИЯ С LANGCHAIN
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 8: ИНТЕГРАЦИЯ С LANGCHAIN")
print("=" * 70)


class MCPToolWrapper:
    """
    Обёртка MCP инструмента для использования в LangChain.
    """

    def __init__(self, client: MCPClient, tool_info: dict):
        self.client = client
        self.name = tool_info["name"]
        self.description = tool_info["description"]
        self.input_schema = tool_info.get("inputSchema", {})

    def to_langchain_tool(self) -> dict:
        """Конвертация в формат LangChain Tool"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema
            }
        }

    async def invoke(self, **kwargs) -> str:
        """Вызов инструмента"""
        result = await self.client.call_tool(self.name, kwargs)
        content = result.get("content", [])
        if content:
            return content[0].get("text", "")
        return ""


class MCPToolkit:
    """
    Toolkit для интеграции MCP серверов с LangChain.
    """

    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
        self._tools: Dict[str, MCPToolWrapper] = {}

    async def add_server(self, name: str, server: MCPServer) -> None:
        """Добавить MCP сервер"""
        client = MCPClient(server)
        await client.connect()
        self._clients[name] = client

        # Загружаем инструменты
        tools = await client.list_tools()
        for tool_info in tools:
            tool_name = f"{name}__{tool_info['name']}"
            self._tools[tool_name] = MCPToolWrapper(client, tool_info)

        print(f"  Добавлен сервер '{name}' с {len(tools)} инструментами")

    def get_tools(self) -> List[dict]:
        """Получить все инструменты в формате LangChain"""
        return [tool.to_langchain_tool() for tool in self._tools.values()]

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Вызов инструмента по имени"""
        if name not in self._tools:
            return f"Tool not found: {name}"
        return await self._tools[name].invoke(**arguments)


# Демонстрация интеграции
async def demo_langchain_integration():
    print("\nИнтеграция MCP с LangChain:")

    toolkit = MCPToolkit()

    # Добавляем серверы
    await toolkit.add_server("fs", fs_server)
    await toolkit.add_server("analytics", analytics_server)

    # Получаем все инструменты
    tools = toolkit.get_tools()
    print(f"\nВсего инструментов: {len(tools)}")
    for tool in tools:
        print(f"  - {tool['function']['name']}")

    # Вызываем инструмент
    result = await toolkit.call_tool("analytics__calculate_stats", {
        "dataset": "sales",
        "field": "units"
    })
    print(f"\nРезультат вызова: {result}")


asyncio.run(demo_langchain_integration())


# ============================================================================
# ДЕМО ФУНКЦИЯ
# ============================================================================

def demo():
    """
    Запуск всех демонстраций.
    """
    print("\n" + "=" * 70)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 70)

    print("""
    Изученные концепции:

    1. Архитектура MCP
       - Host, Client, Server
       - JSON-RPC 2.0 протокол
       - Capabilities negotiation

    2. Примитивы MCP
       - Tools - вызываемые функции
       - Resources - читаемые данные
       - Prompts - шаблоны промптов

    3. MCP Server
       - Регистрация инструментов через декораторы
       - Обработка JSON-RPC сообщений
       - Resource templates для динамических ресурсов

    4. MCP Client
       - Подключение к серверу
       - Вызов инструментов
       - Чтение ресурсов

    5. Транспорты
       - Stdio для локальных серверов
       - Streamable HTTP для удалённых серверов

    6. Интеграция с LangChain
       - MCPToolWrapper для совместимости
       - MCPToolkit для множества серверов

    Практические применения:
    - Стандартизация доступа к данным для AI
    - Подключение любых источников данных
    - Переиспользование серверов между приложениями
    - Безопасная изоляция доступа к ресурсам

    Пример запуска MCP сервера:
    ```bash
    # В Claude Desktop config:
    {
      "mcpServers": {
        "analytics": {
          "command": "python",
          "args": ["analytics_server.py"]
        }
      }
    }
    ```
    """)


if __name__ == "__main__":
    demo()
