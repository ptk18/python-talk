from playlistpy import Playlist
import sys

obj = Playlist()
print(obj.add_song(title='cruel summer song', artist='Taylor Swift', duration='summer playlist'))
print(obj.remove_song(title='cruel summer song'))
print(obj.remove_song(title='castle on the hill song'))
print(obj.add_song(title='Lost in Tokyo', artist='Shawn Mendes'))
print(obj.remove_song(title='summer playlist'))
print(obj.shuffle())
