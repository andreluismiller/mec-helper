from pathlib import Path
import json
import numpy as np
from tqdm.auto import tqdm

from embeder import Embeder
from sqlitesearch import TextSearchIndex, VectorSearchIndex


# ------------------------------------------------------------------
# 1. Carrega o dataset
# ------------------------------------------------------------------
DATASET_PATH = Path(__file__).parent / "data" / "raw" / "dataset.json"

with open(DATASET_PATH, encoding="utf-8") as f:
    documents = json.load(f)

print(f"{len(documents)} documentos carregados de {DATASET_PATH}")


# ------------------------------------------------------------------
# 2. Monta o texto que será embedado, com os MESMOS campos usados no
#    índice textual (nome, pergunta, resposta).
# ------------------------------------------------------------------
def build_passage_text(doc: dict) -> str:
    partes = [doc.get("nome", ""), doc.get("pergunta", ""), doc.get("resposta", "")]
    return "passage: " + " ".join(p for p in partes if p)


texts = [build_passage_text(doc) for doc in documents]


# ------------------------------------------------------------------
# 3. Gera os embeddings em batches de 50
# ------------------------------------------------------------------
embeder = Embeder()  # usa models/Xenova/multilingual-e5-base por padrão

batch_size = 50
vectors = []

for i in tqdm(range(0, len(texts), batch_size)):
    batch = texts[i:i + batch_size]
    batch_vectors = embeder.encode_batch(batch)  # já normalizado (ver embeder.py)
    vectors.extend(batch_vectors)

print(len(vectors))
X = np.array(vectors)
print("Shape de X:", X.shape)  # (n_documentos, dim)


# ------------------------------------------------------------------
# 4. Indexação híbrida (texto + vetor) no mesmo arquivo .db
# ------------------------------------------------------------------
DB_PATH = "mec_faq.db"

vector_index = VectorSearchIndex(
    keyword_fields=["sigla", "agrupamento", "termos", "sinonimos"],
    id_field="doc_id",
    mode="ivf",
    db_path=DB_PATH,
)
vector_index.fit(X, documents)

text_index = TextSearchIndex(
    text_fields=["nome", "pergunta", "resposta"],
    keyword_fields=["sigla", "agrupamento", "termos", "sinonimos"],
    id_field="doc_id",
    db_path=DB_PATH,
)
text_index.fit(documents)

print(f"Índice híbrido salvo em {DB_PATH}")