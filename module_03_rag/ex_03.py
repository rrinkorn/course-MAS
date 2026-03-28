# %%
from qdrant_client import QdrantClient, models

client = QdrantClient(url="http://localhost:6333")

# %%
client.create_collection(
    collection_name="optimized_collection1",
    vectors_config=models.VectorParams(
        size=128,
        distance=models.Distance.COSINE
    ),
    hnsw_config=models.HnswConfigDiff(
        m=32,                    # количество связей (16-64)
        ef_construct=200,        # качество построения (100-500)
        full_scan_threshold=10000  # порог переключения на полный скан
    )
)


# %%
results = client.query_points(
    collection_name="optimized_collection1",
    query=[0.1, 0.2, 0.3],  # Аргумент query_vector заменен на query
    limit=10,
    search_params=models.SearchParams(
        hnsw_ef=128  # efSearch для этого запроса по-прежнему в SearchParams
    )
)
# %%