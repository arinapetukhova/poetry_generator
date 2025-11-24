from core.config import RAPTORConfig
from core.models import Genre, ChromaDocument, SearchResult
from components.embedder import Embedder
from components.parser import SongParser
from components.chroma_manager import ChromaManager
from typing import List
import uuid
import json
import random

class SongRAPTOR:
    def __init__(self, config: RAPTORConfig = None):
        self.config = config or RAPTORConfig()
        self.embedder = Embedder(self.config.embedding_model)
        self.parser = SongParser()
        self.genre_hierarchy: List[Genre] = []
        self.chroma_manager = ChromaManager(self.config)

    def load_songs(self, json_data: List[dict]):
        self.genre_hierarchy = self.parser.parse_to_hierarchy(json_data)

    def build_index(self):
        documents = []

        added_genres = set()
        added_artists = set()

        for genre in self.genre_hierarchy:

            if genre.name not in added_genres:
                added_genres.add(genre.name)
                num_artists = 3
                num_songs_per_artist = 1

                sample_artists = random.sample(genre.singers, min(num_artists, len(genre.singers)))
                sample_songs = []

                for singer in sample_artists:
                    if singer.songs:
                        songs_to_sample = random.sample(singer.songs, min(num_songs_per_artist, len(singer.songs)))
                        for song in songs_to_sample:
                            sample_songs.append(f"\n{song.title} by {singer.name}\nLyrics:\n{song.lyrics_text}")

                genre_text = (
                    f"GENRE: {genre.name}\n"
                    f"DESCRIPTION: {genre.metadata}\n"
                    f"SAMPLE SONGS: {', '.join(sample_songs)}"
                )

                documents.append(ChromaDocument(
                    id=str(uuid.uuid4()),
                    text=genre_text,
                    embedding=self.embedder.embed_to_list(genre_text),
                    metadata={"context": genre.name,
                              "hierarchy_path": json.dumps([genre.name])},
                    hierarchy_level="genre"
                ))

            for singer in genre.singers:

                if singer.name not in added_artists:
                    added_artists.add(singer.name)

                    artist_examples = "\n".join(
                        [f"Name: {song.title}\nLyrics:\n{song.lyrics_text}" for song in singer.songs[:3]]
                    )

                    artist_text = (
                        f"MUSICIAN/BAND: {singer.name}\n"
                        f"GENRES: {', '.join(singer.genres)}\n"
                        f"DESCRIPTION: {singer.metadata}\n\n"
                        f"EXAMPLE LYRICS:\n{artist_examples}"
                    )

                    documents.append(ChromaDocument(
                        id=str(uuid.uuid4()),
                        text=artist_text,
                        embedding=self.embedder.embed_to_list(artist_text),
                        metadata={
                            "context": f"{genre.name} → {singer.name}",
                            "hierarchy_path": json.dumps([genre.name, singer.name])
                        },
                        hierarchy_level="artist"
                    ))

                for song in singer.songs:

                    song_text = f"TITLE: {song.title}\nARTIST: {singer.name}\nGENRE: {genre.name}\nLYRICS:\n{song.lyrics_text}"

                    documents.append(ChromaDocument(
                        id=str(uuid.uuid4()),
                        text=song_text,
                        embedding=self.embedder.embed_to_list(song_text),
                        metadata={
                            "context": f"{genre.name} → {singer.name} → {song.title}",
                            "hierarchy_path": json.dumps([genre.name, singer.name, song.title])
                        },
                        hierarchy_level="song"
                    ))
       
        self.chroma_manager.add_documents(documents, batch_size=5000)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        query_emb = self.embedder.embed_to_list(query)
        return self.chroma_manager.search(query_emb, n_results=top_k)


    def get_statistics(self):
        stats = {
            'total_genres': len(self.genre_hierarchy),
            'total_singers': sum(len(g.singers) for g in self.genre_hierarchy),
            'total_songs': sum(len(s.songs) for g in self.genre_hierarchy for s in g.singers),
            'genres': {}
        }
        for g in self.genre_hierarchy:
            stats['genres'][g.name] = {
                'singers': len(g.singers),
                'songs': sum(len(s.songs) for s in g.singers)
            }
        return stats