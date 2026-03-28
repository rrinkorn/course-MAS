# Курс: Инженерия AI-агентов и мультиагентных систем

## Модуль 1: Введение в AI-агенты

**Цель:** Сформировать фундаментальное понимание агентности, отличий от классического NLP и архитектурных принципов построения автономных систем.

- **Лекция 1. От NLP к агентам** — эпоха правил, статистическая революция, нейронные сети, трансформеры, масштабирование, RLHF, год агентов (2023).
- **Лекция 2. Анатомия AI-агента** — автономность, цикл OODA, компоненты агента (LLM, Tools, Memory, Planning), типы памяти, свойства среды.
- **Лекция 3. Когнитивные архитектуры** — System 1/2, PMPA, ReAct, LATS, AutoGPT, BabyAGI.
- **Лекция 4. Паттерны рассуждений** — Zero/Few-shot, Chain of Thought, ReAct, Tree/Graph of Thoughts, Self-Consistency, Reflection.
- **Лекция 5. Ограничения LLM** — галлюцинации, контекстное окно, knowledge cutoff, планирование, методы митигации.
- **Лекция 6. Экосистема и экономика** — провайдеры, open source, русскоязычные модели, ценообразование, TCO, оптимизация стоимости.
- **Лекция 7. Бенчмарки и оценка качества** — MMLU, MATH, HumanEval, SWE-bench, GAIA, Chatbot Arena, подводные камни.

---

## Модуль 2: LangChain

**Цель:** Изучить стандарт де-факто для оркестрации LLM приложений, освоить декларативный язык выражений LCEL.

- **Лекция 1. Философия LangChain и основы LCEL** — архитектура, Runnable, Pipe `|`, примитивы, визуализация и отладка.
- **Лекция 2. LCEL — продвинутые паттерны** — маршрутизация, retry/fallback, стриминг, батчинг, callbacks, кэширование.
- **Лекция 3. Управление промптами** — сообщения, ChatPromptTemplate, few-shot, MessagesPlaceholder, композиция промптов.
- **Лекция 4. Модели и Model I/O** — LLM vs ChatModel, провайдеры, параметры генерации, токены, мультимодальность, стриминг.
- **Лекция 5. Структурированный вывод и Output Parsers** — JSON, Pydantic, with_structured_output(), обработка ошибок, streaming.
- **Лекция 6. Память и Цепочки** — стратегии памяти, RunnableWithMessageHistory, персистентные хранилища, legacy chains, миграция на LangGraph.

---

## Модуль 3: RAG (Retrieval-Augmented Generation)

**Цель:** Научить агентов работать с приватными данными, преодолеть ограничение контекстного окна.

- **Лекция 1. Архитектура RAG** — компоненты, indexing pipeline, query pipeline.
- **Лекция 2. Векторные представления** — Word2Vec, контекстные эмбеддинги, модели эмбеддингов, MTEB Leaderboard.
- **Лекция 3. Векторные базы данных** — brute-force, IVF, HNSW, Chroma, FAISS, Pinecone, Qdrant.
- **Лекция 4. Подготовка данных** — Document Loaders, стратегии chunking, метаданные и фильтрация.
- **Лекция 5. Продвинутый поиск** — Multi-query, HyDE, Parent Document Retriever, Self-query, Ensemble Retriever.
- **Лекция 6. Переранжирование** — Cross-encoder reranking, LLM-based reranking, Lost in the Middle mitigation.
- **Лекция 7. Генерация с контекстом** — промпт-инжиниринг для RAG, цитирование, оценка качества (faithfulness, relevance, recall).

---

## Модуль 4: Tools and Integrations

**Цель:** Научить агентов взаимодействовать с внешним миром через инструменты, API и протоколы.

- **Лекция 1. Function Calling** — механизм function calling, JSON Schema, параллельные вызовы, forced tool use.
- **Лекция 2. Создание инструментов в LangChain** — @tool, StructuredTool, BaseTool, Pydantic, обработка ошибок.
- **Лекция 3. Toolkit и интеграции** — FileManagement, Shell, Requests, DuckDuckGo, кастомные тулкиты.
- **Лекция 4. SQL и базы данных** — SQLDatabaseToolkit, create_sql_agent, SQL injection prevention, Pandas Agent.
- **Лекция 5. OpenAPI и API Chains** — спецификации, автоматическая генерация инструментов, аутентификация.
- **Лекция 6. Мультимодальные инструменты** — Vision API, Image Generation, Speech-to-Text, Text-to-Speech.
- **Лекция 7. Model Context Protocol (MCP)** — архитектура Host/Client/Server, создание MCP-серверов и клиентов.

---

## Модуль 5: LangGraph

**Цель:** Освоить фреймворк для построения сложных агентов на основе графов состояний.

- **Лекция 1. От цепочек к графам** — StateGraph, узлы, рёбра, условные переходы, компиляция.
- **Лекция 2. State Management** — TypedDict, Pydantic, Annotation-based state, редьюсеры.
- **Лекция 3. Агент с инструментами** — ToolNode, bind_tools, streaming, Command API.
- **Лекция 4. Persistence и Time Travel** — MemorySaver, SqliteSaver, checkpoints, откат истории.
- **Лекция 5. Human-in-the-Loop** — interrupt(), approve/reject/edit, интеграция с UI.
- **Лекция 6. Обработка ошибок** — retry, fallback, graceful degradation, таймауты.
- **Лекция 7. Middleware** — ModelRetry, ToolRetry, Fallback, Summarization, CallLimit, кастомные middleware.
- **Лекция 8. Send — динамический параллелизм** — Send API, динамическое порождение узлов, map-reduce.
- **Лекция 9. Functional API** — @entrypoint, @task, декларативный стиль без графа.

---

## Модуль 6: Мультиагентные системы (MAS)

**Цель:** Научиться проектировать системы из нескольких взаимодействующих агентов.

- **Лекция 1. От одного агента к системе** — зачем нужны MAS, shared state vs message passing.
- **Лекция 2. Паттерны MAS** — Supervisor, Router, Handoffs, Pipeline, Swarm, Plan-Execute, Debate, Voting, Map-Reduce.
- **Лекция 3. Комбинирование паттернов** — Supervisor+Reflection, Pipeline+Voting, Plan-Execute+Map-Reduce и др.
- **Лекция 4. Протоколы — MCP и A2A** — MCP для данных/инструментов, A2A для межагентного взаимодействия.
- **Лекция 5. Стек протоколов** — WebMCP, AG-UI, ANP, конвергенция протоколов.
- **Лекция 6. Альтернативные фреймворки** — CrewAI, OpenAI Agents SDK, Google ADK, Pydantic AI, Mastra, smolagents.
- **Лекция 7. Дизайн MAS в реальном мире** — декомпозиция задач, observability, тестирование, деплой.
