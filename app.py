from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session
import pyodbc
import secrets
from datetime import datetime
from math import ceil
import os

app = Flask(__name__, static_folder='static')
# Initialize visitor count
visitor_count = 151
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

# Database connection configuration
server = 'bookstoredatabaseserver.database.windows.net'  # Note the 'r' before the string
database = 'BookstoreDB'
username = 'BsAdm'
password = 'Oracle69#'
driver = '{ODBC Driver 17 for SQL Server}'

conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def get_db_connection():
    return pyodbc.connect(conn_str)

# Add the count_visitor function here
@app.before_request
def count_visitor():
    global visitor_count
    if 'visited' not in session:
        visitor_count += 1
        session['visited'] = True

        # Log visitor
        if request.endpoint != 'static':
            ip_address = request.remote_addr
            # If you're behind a proxy, you might need to use this instead:
            # ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

            # Get location (optional, you can remove this if you don't want to log location)
            try:
                response = request.get(f'https://ipapi.co/{ip_address}/json/').json()
                location = response.get('city', '') + ', ' + response.get('country_name', '')
            except:
                location = 'Unknown'

            # Insert into Visitor_log
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Visitor_log (IpAddress, Location) VALUES (?, ?)", ip_address, location)
            conn.commit()
            cursor.close()
            conn.close()

# Add the context processor here
@app.context_processor
def inject_visitor_count():
    return dict(visitor_count=visitor_count)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


@app.route('/')
def index():
    return render_template('index.html')

# Add secret visitors.html page route
@app.route('/visitor_log')
def secret_visitor_log():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 100 * FROM Visitor_log ORDER BY VisitTime DESC")
    visitors = cursor.fetchall()
    conn.close()
    return render_template('visitor.html', visitors=visitors)

@app.route('/countries', methods=['GET', 'POST'])
def countries():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        if 'add' in request.form:
            country_name = request.form['country_name']
            cursor.execute("INSERT INTO Countries (CountryName) VALUES (?)", country_name)
            flash('Country added successfully!', 'success')
        elif 'delete' in request.form:
            country_id = request.form['delete']
            cursor.execute("DELETE FROM Countries WHERE CountryID = ?", country_id)
            flash('Country deleted successfully!', 'success')
        elif 'edit' in request.form:
            country_id = request.form['edit_country_id']
            country_name = request.form['edit_country_name']
            cursor.execute("UPDATE Countries SET CountryName = ? WHERE CountryID = ?", country_name, country_id)
            flash('Country updated successfully!', 'success')
        
        conn.commit()
        return redirect(url_for('countries'))
    
    # Handle GET request with search and order_by parameters
    search = request.args.get('search', '')
    order_by = request.args.get('order_by', 'CountryName')
    
    # Construct the SQL query
    query = "SELECT * FROM Countries WHERE CountryName LIKE ?"
    params = [f'%{search}%']
    
    # Add ORDER BY clause
    query += f" ORDER BY {order_by}"
    
    cursor.execute(query, params)
    countries = cursor.fetchall()
    conn.close()
    
    return render_template('countries.html', countries=countries)

@app.route('/genres', methods=['GET', 'POST'])
def genres():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        if 'add' in request.form:
            genre_name = request.form['genre_name']
            cursor.execute("INSERT INTO Genres (GenreName) VALUES (?)", genre_name)
            flash('Genre added successfully!', 'success')
        elif 'delete' in request.form:
            genre_id = request.form['delete']
            cursor.execute("DELETE FROM Genres WHERE GenreID = ?", genre_id)
            flash('Genre deleted successfully!', 'success')
        elif 'edit' in request.form:
            genre_id = request.form['edit_genre_id']
            genre_name = request.form['edit_genre_name']
            cursor.execute("UPDATE Genres SET GenreName = ? WHERE GenreID = ?", genre_name, genre_id)
            flash('Genre updated successfully!', 'success')
        
        conn.commit()
        return redirect(url_for('genres'))
    
    cursor.execute("SELECT * FROM Genres ORDER BY GenreName")
    genres = cursor.fetchall()
    conn.close()
    
    return render_template('genres.html', genres=genres)

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        if 'add' in request.form:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            country_id = request.form['country_id']
            cursor.execute("INSERT INTO Customers (FirstName, LastName, Email, Phone, Address, CountryID) VALUES (?, ?, ?, ?, ?, ?)", 
                           first_name, last_name, email, phone, address, country_id)
            flash('Customer added successfully!', 'success')
        elif 'edit' in request.form:
            customer_id = request.form['edit_customer_id']
            first_name = request.form['edit_first_name']
            last_name = request.form['edit_last_name']
            email = request.form['edit_email']
            phone = request.form['edit_phone']
            address = request.form['edit_address']
            country_id = request.form['edit_country_id']
            cursor.execute("UPDATE Customers SET FirstName = ?, LastName = ?, Email = ?, Phone = ?, Address = ?, CountryID = ? WHERE CustomerID = ?", 
                           first_name, last_name, email, phone, address, country_id, customer_id)
            flash('Customer updated successfully!', 'success')
        elif 'delete' in request.form:
            customer_id = request.form['delete']
            cursor.execute("DELETE FROM Customers WHERE CustomerID = ?", customer_id)
            flash('Customer deleted successfully!', 'success')
        
        conn.commit()
        return redirect(url_for('customers'))
    
    # Handle GET request with search and order_by parameters
    search = request.args.get('search', '')
    order_by = request.args.get('order_by', 'LastName, FirstName')
    
    # Construct the SQL query
    query = """
    SELECT c.CustomerID, c.FirstName, c.LastName, c.Email, c.Phone, c.Address, c.CountryID, co.CountryName 
    FROM Customers c
    LEFT JOIN Countries co ON c.CountryID = co.CountryID
    WHERE c.FirstName LIKE ? OR c.LastName LIKE ? OR c.Email LIKE ?
    """
    params = [f'%{search}%', f'%{search}%', f'%{search}%']
    
    # Add ORDER BY clause
    query += f" ORDER BY {order_by}"
    
    cursor.execute(query, params)
    customers = cursor.fetchall()
    
    # Fetch countries for the dropdown
    cursor.execute("SELECT CountryID, CountryName FROM Countries ORDER BY CountryName")
    countries = cursor.fetchall()
    
    conn.close()
    
    return render_template('customers.html', customers=customers, countries=countries)

@app.route('/books', methods=['GET', 'POST'])
def books():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        if 'add' in request.form:
            title = request.form['title']
            author = request.form['author']
            genre_id = request.form['genre_id'] if request.form['genre_id'] else None
            price = request.form['price']
            stock_quantity = request.form['stock_quantity']
            cursor.execute("INSERT INTO Books (Title, Author, GenreID, Price, StockQuantity) VALUES (?, ?, ?, ?, ?)", 
                           title, author, genre_id, price, stock_quantity)
            flash('Book added successfully!', 'success')
        elif 'edit' in request.form:
            book_id = request.form['edit_book_id']
            title = request.form['edit_title']
            author = request.form['edit_author']
            genre_id = request.form['edit_genre_id'] if request.form['edit_genre_id'] else None
            price = request.form['edit_price']
            stock_quantity = request.form['edit_stock_quantity']
            cursor.execute("UPDATE Books SET Title = ?, Author = ?, GenreID = ?, Price = ?, StockQuantity = ? WHERE BookID = ?", 
                           title, author, genre_id, price, stock_quantity, book_id)
            flash('Book updated successfully!', 'success')
        elif 'delete' in request.form:
            book_id = request.form['delete']
            cursor.execute("DELETE FROM Books WHERE BookID = ?", book_id)
            flash('Book deleted successfully!', 'success')
        
        conn.commit()
        return redirect(url_for('books'))
    
    # Handle GET request with search, order_by, and page parameters
    search = request.args.get('search', '')
    order_by = request.args.get('order_by', 'Title')
    page = int(request.args.get('page', 1))
    per_page = 10
    
    # Construct the SQL query for counting total books
    count_query = """
    SELECT COUNT(*) 
    FROM Books b
    LEFT JOIN Genres g ON b.GenreID = g.GenreID
    WHERE b.Title LIKE ? OR b.Author LIKE ?
    """
    count_params = [f'%{search}%', f'%{search}%']
    
    cursor.execute(count_query, count_params)
    total_books = cursor.fetchone()[0]
    total_pages = ceil(total_books / per_page)
    
    # Construct the SQL query for fetching books with pagination
    query = """
    SELECT b.BookID, b.Title, b.Author, b.GenreID, b.Price, b.StockQuantity, g.GenreName 
    FROM Books b
    LEFT JOIN Genres g ON b.GenreID = g.GenreID
    WHERE b.Title LIKE ? OR b.Author LIKE ?
    """
    params = [f'%{search}%', f'%{search}%']
    
    # Add ORDER BY clause
    query += f" ORDER BY {order_by}"
    
    # Add OFFSET and FETCH for pagination
    query += f" OFFSET {(page - 1) * per_page} ROWS FETCH NEXT {per_page} ROWS ONLY"
    
    cursor.execute(query, params)
    books = cursor.fetchall()
    
    # Format prices
    formatted_books = []
    for book in books:
        formatted_book = list(book)
        formatted_book[4] = f"£{book.Price:.2f}"  # Format price
        formatted_books.append(formatted_book)
    
    # Fetch genres for the dropdown
    cursor.execute("SELECT GenreID, GenreName FROM Genres ORDER BY GenreName")
    genres = cursor.fetchall()
    
    conn.close()
    
    return render_template('books.html', books=formatted_books, genres=genres, 
                           page=page, total_pages=total_pages, search=search, order_by=order_by)

@app.route('/orders', methods=['GET', 'POST'])
def orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        if 'add' in request.form:
            customer_id = request.form['customer_id']
            book_id = request.form['book_id']
            quantity = request.form['quantity']
            # Calculate total price based on book price and quantity
            cursor.execute("SELECT Price FROM Books WHERE BookID = ?", book_id)
            book_price = cursor.fetchone()[0]
            total_price = float(book_price) * int(quantity)
            cursor.execute("INSERT INTO Orders (CustomerID, BookID, Quantity, TotalPrice) VALUES (?, ?, ?, ?)", 
                           customer_id, book_id, quantity, total_price)
            flash('Order added successfully!', 'success')
        elif 'edit' in request.form:
            order_id = request.form['edit_order_id']
            customer_id = request.form['edit_customer_id']
            book_id = request.form['edit_book_id']
            quantity = request.form['edit_quantity']
            # Recalculate total price
            cursor.execute("SELECT Price FROM Books WHERE BookID = ?", book_id)
            book_price = cursor.fetchone()[0]
            total_price = float(book_price) * int(quantity)
            cursor.execute("UPDATE Orders SET CustomerID = ?, BookID = ?, Quantity = ?, TotalPrice = ? WHERE OrderID = ?", 
                           customer_id, book_id, quantity, total_price, order_id)
            flash('Order updated successfully!', 'success')
        elif 'delete' in request.form:
            order_id = request.form['delete']
            cursor.execute("DELETE FROM Orders WHERE OrderID = ?", order_id)
            flash('Order deleted successfully!', 'success')
        
        conn.commit()
        return redirect(url_for('orders'))
    
    # Handle GET request with search, order_by, and page parameters
    search = request.args.get('search', '')
    order_by = request.args.get('order_by', 'OrderDate DESC')
    page = int(request.args.get('page', 1))
    per_page = 10
    
    # Construct the SQL query for counting total orders
    count_query = """
    SELECT COUNT(*) 
    FROM Orders o
    JOIN Customers c ON o.CustomerID = c.CustomerID
    JOIN Books b ON o.BookID = b.BookID
    WHERE CAST(o.OrderID AS NVARCHAR) LIKE ? OR c.FirstName LIKE ? OR c.LastName LIKE ? OR b.Title LIKE ?
    """
    count_params = [f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%']
    
    cursor.execute(count_query, count_params)
    total_orders = cursor.fetchone()[0]
    total_pages = (total_orders + per_page - 1) // per_page
    
    # Construct the SQL query for fetching orders with pagination
    query = """
    SELECT o.OrderID, o.CustomerID, c.FirstName, c.LastName, o.BookID, b.Title, o.OrderDate, o.Quantity, o.TotalPrice
    FROM Orders o
    JOIN Customers c ON o.CustomerID = c.CustomerID
    JOIN Books b ON o.BookID = b.BookID
    WHERE CAST(o.OrderID AS NVARCHAR) LIKE ? OR c.FirstName LIKE ? OR c.LastName LIKE ? OR b.Title LIKE ?
    """
    params = [f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%']
    
    # Add ORDER BY clause
    query += f" ORDER BY {order_by}"
    
    # Add OFFSET and FETCH for pagination
    query += f" OFFSET {(page - 1) * per_page} ROWS FETCH NEXT {per_page} ROWS ONLY"
    
    cursor.execute(query, params)
    orders = cursor.fetchall()
    
    # Format dates and prices
    formatted_orders = []
    for order in orders:
        formatted_order = list(order)
        formatted_order[6] = order.OrderDate.strftime('%d/%m/%Y %H:%M:%S')  # Format date
        formatted_order[8] = f"£{order.TotalPrice:.2f}"  # Format price
        formatted_orders.append(formatted_order)
    
    # Fetch customers for the dropdown
    cursor.execute("SELECT CustomerID, FirstName, LastName FROM Customers ORDER BY LastName, FirstName")
    customers = cursor.fetchall()
    
    # Fetch books for the dropdown
    cursor.execute("SELECT BookID, Title FROM Books ORDER BY Title")
    books = cursor.fetchall()
    
    conn.close()
    
    return render_template('orders.html', orders=formatted_orders, customers=customers, books=books,
                           page=page, total_pages=total_pages, search=search, order_by=order_by)

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/add_country', methods=['POST'])
def add_country():
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'No JSON data received'}), 400

    new_country_name = data.get('country_name')

    if not new_country_name:
        return jsonify({'success': False, 'message': 'Country name is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if country already exists
        cursor.execute("SELECT CountryID FROM Countries WHERE CountryName = ?", (new_country_name,))
        existing_country = cursor.fetchone()

        if existing_country:
            return jsonify({'success': False, 'message': 'Country already exists'}), 400

        # Add new country
        cursor.execute("INSERT INTO Countries (CountryName) OUTPUT INSERTED.CountryID VALUES (?)", (new_country_name,))
        new_country_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({'success': True, 'country_id': new_country_id}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)