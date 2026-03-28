# %%
from sentence_transformers import SentenceTransformer

# Загрузка модели (скачается автоматически при первом запуске)
model = SentenceTransformer("BAAI/bge-m3")
# model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')

# Получение эмбеддингов
texts = [
    "Какие документы нужны для отпуска?",
    "Заявление на ежегодный оплачиваемый отдых",
    "Расписание автобусов до аэропорта",
]

embeddings = model.encode(texts)
print(f"Форма: {embeddings.shape}")  # (3, 1024)

# Вычисление сходства
from sklearn.metrics.pairwise import cosine_similarity

similarities = cosine_similarity(embeddings)
print("Матрица сходства:")
print(similarities)

# %%

import pprint

from langchain_community.document_loaders import FileSystemBlobLoader, PyMuPDFLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import PyPDFParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)


loader = GenericLoader(
    blob_loader=FileSystemBlobLoader(path="docs/", glob="*.pdf"),
    blob_parser=PyPDFParser(),
)
docs = loader.load()

chunks = text_splitter.split_documents(docs)

print(f"Было документов: {len(docs)}, стало фрагментов: {len(chunks)}")

# print(docs[1].page_content)
for i, page in enumerate(docs):
    print(f"Page {i + 1}:")
    pprint.pp(page.metadata)
    print(f"Page content: {page.page_content[:100]}...")
    print("-" * 100)

# %%
