# %%
import chromadb
from chromadb.utils import embedding_functions

# Создание клиента
client = chromadb.PersistentClient(path="./chroma_db")

# Определение функции эмбеддинга
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-m3",
    device="cpu",
    normalize_embeddings=True,
    batch_size=32,
)

# Создание или получение коллекции
collection = client.get_or_create_collection(
    name="documents",
    embedding_function=ef,
)

# Добавление документов
collection.add(
    documents=["Политика удалённой работы...", "Процедура оформления отпуска..."],
    metadatas=[{"category": "HR"}, {"category": "HR"}],
    ids=["doc1", "doc2"],
)

# Поиск
results = collection.query(
    query_texts=["Как оформить отпуск?"],
    n_results=5,
    where={"category": "HR"},  # Фильтрация по метаданным
)

print(results)
# %%
