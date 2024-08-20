from .models import books

def validate_book_data(data):
    if "title" not in data or "author" not in data:
        return False
    return True

def get_next_book_id():
    if not books:
        return 1
    return max(book["id"] for book in books) + 1
