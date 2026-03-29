# %%
import time

# Импорты стандартных инструментов для гибридного поиска и реранкинга
from langchain_classic.retrievers import (
    ContextualCompressionRetriever,
    EnsembleRetriever,
)
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS

# %%
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

# Создаём тестовые документы
docs = [
    Document(
        page_content="Python - язык программирования для машинного обучения",
        metadata={"source": "doc_0", "category": "programming"},
    ),
    Document(
        page_content="Машинное обучение использует Python и математику",
        metadata={"source": "doc_1", "category": "ML"},
    ),
    Document(
        page_content="JavaScript работает в браузере",
        metadata={"source": "doc_2", "category": "web"},
    ),
    Document(
        page_content="Deep learning - подраздел машинного обучения",
        metadata={"source": "doc_3", "category": "ML"},
    ),
    Document(
        page_content="React - библиотека для JavaScript",
        metadata={"source": "doc_4", "category": "web"},
    ),
    Document(
        page_content="PyTorch - фреймворк для глубокого обучения",
        metadata={"source": "doc_5", "category": "ML"},
    ),
    Document(
        page_content="Node.js - среда выполнения JavaScript",
        metadata={"source": "doc_6", "category": "web"},
    ),
    Document(
        page_content="Нейронные сети в deep learning",
        metadata={"source": "doc_7", "category": "ML"},
    ),
]

# 1. Инициализируем компоненты
emb = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
vector_store = FAISS.from_documents(docs, emb)

vector_retriever = vector_store.as_retriever(search_kwargs={"k": 5})
bm25_retriever = BM25Retriever.from_documents(docs, k=5)

# 2. Создаем гибридный ретривер (Stage 1: Retrieval)
# ВАЖНО: EnsembleRetriever объединяет результаты, но НЕ реранжирует их Cross-Encoder-ом
ensemble_retriever = EnsembleRetriever(
    retrievers=[
        vector_retriever,
        bm25_retriever,
    ],
    weights=[0.5, 0.5],
)

# 3. Создаем реранкер (Stage 2: Reranking)
# Используем специализированную модель-реранкер
cross_encoder = HuggingFaceCrossEncoder(
    model_name="BAAI/bge-reranker-v2-m3",
)
compressor = CrossEncoderReranker(
    model=cross_encoder,
    top_n=5,
)

# 4. Оборачиваем всё в ContextualCompressionRetriever
final_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=ensemble_retriever,
)

# %% ТЕСТИРУЕМ С ЗАМЕРОМ ВРЕМЕНИ
start_time = time.perf_counter()
results = final_retriever.invoke("расскажи про машинное обучение")
end_time = time.perf_counter()

latency = end_time - start_time

print(f"=== Гибридный поиск завершен за {latency:.4f} сек ===")
for i, doc in enumerate(results, 1):
    print(f"{i}. {doc.page_content}")
    print(f"   Источник: {doc.metadata.get('source')}\n")
