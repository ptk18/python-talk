class Library:
    def add_book(self, title, author):
        """Add a new book to the library collection."""
        return f"Book '{title}' by {author} added successfully"
    
    def remove_book(self, title):
        """Remove a book from the library by its title."""
        return f"Book '{title}' removed from library"
    
    def search_by_author(self, author):
        """Find all books written by a specific author."""
        return [f"Book 1 by {author}", f"Book 2 by {author}"]
    
    def check_availability(self, title):
        """Check if a book is currently available for borrowing."""
        return True