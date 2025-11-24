# test_fixed.py
import json
from main import SongRAPTOR
from core.config import RAPTORConfig

# Load dataset (path should exist and contain expected JSON)
with open('data/dataset/cleaned_songs_dataset.json', 'r', encoding='utf-8') as f:
    song_data = json.load(f)

# Configure RAPTOR
config = RAPTORConfig()

raptor = SongRAPTOR(config)
raptor.load_songs(song_data)
raptor.build_index()

# Print statistics
stats = raptor.get_statistics()
print(f"Database Statistics: {stats}")