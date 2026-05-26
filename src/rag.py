import chromadb
from chromadb.utils import embedding_functions
import fitz  # PyMuPDF
from pathlib import Path

DOCS_DIR = Path("data/documents")
CHROMA_DIR = Path("data/chroma_db")
COLLECTION_NAME = "support_docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5


class RAGPipeline:
    def __init__(self):
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.embed_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embed_fn,
            metadata={"hnsw:space": "cosine"}
        )
        self._ingest_new_documents()

    def _ingest_new_documents(self):
        if not DOCS_DIR.exists():
            return

        existing_sources = set()
        if self.collection.count() > 0:
            all_meta = self.collection.get(include=["metadatas"])["metadatas"]
            existing_sources = {m["source"] for m in all_meta if m}

        for filepath in sorted(DOCS_DIR.iterdir()):
            if not filepath.is_file() or filepath.name in existing_sources:
                continue
            if filepath.suffix.lower() == ".pdf":
                self._ingest_pdf(filepath)
            elif filepath.suffix.lower() in {".txt", ".md"}:
                self._ingest_text(filepath)

    def _ingest_pdf(self, filepath: Path):
        doc = fitz.open(str(filepath))
        chunks, ids, metas = [], [], []

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            for i, chunk in enumerate(self._chunk_text(text)):
                chunks.append(chunk)
                ids.append(f"{filepath.name}::p{page_num}::c{i}")
                metas.append({
                    "source": filepath.name,
                    "page": page_num,
                    "chunk": i
                })

        if chunks:
            self._batch_add(ids, chunks, metas)

    def _ingest_text(self, filepath: Path):
        text = filepath.read_text(encoding="utf-8", errors="ignore")
        chunks, ids, metas = [], [], []

        for i, chunk in enumerate(self._chunk_text(text)):
            chunks.append(chunk)
            ids.append(f"{filepath.name}::c{i}")
            metas.append({"source": filepath.name, "page": 1, "chunk": i})

        if chunks:
            self._batch_add(ids, chunks, metas)

    def _chunk_text(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            chunks.append(text[start:end])
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return chunks

    def _batch_add(self, ids, documents, metadatas, batch_size=100):
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )

    def search(self, query: str) -> list[dict]:
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(TOP_K, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            output.append({
                "content": doc,
                "source": meta.get("source", "unknown"),
                "page": meta.get("page", 1),
                "relevance_score": round(1 - dist, 3)
            })

        return output
