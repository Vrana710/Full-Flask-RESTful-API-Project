import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .config import Config
from .models import books, get_book_by_id
from .utils import validate_book_data, get_next_book_id

app = Flask(__name__)
app.config.from_object(Config)

# Set up rate limiter
limiter = Limiter(app=app, key_func=get_remote_address)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/books')
def book_page():
    return render_template('books.html', books=books)

@app.route('/books/new', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        new_book = {
            'id': get_next_book_id(),
            'title': request.form['title'],
            'author': request.form['author']
        }
        if not validate_book_data(new_book):
            return render_template('error.html', error_message="Invalid book data"), 400
        books.append(new_book)
        app.logger.info(f'Added new book: {new_book}')
        return redirect(url_for('book_page'))
    return render_template('book_form.html')

@app.route('/books/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = get_book_by_id(book_id)
    if not book:
        return render_template('error.html', error_message="Book not found"), 404

    if request.method == 'POST':
        book['title'] = request.form['title']
        book['author'] = request.form['author']
        app.logger.info(f'Updated book {book_id}: {book}')
        return redirect(url_for('book_page'))

    return render_template('book_form.html', book=book)

@app.route('/books/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    global books
    book = get_book_by_id(book_id)
    if not book:
        return render_template('error.html', error_message="Book not found"), 404

    books = [b for b in books if b["id"] != book_id]
    app.logger.info(f'Deleted book {book_id}')
    return redirect(url_for('book_page'))

@app.route('/api/books', methods=['GET', 'POST'])
@limiter.limit(Config.RATE_LIMIT)
def handle_books():
    if request.method == 'POST':
        new_book = request.get_json()
        if not validate_book_data(new_book):
            return jsonify({"error": "Invalid book data"}), 400
        new_book['id'] = get_next_book_id()
        books.append(new_book)
        app.logger.info(f'Added new book: {new_book}')
        return jsonify(new_book), 201

    # GET request with query parameters for filtering by author and title
    author = request.args.get('author')
    title = request.args.get('title')

    filtered_books = books

    # Filter by author if specified
    if author:
        filtered_books = [book for book 
                                in filtered_books 
                                    if book.get('author') == author]
    
    # Filter by title if specified
    if title:
        filtered_books = [book for book 
                                in filtered_books 
                                    if title.lower() in book.get('title', '').lower()]

    app.logger.info(f'GET request with filters - Author: {author}, Title: {title}')
    return jsonify(filtered_books)


@app.route('/api/books/<int:book_id>', methods=['GET', 'PUT', 'DELETE'])
@limiter.limit(Config.RATE_LIMIT)
def handle_book(book_id):
    book = get_book_by_id(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    if request.method == 'GET':
        return jsonify(book)

    if request.method == 'PUT':
        updated_data = request.get_json()
        if not validate_book_data(updated_data):
            return jsonify({"error": "Invalid book data"}), 400
        book.update(updated_data)
        app.logger.info(f'Updated book {book_id}: {book}')
        return jsonify(book)

    if request.method == 'DELETE':
        global books
        books = [b for b in books if b["id"] != book_id]
        app.logger.info(f'Deleted book {book_id}')
        return jsonify({"message": "Book deleted"}), 200

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_message="Page Not Found!"), 404
