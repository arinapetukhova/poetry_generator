import json
from rag_pipeline import SongRAPTOR
from core.config import RAPTORConfig

with open('../data/dataset/cleaned_songs_dataset.json', 'r', encoding='utf-8') as f:
    song_data = json.load(f)

config = RAPTORConfig()

raptor = SongRAPTOR(config)
raptor.load_songs(song_data)
raptor.build_index()

stats = raptor.get_statistics()
print(f"Database Statistics: {stats}")