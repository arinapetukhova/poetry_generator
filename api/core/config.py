from dataclasses import dataclass

@dataclass
class RAPTORConfig:
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_persist_path: str = "./chroma_db"
    collection_name: str = "song_raptor"
    distance_function: str = "cosine"
    min_line_words: int = 0
    top_k: int = 5