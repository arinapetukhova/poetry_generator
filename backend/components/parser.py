from typing import List, Dict
from core.models import Song, Singer, Genre

class SongParser:
    def parse_to_hierarchy(self, json_data: List[Dict]) -> List[Genre]:
        genres_dict = {}
        singers_dict = {}

        for song_data in json_data:
            song = self._parse_song(song_data)
            genre_name = song.genre
            singer_name = song.artist

            if genre_name not in genres_dict:
                genres_dict[genre_name] = Genre(name=genre_name, singers=[], metadata=song.genre_metadata)

            if singer_name not in singers_dict:
                singer = Singer(name=singer_name, songs=[], genres=[], metadata=song.artist_metadata)
                singers_dict[singer_name] = singer
                genres_dict[genre_name].singers.append(singer)

            singers_dict[singer_name].songs.append(song)
            if genre_name not in singers_dict[singer_name].genres:
                singers_dict[singer_name].genres.append(genre_name)

        return list(genres_dict.values())

    def _parse_song(self, song_data: Dict) -> Song:
        full_lyrics = []

        for _, stanza_text in enumerate(song_data['lyrics']):
            full_lyrics.append(stanza_text)

        return Song(
            title=song_data['title'],
            artist=song_data['artist'],
            artist_metadata=song_data['artist_metadata'],
            genre_metadata=song_data['genre_metadata'],
            genre=song_data['genre'],
            year=song_data.get('year', 0),
            lyrics_text='\n\n'.join(full_lyrics)
        )