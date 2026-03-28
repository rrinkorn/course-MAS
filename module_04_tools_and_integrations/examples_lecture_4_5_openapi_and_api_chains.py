"""
Примеры к лекции 4.5: OpenAPI и API Chains

Демонстрация интеграции с внешними API через OpenAPI спецификации,
создание API chains, авторизация и обработка ошибок.

Автор: AI Assistant
Лекция: 4.5 OpenAPI и API Chains
"""

import json
import time
import hashlib
import asyncio
from typing import Optional, Any, Dict, List, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from abc import ABC, abstractmethod
from enum import Enum
import yaml


# ============================================================================
# ЧАСТЬ 1: ЗАГРУЗКА И ПАРСИНГ OPENAPI СПЕЦИФИКАЦИЙ
# ============================================================================

print("=" * 70)
print("ЧАСТЬ 1: ЗАГРУЗКА И ПАРСИНГ OPENAPI СПЕЦИФИКАЦИЙ")
print("=" * 70)


# Пример OpenAPI спецификации для Weather API
WEATHER_API_SPEC = """
openapi: 3.0.0
info:
  title: Weather API
  description: API для получения данных о погоде
  version: 1.0.0
servers:
  - url: https://api.weather.example.com/v1
paths:
  /current:
    get:
      operationId: getCurrentWeather
      summary: Получить текущую погоду
      parameters:
        - name: city
          in: query
          required: true
          schema:
            type: string
          description: Название города
        - name: units
          in: query
          required: false
          schema:
            type: string
            enum: [metric, imperial]
            default: metric
          description: Единицы измерения
      responses:
        '200':
          description: Успешный ответ
          content:
            application/json:
              schema:
                type: object
                properties:
                  city:
                    type: string
                  temperature:
                    type: number
                  humidity:
                    type: integer
                  conditions:
                    type: string
  /forecast:
    get:
      operationId: getForecast
      summary: Получить прогноз погоды
      parameters:
        - name: city
          in: query
          required: true
          schema:
            type: string
        - name: days
          in: query
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 7
            default: 3
      responses:
        '200':
          description: Прогноз погоды
"""


class OpenAPIParser:
    """Парсер OpenAPI спецификаций"""

    def __init__(self, spec: str | dict):
        if isinstance(spec, str):
            self.spec = yaml.safe_load(spec)
        else:
            self.spec = spec

    @property
    def info(self) -> dict:
        """Информация об API"""
        return self.spec.get("info", {})

    @property
    def servers(self) -> List[dict]:
        """Список серверов"""
        return self.spec.get("servers", [])

    @property
    def base_url(self) -> str:
        """Базовый URL первого сервера"""
        servers = self.servers
        return servers[0]["url"] if servers else ""

    def get_operations(self) -> List[dict]:
        """Получить все операции API"""
        operations = []

        for path, methods in self.spec.get("paths", {}).items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    operations.append({
                        "path": path,
                        "method": method.upper(),
                        "operation_id": details.get("operationId"),
                        "summary": details.get("summary"),
                        "parameters": details.get("parameters", []),
                        "request_body": details.get("requestBody"),
                        "responses": details.get("responses", {})
                    })

        return operations

    def get_operation_by_id(self, operation_id: str) -> Optional[dict]:
        """Найти операцию по ID"""
        for op in self.get_operations():
            if op["operation_id"] == operation_id:
                return op
        return None

    def to_tool_schema(self, operation: dict) -> dict:
        """Преобразовать операцию в JSON Schema для LLM"""
        properties = {}
        required = []

        for param in operation.get("parameters", []):
            param_name = param["name"]
            param_schema = param.get("schema", {})

            properties[param_name] = {
                "type": param_schema.get("type", "string"),
                "description": param.get("description", "")
            }

            if "enum" in param_schema:
                properties[param_name]["enum"] = param_schema["enum"]

            if param.get("required", False):
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": operation["operation_id"],
                "description": operation.get("summary", ""),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


# Демонстрация парсинга
parser = OpenAPIParser(WEATHER_API_SPEC)

print(f"\nAPI: {parser.info.get('title')}")
print(f"Version: {parser.info.get('version')}")
print(f"Base URL: {parser.base_url}")

print("\nДоступные операции:")
for op in parser.get_operations():
    print(f"  - {op['method']} {op['path']}: {op['summary']}")

# Преобразование в tool schema
print("\nJSON Schema для getCurrentWeather:")
current_weather_op = parser.get_operation_by_id("getCurrentWeather")
if current_weather_op:
    tool_schema = parser.to_tool_schema(current_weather_op)
    print(json.dumps(tool_schema, indent=2, ensure_ascii=False))


# ============================================================================
# ЧАСТЬ 2: АВТОРИЗАЦИЯ И АУТЕНТИФИКАЦИЯ
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 2: АВТОРИЗАЦИЯ И АУТЕНТИФИКАЦИЯ")
print("=" * 70)


class AuthType(Enum):
    """Типы авторизации"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"


@dataclass
class AuthConfig:
    """Конфигурация авторизации"""
    auth_type: AuthType
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    bearer_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    oauth_token: Optional[str] = None

    def get_headers(self) -> dict:
        """Получить заголовки авторизации"""
        headers = {}

        if self.auth_type == AuthType.API_KEY and self.api_key:
            headers[self.api_key_header] = self.api_key

        elif self.auth_type == AuthType.BEARER and self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"

        elif self.auth_type == AuthType.BASIC:
            import base64
            credentials = f"{self.username}:{self.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        elif self.auth_type == AuthType.OAUTH2 and self.oauth_token:
            headers["Authorization"] = f"Bearer {self.oauth_token}"

        return headers


class AuthProvider(ABC):
    """Абстрактный провайдер авторизации"""

    @abstractmethod
    def get_auth_headers(self) -> dict:
        """Получить заголовки авторизации"""
        pass

    @abstractmethod
    def refresh_if_needed(self) -> bool:
        """Обновить токен если нужно"""
        pass


class APIKeyAuth(AuthProvider):
    """Авторизация через API ключ"""

    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        self.api_key = api_key
        self.header_name = header_name

    def get_auth_headers(self) -> dict:
        return {self.header_name: self.api_key}

    def refresh_if_needed(self) -> bool:
        return True  # API ключ не истекает


class BearerTokenAuth(AuthProvider):
    """Авторизация через Bearer токен с обновлением"""

    def __init__(
        self,
        token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        refresh_callback: Optional[callable] = None
    ):
        self.token = token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.refresh_callback = refresh_callback

    def get_auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        # Обновляем за 5 минут до истечения
        return datetime.now() >= self.expires_at - timedelta(minutes=5)

    def refresh_if_needed(self) -> bool:
        if not self.is_expired():
            return True

        if not self.refresh_callback or not self.refresh_token:
            return False

        try:
            new_tokens = self.refresh_callback(self.refresh_token)
            self.token = new_tokens["access_token"]
            self.refresh_token = new_tokens.get("refresh_token", self.refresh_token)
            if "expires_in" in new_tokens:
                self.expires_at = datetime.now() + timedelta(seconds=new_tokens["expires_in"])
            return True
        except Exception as e:
            print(f"Ошибка обновления токена: {e}")
            return False


# Демонстрация различных типов авторизации
print("\n1. API Key авторизация:")
api_key_auth = APIKeyAuth("my-secret-api-key", "X-API-Key")
print(f"   Headers: {api_key_auth.get_auth_headers()}")

print("\n2. Bearer Token авторизация:")
bearer_auth = BearerTokenAuth(
    token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    expires_at=datetime.now() + timedelta(hours=1)
)
print(f"   Headers: {bearer_auth.get_auth_headers()}")
print(f"   Expired: {bearer_auth.is_expired()}")

print("\n3. Basic Auth:")
basic_config = AuthConfig(
    auth_type=AuthType.BASIC,
    username="user",
    password="password123"
)
print(f"   Headers: {basic_config.get_headers()}")


# ============================================================================
# ЧАСТЬ 3: ОБРАБОТКА ОШИБОК API
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 3: ОБРАБОТКА ОШИБОК API")
print("=" * 70)


class APIError(Exception):
    """Базовый класс для ошибок API"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[dict] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class RetryableError(APIError):
    """Ошибка, которую можно повторить"""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after  # Секунды до повтора


class PermanentError(APIError):
    """Постоянная ошибка (повтор не поможет)"""
    pass


class RateLimitError(RetryableError):
    """Превышен лимит запросов"""
    pass


class AuthenticationError(PermanentError):
    """Ошибка аутентификации"""
    pass


class ValidationError(PermanentError):
    """Ошибка валидации запроса"""
    pass


def classify_api_error(status_code: int, response_body: Optional[dict] = None) -> APIError:
    """Классификация ошибки API по статус-коду"""

    error_message = ""
    if response_body:
        error_message = response_body.get("error", {}).get("message", str(response_body))

    # 4xx - клиентские ошибки
    if status_code == 400:
        return ValidationError(
            f"Некорректный запрос: {error_message}",
            status_code=status_code,
            response_body=response_body
        )

    elif status_code == 401:
        return AuthenticationError(
            "Ошибка аутентификации: неверный или истекший токен",
            status_code=status_code,
            response_body=response_body
        )

    elif status_code == 403:
        return PermanentError(
            f"Доступ запрещён: {error_message}",
            status_code=status_code,
            response_body=response_body
        )

    elif status_code == 404:
        return PermanentError(
            f"Ресурс не найден: {error_message}",
            status_code=status_code,
            response_body=response_body
        )

    elif status_code == 429:
        retry_after = None
        if response_body:
            retry_after = response_body.get("retry_after")
        return RateLimitError(
            "Превышен лимит запросов",
            status_code=status_code,
            response_body=response_body,
            retry_after=retry_after
        )

    # 5xx - серверные ошибки (можно повторить)
    elif status_code >= 500:
        return RetryableError(
            f"Серверная ошибка ({status_code}): {error_message}",
            status_code=status_code,
            response_body=response_body
        )

    return APIError(
        f"Неизвестная ошибка ({status_code}): {error_message}",
        status_code=status_code,
        response_body=response_body
    )


# Демонстрация классификации ошибок
print("\nПримеры классификации ошибок:")

test_errors = [
    (400, {"error": {"message": "Invalid city parameter"}}),
    (401, {"error": {"message": "Token expired"}}),
    (429, {"error": {"message": "Too many requests"}, "retry_after": 60}),
    (500, {"error": {"message": "Internal server error"}}),
    (503, {"error": {"message": "Service unavailable"}}),
]

for status, body in test_errors:
    error = classify_api_error(status, body)
    error_type = type(error).__name__
    is_retryable = isinstance(error, RetryableError)
    print(f"  {status}: {error_type} (retryable: {is_retryable})")


# ============================================================================
# ЧАСТЬ 4: RETRY СТРАТЕГИИ
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 4: RETRY СТРАТЕГИИ")
print("=" * 70)


@dataclass
class RetryConfig:
    """Конфигурация повторных попыток"""
    max_retries: int = 3
    initial_delay: float = 1.0  # секунды
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True  # Добавлять случайность


class RetryStrategy(ABC):
    """Абстрактная стратегия повторных попыток"""

    @abstractmethod
    def get_delay(self, attempt: int, error: Optional[Exception] = None) -> float:
        """Получить задержку перед следующей попыткой"""
        pass

    @abstractmethod
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Определить, нужно ли повторять"""
        pass


class ExponentialBackoff(RetryStrategy):
    """Экспоненциальный backoff с jitter"""

    def __init__(self, config: RetryConfig):
        self.config = config

    def get_delay(self, attempt: int, error: Optional[Exception] = None) -> float:
        # Если есть retry_after от API - используем его
        if isinstance(error, RetryableError) and error.retry_after:
            return error.retry_after

        # Экспоненциальный рост
        delay = self.config.initial_delay * (self.config.exponential_base ** attempt)

        # Ограничиваем максимумом
        delay = min(delay, self.config.max_delay)

        # Добавляем jitter (±25%)
        if self.config.jitter:
            import random
            jitter = delay * 0.25 * (2 * random.random() - 1)
            delay += jitter

        return max(0, delay)

    def should_retry(self, attempt: int, error: Exception) -> bool:
        # Превышено число попыток
        if attempt >= self.config.max_retries:
            return False

        # Только RetryableError можно повторять
        return isinstance(error, RetryableError)


def with_retry(strategy: RetryStrategy):
    """Декоратор для автоматических повторных попыток"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(strategy.config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    if not strategy.should_retry(attempt, e):
                        raise

                    delay = strategy.get_delay(attempt, e)
                    print(f"  Попытка {attempt + 1} неудачна: {e}")
                    print(f"  Повтор через {delay:.2f} сек...")
                    time.sleep(delay)

            raise last_error

        return wrapper
    return decorator


# Демонстрация retry
print("\nЭкспоненциальный backoff:")
retry_config = RetryConfig(max_retries=5, initial_delay=1.0, exponential_base=2.0)
backoff = ExponentialBackoff(retry_config)

print("Задержки при последовательных неудачах:")
for attempt in range(5):
    delay = backoff.get_delay(attempt)
    print(f"  Попытка {attempt + 1}: {delay:.2f} сек")


# Пример с retry
retry_strategy = ExponentialBackoff(RetryConfig(max_retries=3))

call_count = 0

@with_retry(retry_strategy)
def unreliable_api_call():
    """Симуляция нестабильного API"""
    global call_count
    call_count += 1

    if call_count < 3:
        raise RetryableError(f"Сервер недоступен (попытка {call_count})", status_code=503)

    return {"status": "success", "data": "Hello!"}

print("\nТест retry механизма:")
try:
    result = unreliable_api_call()
    print(f"Успех после {call_count} попыток: {result}")
except Exception as e:
    print(f"Финальная ошибка: {e}")


# ============================================================================
# ЧАСТЬ 5: RATE LIMITING
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 5: RATE LIMITING")
print("=" * 70)


class RateLimiter:
    """Rate limiter с token bucket алгоритмом"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None
    ):
        self.rpm = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.tokens = float(self.burst_size)
        self.last_update = time.time()
        self._lock = asyncio.Lock() if asyncio else None

    def _refill(self):
        """Пополнить токены"""
        now = time.time()
        elapsed = now - self.last_update

        # Добавляем токены пропорционально прошедшему времени
        tokens_to_add = elapsed * (self.rpm / 60.0)
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_update = now

    def acquire(self, tokens: int = 1) -> float:
        """
        Получить токены для запроса.
        Возвращает время ожидания (0 если можно сразу).
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return 0.0

        # Вычисляем время ожидания
        tokens_needed = tokens - self.tokens
        wait_time = tokens_needed / (self.rpm / 60.0)
        return wait_time

    def wait_and_acquire(self, tokens: int = 1):
        """Подождать и получить токены"""
        wait_time = self.acquire(tokens)
        if wait_time > 0:
            print(f"  Rate limit: ожидание {wait_time:.2f} сек...")
            time.sleep(wait_time)
            self._refill()
            self.tokens -= tokens


class AdaptiveRateLimiter(RateLimiter):
    """Адаптивный rate limiter, учитывающий заголовки ответа"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.remaining_requests = None
        self.reset_time = None

    def update_from_headers(self, headers: dict):
        """Обновить лимиты из заголовков ответа"""
        # X-RateLimit-Remaining
        if "X-RateLimit-Remaining" in headers:
            self.remaining_requests = int(headers["X-RateLimit-Remaining"])
            self.tokens = min(self.tokens, self.remaining_requests)

        # X-RateLimit-Reset
        if "X-RateLimit-Reset" in headers:
            self.reset_time = datetime.fromtimestamp(int(headers["X-RateLimit-Reset"]))

    def acquire(self, tokens: int = 1) -> float:
        # Если знаем что лимит исчерпан
        if self.remaining_requests is not None and self.remaining_requests < tokens:
            if self.reset_time:
                wait_time = (self.reset_time - datetime.now()).total_seconds()
                return max(0, wait_time)

        return super().acquire(tokens)


# Демонстрация rate limiting
print("\nToken Bucket Rate Limiter (10 RPM):")
limiter = RateLimiter(requests_per_minute=10, burst_size=3)

for i in range(5):
    wait = limiter.acquire()
    if wait > 0:
        print(f"  Запрос {i+1}: нужно ждать {wait:.2f} сек")
    else:
        print(f"  Запрос {i+1}: выполнен сразу (токенов: {limiter.tokens:.1f})")


# ============================================================================
# ЧАСТЬ 6: TTL КЭШИРОВАНИЕ
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 6: TTL КЭШИРОВАНИЕ")
print("=" * 70)


@dataclass
class CacheEntry:
    """Запись в кэше"""
    value: Any
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        return datetime.now() >= self.expires_at


class TTLCache:
    """Кэш с TTL (Time To Live)"""

    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: Время жизни записей в секундах (по умолчанию 5 минут)
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}

    def _make_key(self, *args, **kwargs) -> str:
        """Создать ключ кэша из аргументов"""
        key_data = {"args": args, "kwargs": sorted(kwargs.items())}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        entry = self._cache.get(key)

        if entry is None:
            return None

        if entry.is_expired():
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Сохранить значение в кэш"""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)

        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    def invalidate(self, key: str):
        """Удалить запись из кэша"""
        self._cache.pop(key, None)

    def clear(self):
        """Очистить весь кэш"""
        self._cache.clear()

    def cleanup_expired(self):
        """Удалить все истекшие записи"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    def stats(self) -> dict:
        """Статистика кэша"""
        self.cleanup_expired()
        return {
            "total_entries": len(self._cache),
            "memory_estimate": sum(
                len(str(e.value)) for e in self._cache.values()
            )
        }


def cached(ttl: int = 300, cache: Optional[TTLCache] = None):
    """Декоратор для кэширования результатов"""
    _cache = cache or TTLCache(default_ttl=ttl)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = _cache._make_key(func.__name__, *args, **kwargs)

            # Проверяем кэш
            cached_value = _cache.get(key)
            if cached_value is not None:
                print(f"  [CACHE HIT] {func.__name__}")
                return cached_value

            # Выполняем функцию
            print(f"  [CACHE MISS] {func.__name__}")
            result = func(*args, **kwargs)

            # Сохраняем в кэш
            _cache.set(key, result, ttl)
            return result

        wrapper.cache = _cache
        wrapper.invalidate = lambda *args, **kwargs: _cache.invalidate(
            _cache._make_key(func.__name__, *args, **kwargs)
        )

        return wrapper
    return decorator


# Демонстрация кэширования
print("\nTTL Cache демонстрация:")

api_cache = TTLCache(default_ttl=60)

@cached(ttl=30, cache=api_cache)
def fetch_weather(city: str) -> dict:
    """Симуляция API запроса"""
    time.sleep(0.1)  # Имитация сетевой задержки
    return {"city": city, "temp": 20, "timestamp": datetime.now().isoformat()}

# Первый вызов - cache miss
print("\nПервый вызов (cache miss):")
result1 = fetch_weather("Moscow")
print(f"  Результат: {result1['city']}, temp={result1['temp']}")

# Второй вызов - cache hit
print("\nВторой вызов (cache hit):")
result2 = fetch_weather("Moscow")
print(f"  Результат: {result2['city']}, temp={result2['temp']}")

# Другой город - cache miss
print("\nДругой город (cache miss):")
result3 = fetch_weather("London")
print(f"  Результат: {result3['city']}, temp={result3['temp']}")

print(f"\nСтатистика кэша: {api_cache.stats()}")


# ============================================================================
# ЧАСТЬ 7: API CLIENT С ПОЛНЫМ ФУНКЦИОНАЛОМ
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 7: API CLIENT С ПОЛНЫМ ФУНКЦИОНАЛОМ")
print("=" * 70)


class APIClient:
    """
    Полнофункциональный API клиент с:
    - Авторизацией
    - Rate limiting
    - Кэшированием
    - Retry механизмом
    - Обработкой ошибок
    """

    def __init__(
        self,
        base_url: str,
        auth_provider: Optional[AuthProvider] = None,
        rate_limiter: Optional[RateLimiter] = None,
        cache: Optional[TTLCache] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.auth_provider = auth_provider
        self.rate_limiter = rate_limiter or RateLimiter()
        self.cache = cache or TTLCache()
        self.retry_strategy = ExponentialBackoff(
            retry_config or RetryConfig()
        )

        # Статистика
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "retries": 0,
            "errors": 0
        }

    def _get_headers(self) -> dict:
        """Получить заголовки запроса"""
        headers = {"Content-Type": "application/json"}

        if self.auth_provider:
            self.auth_provider.refresh_if_needed()
            headers.update(self.auth_provider.get_auth_headers())

        return headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        use_cache: bool = True,
        cache_ttl: int = 300
    ) -> dict:
        """Выполнить HTTP запрос (симуляция)"""

        url = f"{self.base_url}{endpoint}"
        cache_key = self.cache._make_key(method, url, params)

        # Проверяем кэш для GET запросов
        if method == "GET" and use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                self.stats["cache_hits"] += 1
                return cached

        # Rate limiting
        self.rate_limiter.wait_and_acquire()

        # Симуляция HTTP запроса
        self.stats["total_requests"] += 1
        headers = self._get_headers()

        # Симуляция ответа
        print(f"  >> {method} {url}")
        print(f"     Params: {params}")
        print(f"     Headers: {list(headers.keys())}")

        # Симулируем успешный ответ
        response = {
            "status": "success",
            "data": {
                "endpoint": endpoint,
                "params": params,
                "timestamp": datetime.now().isoformat()
            }
        }

        # Кэшируем GET запросы
        if method == "GET" and use_cache:
            self.cache.set(cache_key, response, cache_ttl)

        return response

    def get(self, endpoint: str, **kwargs) -> dict:
        """GET запрос"""
        return self._make_request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, data: dict, **kwargs) -> dict:
        """POST запрос"""
        return self._make_request("POST", endpoint, data=data, use_cache=False, **kwargs)

    def get_stats(self) -> dict:
        """Получить статистику клиента"""
        cache_stats = self.cache.stats()
        return {
            **self.stats,
            "cache_entries": cache_stats["total_entries"],
            "cache_hit_rate": (
                self.stats["cache_hits"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0 else 0
            )
        }


# Демонстрация API клиента
print("\nСоздание API клиента:")

client = APIClient(
    base_url="https://api.weather.example.com/v1",
    auth_provider=APIKeyAuth("demo-api-key"),
    rate_limiter=RateLimiter(requests_per_minute=60),
    cache=TTLCache(default_ttl=300),
    retry_config=RetryConfig(max_retries=3)
)

print("\nВыполнение запросов:")

# Запрос 1
print("\n1. Первый запрос (cache miss):")
result1 = client.get("/weather", params={"city": "Moscow"})

# Запрос 2 - тот же (cache hit)
print("\n2. Повторный запрос (cache hit):")
result2 = client.get("/weather", params={"city": "Moscow"})

# Запрос 3 - другие параметры
print("\n3. Другой город:")
result3 = client.get("/weather", params={"city": "London"})

# POST запрос (не кэшируется)
print("\n4. POST запрос:")
result4 = client.post("/feedback", data={"rating": 5})

print(f"\nСтатистика клиента: {client.get_stats()}")


# ============================================================================
# ЧАСТЬ 8: OPENAPI TOOLKIT ДЛЯ LANGCHAIN
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 8: OPENAPI TOOLKIT ДЛЯ LANGCHAIN")
print("=" * 70)


class OpenAPITool:
    """Инструмент на основе OpenAPI операции"""

    def __init__(
        self,
        operation: dict,
        client: APIClient,
        parser: OpenAPIParser
    ):
        self.operation = operation
        self.client = client
        self.parser = parser
        self.name = operation["operation_id"]
        self.description = operation.get("summary", "")

    def get_schema(self) -> dict:
        """Получить JSON Schema для LLM"""
        return self.parser.to_tool_schema(self.operation)

    def invoke(self, **kwargs) -> dict:
        """Вызвать API"""
        method = self.operation["method"]
        path = self.operation["path"]

        # Подготовка параметров
        query_params = {}
        path_params = {}
        body = None

        for param in self.operation.get("parameters", []):
            param_name = param["name"]
            param_in = param.get("in", "query")

            if param_name in kwargs:
                if param_in == "query":
                    query_params[param_name] = kwargs[param_name]
                elif param_in == "path":
                    path_params[param_name] = kwargs[param_name]

        # Подстановка path параметров
        for name, value in path_params.items():
            path = path.replace(f"{{{name}}}", str(value))

        # Выполнение запроса
        if method == "GET":
            return self.client.get(path, params=query_params)
        elif method == "POST":
            return self.client.post(path, data=body, params=query_params)

        return {"error": f"Unsupported method: {method}"}


class OpenAPIToolkit:
    """Toolkit из OpenAPI спецификации"""

    def __init__(self, spec: str | dict, client: APIClient):
        self.parser = OpenAPIParser(spec)
        self.client = client
        self._tools: Dict[str, OpenAPITool] = {}

        # Создаём инструменты для всех операций
        for operation in self.parser.get_operations():
            tool = OpenAPITool(operation, client, self.parser)
            self._tools[tool.name] = tool

    def get_tools(self) -> List[OpenAPITool]:
        """Получить все инструменты"""
        return list(self._tools.values())

    def get_tool(self, name: str) -> Optional[OpenAPITool]:
        """Получить инструмент по имени"""
        return self._tools.get(name)

    def get_tool_schemas(self) -> List[dict]:
        """Получить схемы всех инструментов для LLM"""
        return [tool.get_schema() for tool in self._tools.values()]

    def invoke(self, tool_name: str, **kwargs) -> dict:
        """Вызвать инструмент по имени"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {"error": f"Tool not found: {tool_name}"}
        return tool.invoke(**kwargs)


# Демонстрация OpenAPI Toolkit
print("\nСоздание OpenAPI Toolkit:")

toolkit = OpenAPIToolkit(
    spec=WEATHER_API_SPEC,
    client=client
)

print(f"\nДоступные инструменты:")
for tool in toolkit.get_tools():
    print(f"  - {tool.name}: {tool.description}")

print("\nJSON Schemas для LLM:")
for schema in toolkit.get_tool_schemas():
    print(f"  - {schema['function']['name']}")

print("\nВызов инструмента:")
result = toolkit.invoke("getCurrentWeather", city="Paris", units="metric")
print(f"  Результат: {json.dumps(result, indent=2)}")


# ============================================================================
# ЧАСТЬ 9: ПОЛНЫЙ ПРИМЕР - WEATHER AGENT
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 9: ПОЛНЫЙ ПРИМЕР - WEATHER AGENT")
print("=" * 70)


class WeatherAgent:
    """
    Агент для работы с Weather API.
    Демонстрирует полный цикл:
    1. Получение запроса от пользователя
    2. Выбор инструмента (имитация LLM)
    3. Вызов API через toolkit
    4. Формирование ответа
    """

    def __init__(self, toolkit: OpenAPIToolkit):
        self.toolkit = toolkit
        self.conversation_history = []

    def _select_tool(self, user_query: str) -> tuple[str, dict]:
        """
        Имитация выбора инструмента LLM.
        В реальности здесь был бы вызов LLM.
        """
        query_lower = user_query.lower()

        if "прогноз" in query_lower or "forecast" in query_lower:
            # Извлекаем город (упрощённо)
            city = "Moscow"  # По умолчанию
            for word in user_query.split():
                if word[0].isupper() and len(word) > 2:
                    city = word
                    break
            return "getForecast", {"city": city, "days": 5}

        else:
            # По умолчанию - текущая погода
            city = "Moscow"
            for word in user_query.split():
                if word[0].isupper() and len(word) > 2:
                    city = word
                    break
            return "getCurrentWeather", {"city": city, "units": "metric"}

    def _format_response(self, tool_name: str, result: dict) -> str:
        """Форматирование ответа"""
        if "error" in result:
            return f"Извините, произошла ошибка: {result['error']}"

        data = result.get("data", {})

        if tool_name == "getCurrentWeather":
            return (
                f"Погода в городе {data.get('params', {}).get('city', 'N/A')}: "
                f"данные получены успешно. "
                f"(Время запроса: {data.get('timestamp', 'N/A')})"
            )

        elif tool_name == "getForecast":
            city = data.get('params', {}).get('city', 'N/A')
            days = data.get('params', {}).get('days', 'N/A')
            return f"Прогноз погоды для {city} на {days} дней получен."

        return f"Результат: {result}"

    def chat(self, user_message: str) -> str:
        """Обработка сообщения пользователя"""
        print(f"\nПользователь: {user_message}")

        # Сохраняем в историю
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Выбираем инструмент
        tool_name, tool_args = self._select_tool(user_message)
        print(f"  Выбран инструмент: {tool_name}")
        print(f"  Аргументы: {tool_args}")

        # Вызываем API
        result = self.toolkit.invoke(tool_name, **tool_args)

        # Формируем ответ
        response = self._format_response(tool_name, result)

        # Сохраняем в историю
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "tool_used": tool_name
        })

        print(f"Ассистент: {response}")
        return response


# Демонстрация агента
print("\nДемонстрация Weather Agent:")

agent = WeatherAgent(toolkit)

# Тестовые запросы
agent.chat("Какая погода в Moscow сейчас?")
agent.chat("Покажи прогноз для London на неделю")
agent.chat("Текущая температура в Paris")


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

    1. OpenAPI спецификации
       - Парсинг YAML/JSON спецификаций
       - Извлечение операций и параметров
       - Преобразование в JSON Schema для LLM

    2. Авторизация
       - API Key
       - Bearer Token с refresh
       - Basic Auth
       - OAuth2

    3. Обработка ошибок
       - Классификация ошибок (RetryableError, PermanentError)
       - Rate limit ошибки
       - Authentication ошибки

    4. Retry стратегии
       - Exponential backoff
       - Jitter для предотвращения thundering herd
       - Respect для retry_after

    5. Rate Limiting
       - Token bucket алгоритм
       - Адаптивный лимитер на основе заголовков

    6. Кэширование
       - TTL кэш
       - Декоратор @cached
       - Инвалидация кэша

    7. API Client
       - Интеграция всех компонентов
       - Статистика использования

    8. OpenAPI Toolkit
       - Автоматическое создание инструментов
       - Интеграция с LangChain-style агентами

    Практические применения:
    - Интеграция с любыми REST API
    - Построение надёжных агентов для работы с внешними сервисами
    - Автоматизация взаимодействия с API на основе документации
    """)


if __name__ == "__main__":
    demo()
