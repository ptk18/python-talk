from playlistpy import Playlist
import sys

obj = Playlist()
print(obj.add_song(title='free now', artist='Gracie Abrams', duration=2026.0))
print(obj.shuffle())
print(obj.remove_song(title='supermarket flowers song'))
