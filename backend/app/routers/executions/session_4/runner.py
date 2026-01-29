from librarypy import Library
import sys

obj = Library()
print(obj.add_book())
print(obj.add_book())
print(obj.add_book())
print(obj.add_book())
print(obj.add_book())
print(obj.add_book(title='Atomic Habits', author='James Clear'))
print(obj.remove_book(title='Atomic Habits'))
