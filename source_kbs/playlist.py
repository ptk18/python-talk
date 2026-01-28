class MusicPlaylist:
    """A music playlist manager - demonstrates dynamic domain discovery"""

    def __init__(self, name="My Playlist"):
        self.name = name
        self.songs = []
        self.current_index = 0
        self.is_playing = False
        self.volume = 50

    def add_song(self, title):
        """Add a song to the playlist"""
        self.songs.append(title)
        return f"Added '{title}'"

    def remove_song(self, title):
        """Remove a song from the playlist"""
        if title in self.songs:
            self.songs.remove(title)
            return f"Removed '{title}'"
        return "Song not found"

    def play(self):
        """Start playing the playlist"""
        if self.songs:
            self.is_playing = True
            return f"Playing: {self.songs[self.current_index]}"
        return "Playlist is empty"

    def pause(self):
        """Pause playback"""
        self.is_playing = False
        return "Paused"

    def skip(self):
        """Skip to next song"""
        if self.songs:
            self.current_index = (self.current_index + 1) % len(self.songs)
            return f"Skipped to: {self.songs[self.current_index]}"
        return "No songs to skip"

    def previous(self):
        """Go to previous song"""
        if self.songs:
            self.current_index = (self.current_index - 1) % len(self.songs)
            return f"Previous: {self.songs[self.current_index]}"
        return "No songs"

    def set_volume(self, level):
        """Set volume level (0-100)"""
        self.volume = max(0, min(100, level))
        return f"Volume: {self.volume}"

    def increase_volume(self, amount=10):
        """Increase volume by amount"""
        self.volume = min(100, self.volume + amount)
        return f"Volume: {self.volume}"

    def decrease_volume(self, amount=10):
        """Decrease volume by amount"""
        self.volume = max(0, self.volume - amount)
        return f"Volume: {self.volume}"

    def get_volume(self):
        """Get current volume level"""
        return self.volume

    def get_playlist(self):
        """Get list of all songs"""
        return self.songs

    def get_current_song(self):
        """Get currently playing song"""
        if self.songs:
            return self.songs[self.current_index]
        return None

    def is_playing_now(self):
        """Check if music is currently playing"""
        return self.is_playing

    def shuffle(self):
        """Shuffle the playlist"""
        import random
        random.shuffle(self.songs)
        return "Playlist shuffled"

    def clear(self):
        """Clear all songs from playlist"""
        self.songs = []
        self.current_index = 0
        return "Playlist cleared"


if __name__ == "__main__":
    # Demo usage
    from auto_nl_interface_backup import NaturalLanguageInterface, CommandExecutor

    interface = NaturalLanguageInterface("playlist.py", "MusicPlaylist")
    playlist = interface.catalog.classes["MusicPlaylist"]()
    executor = CommandExecutor(playlist)

    print("Testing MusicPlaylist with natural language:")
    commands = [
        "add song Bohemian Rhapsody",
        "play",
        "set volume 75",
        "get current song",
    ]

    for cmd in commands:
        seq, _ = interface.process(cmd)
        if seq.commands:
            result = executor.execute(seq.commands[0])
            print(f"✓ '{cmd}' → {result}")
