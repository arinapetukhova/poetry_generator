import chromadb
from typing import List, Dict, Any
import json
from core.models import ChromaDocument, SearchResult
from core.config import RAPTORConfig

class ChromaManager:
    def __init__(self, config: RAPTORConfig):
        self.config = config
        self.client = chromadb.PersistentClient(path=config.chroma_persist_path)
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            return self.client.get_collection(self.config.collection_name)
        except:
            return self.client.create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    def add_documents(self, documents: List[ChromaDocument], batch_size: int = 5000):
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            self.collection.add(
                ids=[doc.id for doc in batch],
                embeddings=[doc.embedding for doc in batch],
                documents=[doc.text for doc in batch],
                metadatas=[doc.metadata or {} for doc in batch]
            )

    def search(self, query_embedding: List[float], n_results: int = 5) -> List[SearchResult]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        search_results = []
        for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            search_results.append(SearchResult(
                text=doc,
                similarity=1 - dist,
                context=meta.get('context', ''),
                hierarchy_path=meta.get('hierarchy_path', []),
                metadata=meta
            ))
        return search_results