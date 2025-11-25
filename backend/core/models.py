from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

@dataclass
class Song:
    title: str
    artist: str
    genre: str
    year: int
    lyrics_text: str
    artist_metadata: str
    genre_metadata: str

@dataclass
class Singer:
    name: str
    songs: List[Song]
    genres: List[str]
    metadata: str

@dataclass
class Genre:
    name: str
    singers: List[Singer]
    metadata: str

@dataclass
class SearchResult:
    text: str
    similarity: float
    context: str
    hierarchy_path: List[str]
    metadata: Dict[str, Any]

@dataclass
class ChromaDocument:
    id: str
    text: str
    embedding: List[float]
    metadata: Optional[Dict[str, Any]] = None
    hierarchy_level: Optional[str] = None

class GenerateRequest(BaseModel):
    query: str
    top_k: int

class GenerateResponse(BaseModel):
    lyrics: str
    reasoning: str 
    context: str
    prompt: str