import chromadb
from typing import List
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
            # Create collection with ChromaDB's default embedding function
            return self.client.create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": "cosine"}
                # ChromaDB will use its default embedder automatically
            )

    def add_documents(self, documents: List[ChromaDocument], batch_size: int = 5000):
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            # Only pass text - ChromaDB will compute embeddings automatically
            self.collection.add(
                ids=[doc.id for doc in batch],
                documents=[doc.text for doc in batch],  # Only text, no pre-computed embeddings
                metadatas=[doc.metadata or {} for doc in batch]
            )

    def search_with_text(self, query_text: str, n_results: int = 5) -> List[SearchResult]:
        """Search using text query - ChromaDB handles embedding internally"""
        results = self.collection.query(
            query_texts=[query_text],  # Pass text instead of embeddings
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        search_results = []
        for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            search_results.append(SearchResult(
                text=doc,
                similarity=1 - dist,
                context=meta.get('context', ''),
                hierarchy_path=json.loads(meta.get('hierarchy_path', '[]')) if meta.get('hierarchy_path') else [],
                metadata=meta
            ))
        return search_results

    # Keep the original search method for backward compatibility
    def search(self, query_embedding: List[float], n_results: int = 5) -> List[SearchResult]:
        """Search using pre-computed embeddings (for backward compatibility)"""
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
                hierarchy_path=json.loads(meta.get('hierarchy_path', '[]')) if meta.get('hierarchy_path') else [],
                metadata=meta
            ))
        return search_results