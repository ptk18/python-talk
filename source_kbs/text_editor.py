class TextEditor:
    def insert_text(self, position, text):
        """Insert text at the given position in the document."""
        return f"Inserted '{text}' at position {position}"

    def delete_text(self, start, end):
        """Delete text between the start and end positions."""
        return f"Deleted text from position {start} to {end}"

    def cut_text(self, start, end):
        """Cut text between start and end positions to the clipboard."""
        return f"Cut text from position {start} to {end} to clipboard"

    def copy_text(self, start, end):
        """Copy text between start and end positions to the clipboard."""
        return f"Copied text from position {start} to {end} to clipboard"

    def paste_text(self, position):
        """Paste clipboard content at the given position."""
        return f"Pasted clipboard content at position {position}"

    def undo(self):
        """Undo the last editing action."""
        return "Last action undone"

    def redo(self):
        """Redo the last undone editing action."""
        return "Last undone action redone"

    def find_text(self, query):
        """Search for text matching the query in the document."""
        return [f"Found '{query}' at position 10", f"Found '{query}' at position 25"]

    def replace_text(self, old_text, new_text):
        """Replace all occurrences of old text with new text."""
        return f"Replaced all occurrences of '{old_text}' with '{new_text}'"

    def get_word_count(self):
        """Return the total number of words in the document."""
        return 150
