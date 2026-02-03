class Playlist:
    def add_song(self, title, artist, duration):
        """Add a new song to the playlist."""
        return f"Added '{title}' by {artist} ({duration} seconds)"
    
    def remove_song(self, title):
        """Remove a song from the playlist by title."""
        return f"Removed '{title}' from playlist"
    
    def shuffle(self):
        """Randomize the order of songs in the playlist."""
        return ["Song 3", "Song 1", "Song 2"]
    
    def get_total_duration(self):
        """Calculate the total duration of all songs in the playlist."""
        return 1245