import json
import re
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from fastembed import TextEmbedding
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
INDEX_FILE = DATA_DIR / "index.json"
MODEL_CACHE_DIR = DATA_DIR / "model_cache"

EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
MIN_SCORE = 0.55

_model = None


def ensure_dirs():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.exists():
        INDEX_FILE.write_text('{"assets": [], "chunks": []}', encoding="utf-8")


def load_index() -> Dict[str, Any]:
    ensure_dirs()
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"assets": [], "chunks": []}


def save_index(index: Dict[str, Any]):
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(
            model_name=EMBEDDING_MODEL,
            cache_dir=str(MODEL_CACHE_DIR),
        )
    return _model


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def chunk_page(text: str) -> List[str]:
    text = clean_text(text)
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def parse_pdf(path: Path):
    reader = PdfReader(str(path))
    chunks = []
    for page_no, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        for idx, chunk in enumerate(chunk_page(text)):
            chunks.append({
                "page": page_no,
                "text": chunk,
                "chunk_on_page": idx + 1,
            })
    return chunks, len(reader.pages)


def add_pdf(filename: str, file_path: Path) -> Dict[str, Any]:
    raw_chunks, page_count = parse_pdf(file_path)
    if not raw_chunks:
        raise ValueError(
            "没有从 PDF 中解析出可用文本。请确认这是文字型 PDF，而不是纯扫描图片 PDF。"
        )

    model = get_model()
    embeddings = list(model.passage_embed([c["text"] for c in raw_chunks]))
    index = load_index()

    index["assets"] = [a for a in index["assets"] if a["filename"] != filename]
    index["chunks"] = [c for c in index["chunks"] if c["source"] != filename]

    for i, (chunk, vector) in enumerate(zip(raw_chunks, embeddings)):
        index["chunks"].append({
            "id": f"{filename}__{i}",
            "source": filename,
            "page": chunk["page"],
            "text": chunk["text"],
            "embedding": np.asarray(vector, dtype=np.float32).tolist(),
        })

    index["assets"].append({
        "filename": filename,
        "pages": page_count,
        "chunks": len(raw_chunks),
    })
    save_index(index)
    return {"filename": filename, "pages": page_count, "chunks": len(raw_chunks)}


def cosine_similarity(a, b) -> float:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    index = load_index()
    chunks = index.get("chunks", [])
    if not chunks:
        return []

    model = get_model()
    query_vector = list(model.query_embed(query))[0]
    scored = []
    for chunk in chunks:
        score = cosine_similarity(query_vector, chunk["embedding"])
        scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, chunk in scored[:top_k]:
        if score < MIN_SCORE:
            continue
        results.append({
            "id": chunk["id"],
            "title": f"{chunk['source']} · 第 {chunk['page']} 页",
            "object": "检索到的知识片段",
            "source": chunk["source"],
            "page": chunk["page"],
            "text": chunk["text"],
            "original": chunk["text"],
            "score": round(score, 4),
        })
    return results
