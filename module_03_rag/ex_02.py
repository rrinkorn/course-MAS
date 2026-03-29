# %%
import faiss
import numpy as np

def compute_recall(true_neighbors: np.ndarray, found_neighbors: np.ndarray, k: int) -> float:
    """
    Вычисление Recall@k.
    
    Args:
        true_neighbors: истинные ближайшие соседи (из точного поиска)
        found_neighbors: найденные соседи (из приближённого поиска)
        k: количество соседей для проверки
    """
    recall_sum = 0
    for i in range(len(true_neighbors)):
        true_set = set(true_neighbors[i, :k])
        found_set = set(found_neighbors[i, :k])
        recall_sum += len(true_set & found_set) / k
    return recall_sum / len(true_neighbors)

dimension = 128
nb = 100000
vectors = np.random.random((nb, dimension)).astype('float32')
queries = np.random.random((100, dimension)).astype('float32')

# Создание IVF индекса
nlist = 100  # количество кластеров
quantizer = faiss.IndexFlatL2(dimension)
index_ivf = faiss.IndexIVFFlat(quantizer, dimension, nlist)

# Обучение (обязательно для IVF!)
print("Обучение индекса...")
index_ivf.train(vectors)

# Добавление векторов
index_ivf.add(vectors)

# Эталонный поиск для сравнения
index_flat = faiss.IndexFlatL2(dimension)
index_flat.add(vectors)
D_true, I_true = index_flat.search(queries, 10)

# %%
# Тест разных nprobe
for nprobe in [1, 5, 10, 20]:
    index_ivf.nprobe = nprobe
    D_found, I_found = index_ivf.search(queries, 10)
    recall = compute_recall(I_true, I_found, 10)
    print(f"nprobe={nprobe}: Recall@10 = {recall:.1%}")

# Примерный вывод:
# nprobe=1: Recall@10 = 65%
# nprobe=5: Recall@10 = 88%
# nprobe=10: Recall@10 = 95%
# nprobe=20: Recall@10 = 98%
# %%
