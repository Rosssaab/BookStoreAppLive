from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session
from sqlalchemy import create_engine, text
import secrets
from datetime import datetime
from math import ceil
import os
import logging
import requests
from dotenv import load_dotenv
import urllib.parse

# Load environment variables from .env file
load_dotenv()

# Instead, use only the SQL Server connection
engine = create_engine(f"mssql+pyodbc://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}?driver={os.getenv('DB_DRIVER').replace(' ', '+')}")

# Force current dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Current working directory: {os.getcwd()}")
print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")

# Rest of your code...
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}?driver={os.getenv('DB_DRIVER').replace(' ', '+')}"
app.config['APPLICATION_ROOT'] = '/BookStore'

def get_db_connection():
    logger.debug("Attempting to establish database connection")
    try:
        connection = engine.connect()
        logger.debug("Database connection established successfully")
        return connection
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

# Initialize visitor count
visitor_count = 651

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
                logger.debug(f"IP Address = [{ip_address}]")                          
                response = request.get('https://ipapi.co/{ip_address}/json/').json()
                logger.debug(f"response = [{response}]")                             
                location = response.get('city', '') + ', ' + response.get('country_name', '')
                logger.debug(f"response = [{location}]")
            except:
                location = 'Unknown'

            # Insert into Visitor_log
            try:

                conn = get_db_connection()
                conn.execute(text("INSERT INTO Visitor_log (IpAddress, Location) VALUES (:ip_address, :location)"), {"ip_address": ip_address, "location": location})
                conn.close()
            except:
                location = 'Unknown'
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
    result = conn.execute(text("SELECT TOP 100 * FROM Visitor_log ORDER BY VisitTime DESC"))
    visitors = result.fetchall()
    conn.close()
    return render_template('visitor.html', visitors=visitors)

@app.route('/countries', methods=['GET', 'POST'])
def countries():
    conn = get_db_connection()
    
    if request.method == 'POST':
        if 'add' in request.form:
            country_name = request.form['country_name']
            conn.execute(text("INSERT INTO Countries (CountryName) VALUES (:country_name)"), {"country_name": country_name})
            flash('Country added successfully!', 'success')
        elif 'delete' in request.form:
            country_id = request.form['delete']
            conn.execute(text("DELETE FROM Countries WHERE CountryID = :country_id"), {"country_id": country_id})
            flash('Country deleted successfully!', 'success')
        elif 'edit' in request.form:
            country_id = request.form['edit_country_id']
            country_name = request.form['edit_country_name']
            conn.execute(text("UPDATE Countries SET CountryName = :country_name WHERE CountryID = :country_id"), {"country_name": country_name, "country_id": country_id})
            flash('Country updated successfully!', 'success')
        
        conn.commit()
        return redirect(url_for('countries', _external=True).replace('http://www.mywebstuff.co.uk', 'http://www.mywebstuff.co.uk/BookStore'))
    
    # Handle GET request with search and order_by parameters
    search = request.args.get('search', '')
    order_by = request.args.get('order_by', 'CountryName')
    
    # Construct the SQL query
    query = "SELECT * FROM Countries WHERE CountryName LIKE :search"
    params = {"search": f'%{search}%'}
    
    # Add ORDER BY clause
    query += f" ORDER BY {order_by}"
    
    result = conn.execute(text(query), params)
    countries = result.fetchall()
    conn.close()
    
    return render_template('countries.html', countries=countries)

@app.route('/genres', methods=['GET', 'POST'])
def genres():
    conn = get_db_connection()
    
    if request.method == 'POST':
        if 'add' in request.form:
            genre_name = request.form['genre_name']
            conn.execute(text("INSERT INTO Genres (GenreName) VALUES (:genre_name)"), {"genre_name": genre_name})
            flash('Genre added successfully!', 'success')
        elif 'delete' in request.form:
            genre_id = request.form['delete']
            conn.execute(text("DELETE FROM Genres WHERE GenreID = :genre_id"), {"genre_id": genre_id})
            flash('Genre deleted successfully!', 'success')
        elif 'edit' in request.form:
            genre_id = request.form['edit_genre_id']
            genre_name = request.form['edit_genre_name']
            conn.execute(text("UPDATE Genres SET GenreName = :genre_name WHERE GenreID = :genre_id"), {"genre_name": genre_name, "genre_id": genre_id})
            flash('Genre updated successfully!', 'success')
        
        conn.commit()
        return redirect(url_for('genres', _external=True).replace('http://www.mywebstuff.co.uk', 'http://www.mywebstuff.co.uk/BookStore'))
    
    result = conn.execute(text("SELECT * FROM Genres ORDER BY GenreName"))
    genres = result.fetchall()
    conn.close()
    
    return render_template('genres.html', genres=genres)

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    conn = get_db_connection()
    if request.method == 'POST':
        # Add debugging
        print("POST request received")
        print("Form data:", request.form)
        
        if 'add' in request.form:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            country_id = request.form['country_id']
            conn.execute(text("INSERT INTO Customers (FirstName, LastName, Email, Phone, Address, CountryID) VALUES (:first_name, :last_name, :email, :phone, :address, :country_id)"), 
                           {"first_name": first_name, "last_name": last_name, "email": email, "phone": phone, "address": address, "country_id": country_id})
            flash('Customer added successfully!', 'success')
        elif 'edit' in request.form:
            try:
                customer_id = request.form['edit_customer_id']
                first_name = request.form['edit_first_name']
                last_name = request.form['edit_last_name']
                email = request.form['edit_email']
                phone = request.form['edit_phone']
                address = request.form['edit_address']
                country_id = request.form['edit_country_id']
                
                # Debug print
                print(f"Updating customer {customer_id} with data:", {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                    "address": address,
                    "country_id": country_id
                })
                
                # Execute the update
                conn.execute(text("""
                    UPDATE Customers 
                    SET FirstName = :first_name, 
                        LastName = :last_name, 
                        Email = :email, 
                        Phone = :phone, 
                        Address = :address, 
                        CountryID = :country_id 
                    WHERE CustomerID = :customer_id
                """), {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                    "address": address,
                    "country_id": country_id,
                    "customer_id": customer_id
                })
                
                conn.commit()
                flash('Customer updated successfully!', 'success')
            except Exception as e:
                print("Error updating customer:", str(e))
                conn.rollback()
                flash('Error updating customer: ' + str(e), 'error')
        
        return redirect(url_for('customers', _external=True).replace('http://www.mywebstuff.co.uk', 'http://www.mywebstuff.co.uk/BookStore'))
    
    # Handle GET request with search and order_by parameters
    search = request.args.get('search', '')
    order_by = request.args.get('order_by', 'LastName, FirstName')
    
    # Construct the SQL query
    query = """
    SELECT c.CustomerID, c.FirstName, c.LastName, c.Email, c.Phone, c.Address, c.CountryID, co.CountryName 
    FROM Customers c
    LEFT JOIN Countries co ON c.CountryID = co.CountryID
    WHERE c.FirstName LIKE :search OR c.LastName LIKE :search OR c.Email LIKE :search
    """
    params = {"search": f'%{search}%'}
    
    # Add ORDER BY clause
    query += f" ORDER BY {order_by}"
    
    result = conn.execute(text(query), params)
    customers = result.fetchall()
    
    # Fetch countries for the dropdown
    result = conn.execute(text("SELECT CountryID, CountryName FROM Countries ORDER BY CountryName"))
    countries = result.fetchall()
    
    conn.close()
    
    return render_template('customers.html', customers=customers, countries=countries)

@app.route('/books', methods=['GET', 'POST'])
def books():
    conn = get_db_connection()
    
    if request.method == 'POST':
        if 'add' in request.form:
            title = request.form['title']
            author = request.form['author']
            genre_id = request.form['genre_id'] if request.form['genre_id'] else None
            price = request.form['price']
            stock_quantity = request.form['stock_quantity']
            conn.execute(text("INSERT INTO Books (Title, Author, GenreID, Price, StockQuantity) VALUES (:title, :author, :genre_id, :price, :stock_quantity)"), 
                           {"title": title, "author": author, "genre_id": genre_id, "price": price, "stock_quantity": stock_quantity})
            flash('Book added successfully!', 'success')
        elif 'edit' in request.form:
            book_id = request.form['edit_book_id']
            title = request.form['edit_title']
            author = request.form['edit_author']
            genre_id = request.form['edit_genre_id'] if request.form['edit_genre_id'] else None
            price = request.form['edit_price']
            stock_quantity = request.form['edit_stock_quantity']
            conn.execute(text("UPDATE Books SET Title = :title, Author = :author, GenreID = :genre_id, Price = :price, StockQuantity = :stock_quantity WHERE BookID = :book_id"), 
                           {"title": title, "author": author, "genre_id": genre_id, "price": price, "stock_quantity": stock_quantity, "book_id": book_id})
            flash('Book updated successfully!', 'success')
        elif 'delete' in request.form:
            book_id = request.form['delete']
            conn.execute(text("DELETE FROM Books WHERE BookID = :book_id"), {"book_id": book_id})
            flash('Book deleted successfully!', 'success')
        
        conn.commit()
        return redirect(url_for('books', _external=True).replace('http://www.mywebstuff.co.uk', 'http://www.mywebstuff.co.uk/BookStore'))
    
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
    WHERE b.Title LIKE :search OR b.Author LIKE :search
    """
    count_params = {"search": f'%{search}%'}
    
    result = conn.execute(text(count_query), count_params)
    total_books = result.fetchone()[0]
    total_pages = ceil(total_books / per_page)
    
    # Construct the SQL query for fetching books with pagination
    query = """
    SELECT b.BookID, b.Title, b.Author, b.GenreID, b.Price, b.StockQuantity, g.GenreName 
    FROM Books b
    LEFT JOIN Genres g ON b.GenreID = g.GenreID
    WHERE b.Title LIKE :search OR b.Author LIKE :search
    """
    params = {"search": f'%{search}%'}
    
    # Add ORDER BY clause
    query += f" ORDER BY {order_by}"
    
    # Add OFFSET and FETCH for pagination
    query += f" OFFSET {(page - 1) * per_page} ROWS FETCH NEXT {per_page} ROWS ONLY"
    
    result = conn.execute(text(query), params)
    books = result.fetchall()
    
    # Format prices
    formatted_books = []
    for book in books:
        formatted_book = list(book)
        formatted_book[4] = f"£{book.Price:.2f}"  # Format price
        formatted_books.append(formatted_book)
    
    # Fetch genres for the dropdown
    result = conn.execute(text("SELECT GenreID, GenreName FROM Genres ORDER BY GenreName"))
    genres = result.fetchall()
    
    conn.close()
    
    return render_template('books.html', books=formatted_books, genres=genres, 
                           page=page, total_pages=total_pages, search=search, order_by=order_by)

@app.route('/orders', methods=['GET', 'POST'])
def orders():
    conn = get_db_connection()
    
    if request.method == 'POST':
        if 'add' in request.form:
            customer_id = request.form['customer_id']
            book_id = request.form['book_id']
            quantity = request.form['quantity']
            # Calculate total price based on book price and quantity
            result = conn.execute(text("SELECT Price FROM Books WHERE BookID = :book_id"), {"book_id": book_id})
            book_price = result.fetchone()[0]
            total_price = float(book_price) * int(quantity)
            conn.execute(text("INSERT INTO Orders (CustomerID, BookID, Quantity, TotalPrice) VALUES (:customer_id, :book_id, :quantity, :total_price)"), 
                           {"customer_id": customer_id, "book_id": book_id, "quantity": quantity, "total_price": total_price})
            flash('Order added successfully!', 'success')
        elif 'edit' in request.form:
            order_id = request.form['edit_order_id']
            customer_id = request.form['edit_customer_id']
            book_id = request.form['edit_book_id']
            quantity = request.form['edit_quantity']
            # Recalculate total price
            result = conn.execute(text("SELECT Price FROM Books WHERE BookID = :book_id"), {"book_id": book_id})
            book_price = result.fetchone()[0]
            total_price = float(book_price) * int(quantity)
            conn.execute(text("UPDATE Orders SET CustomerID = :customer_id, BookID = :book_id, Quantity = :quantity, TotalPrice = :total_price WHERE OrderID = :order_id"), 
                           {"customer_id": customer_id, "book_id": book_id, "quantity": quantity, "total_price": total_price, "order_id": order_id})
            flash('Order updated successfully!', 'success')
        elif 'delete' in request.form:
            order_id = request.form['delete']
            conn.execute(text("DELETE FROM Orders WHERE OrderID = :order_id"), {"order_id": order_id})
            flash('Order deleted successfully!', 'success')
        
        conn.commit()
        return redirect(url_for('orders', _external=True).replace('http://www.mywebstuff.co.uk', 'http://www.mywebstuff.co.uk/BookStore'))
    
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
    WHERE CAST(o.OrderID AS NVARCHAR) LIKE :search OR c.FirstName LIKE :search OR c.LastName LIKE :search OR b.Title LIKE :search
    """
    count_params = {"search": f'%{search}%'}
    
    result = conn.execute(text(count_query), count_params)
    total_orders = result.fetchone()[0]
    total_pages = (total_orders + per_page - 1) // per_page
    
    # Construct the SQL query for fetching orders with pagination
    query = """
    SELECT o.OrderID, o.CustomerID, c.FirstName, c.LastName, o.BookID, b.Title, o.OrderDate, o.Quantity, o.TotalPrice
    FROM Orders o
    JOIN Customers c ON o.CustomerID = c.CustomerID
    JOIN Books b ON o.BookID = b.BookID
    WHERE CAST(o.OrderID AS NVARCHAR) LIKE :search OR c.FirstName LIKE :search OR c.LastName LIKE :search OR b.Title LIKE :search
    """
    params = {"search": f'%{search}%'}
    
    # Add ORDER BY clause
    query += f" ORDER BY {order_by}"
    
    # Add OFFSET and FETCH for pagination
    query += f" OFFSET {(page - 1) * per_page} ROWS FETCH NEXT {per_page} ROWS ONLY"
    
    result = conn.execute(text(query), params)
    orders = result.fetchall()
    
    # Format dates and prices
    formatted_orders = []
    for order in orders:
        formatted_order = list(order)
        formatted_order[6] = order.OrderDate.strftime('%d/%m/%Y %H:%M:%S')  # Format date
        formatted_order[8] = f"£{order.TotalPrice:.2f}"  # Format price
        formatted_orders.append(formatted_order)
    
    # Fetch customers for the dropdown
    result = conn.execute(text("SELECT CustomerID, FirstName, LastName FROM Customers ORDER BY LastName, FirstName"))
    customers = result.fetchall()
    
    # Fetch books for the dropdown
    result = conn.execute(text("SELECT BookID, Title FROM Books ORDER BY Title"))
    books = result.fetchall()
    
    conn.close()
    
    return render_template('orders.html', orders=formatted_orders, customers=customers, books=books,
                           page=page, total_pages=total_pages, search=search, order_by=order_by)

@app.route('/add_country', methods=['POST'])
def add_country():
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'No JSON data received'}), 400

    new_country_name = data.get('country_name')

    if not new_country_name:
        return jsonify({'success': False, 'message': 'Country name is required'}), 400

    conn = get_db_connection()

    try:
        # Check if country already exists
        result = conn.execute(text("SELECT CountryID FROM Countries WHERE CountryName = :country_name"), {"country_name": new_country_name})
        existing_country = result.fetchone()

        if existing_country:
            return jsonify({'success': False, 'message': 'Country already exists'}), 400

        # Add new country
        result = conn.execute(text("INSERT INTO Countries (CountryName) OUTPUT INSERTED.CountryID VALUES (:country_name)"), {"country_name": new_country_name})
        new_country_id = result.fetchone()[0]
        conn.commit()

        return jsonify({'success': True, 'country_id': new_country_id}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        conn.close()

# @app.route('/DvlaSearch/')
# @app.route('/DvlaSearch')
# @app.route('/dvlasearch/')
# @app.route('/dvlasearch')
# def dvla_search():
#     return render_template('dvla_search.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8085))
    app.run(host='0.0.0.0', port=port, debug=True)