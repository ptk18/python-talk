class FileManager:
    def create_file(self, file_path):
        """Create a new empty file at the specified path."""
        return f"File created at '{file_path}'"

    def delete_file(self, file_path):
        """Permanently delete the file at the specified path."""
        return f"File '{file_path}' deleted"

    def rename_file(self, old_name, new_name):
        """Rename a file from old name to new name."""
        return f"File renamed from '{old_name}' to '{new_name}'"

    def move_file(self, source_path, destination_path):
        """Move a file from the source path to the destination path."""
        return f"File moved from '{source_path}' to '{destination_path}'"

    def copy_file(self, source_path, destination_path):
        """Create a duplicate of the file at a new location."""
        return f"File copied from '{source_path}' to '{destination_path}'"

    def list_files(self, directory_path):
        """List all files in the specified directory."""
        return ["file1.txt", "file2.py", "file3.csv"]

    def get_file_size(self, file_path):
        """Return the size of the specified file in bytes."""
        return 2048

    def file_exists(self, file_path):
        """Check whether a file exists at the specified path."""
        return True
