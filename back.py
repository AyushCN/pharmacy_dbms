from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production!

# Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',  # Change this
    'database': 'pharmacy_db'
}

# Helper Function: Database Connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Initialize database tables
def initialize_database():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Create users table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer (
                    customer_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(15) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create medicines table - CORRECTED to use quantity_in_stock
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medicine (
                    medicine_id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    category VARCHAR(50),
                    price DECIMAL(10,2) NOT NULL,
                    expiry_date DATE NOT NULL,
                    quantity_in_stock INT NOT NULL,
                    c_id VARCHAR(10)
                )
            """)
            
            # Create supplier table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supplier (
                    supplier_id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    contact VARCHAR(15) NOT NULL,
                    address TEXT
                )
            """)
            
            # Create purchases table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchases (
                    purchase_id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    medicine_id VARCHAR(10) NOT NULL,
                    quantity INT NOT NULL,
                    total_price DECIMAL(10,2) NOT NULL,
                    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
                    FOREIGN KEY (medicine_id) REFERENCES medicine(medicine_id)
                )
            """)
            
            # Create at least one admin user if none exists
            cursor.execute("SELECT * FROM customer WHERE is_admin = TRUE")
            if not cursor.fetchone():
                hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
                cursor.execute(
                    "INSERT INTO customer (name, email, phone, password, is_admin) VALUES (%s, %s, %s, %s, %s)",
                    ('Admin', 'admin@pharmacy.com', '1234567890', hashed_password, True)
                )
            
            conn.commit()
        except Error as e:
            print(f"Error initializing database: {e}")
        finally:
            cursor.close()
            conn.close()

# Initialize the database when the app starts
initialize_database()

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    return render_template('admin_dashboard.html')

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'customer_id' not in session:
        return redirect(url_for('home'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT supplier_id, name FROM supplier")
    suppliers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customer_dashboard.html', suppliers=suppliers)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))

# Authentication endpoints
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    # Validation
    if not all([name, email, phone, password, confirm_password]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'}), 400

    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if customer already exists
        cursor.execute("SELECT * FROM customer WHERE email = %s OR phone = %s", (email, phone))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email or phone already registered'}), 400

        # Insert new customer
        cursor.execute(
            "INSERT INTO customer (name, phone, email, password) VALUES (%s, %s, %s, %s)",
            (name, phone, email, hashed_password)
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Account created successfully!'})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

    if not (email or phone) or not password:
        return jsonify({'success': False, 'message': 'Email/phone and password required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = conn.cursor(dictionary=True)
    try:
        if email:
            cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT * FROM customer WHERE phone = %s", (phone,))

        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            session['customer_id'] = user['customer_id']
            session['user_email'] = user['email']
            session['is_admin'] = user['is_admin']
            return jsonify({
                'success': True, 
                'message': 'Login successful!', 
                'is_admin': bool(user['is_admin'])
            })
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/medicines', methods=['GET'])
def get_medicines():
    if 'customer_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    supplier_id = request.args.get('supplier_id')
    if not supplier_id:
        return jsonify({'error': 'Supplier ID required'}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.*, s.name as supplier_name 
            FROM medicine m
            LEFT JOIN supplier s ON m.c_id = s.supplier_id
            WHERE m.c_id = %s AND m.quantity_in_stock > 0
        """, (supplier_id,))
        medicines = cursor.fetchall()
        return jsonify(medicines)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@app.route('/medicines', methods=['POST'])
def add_medicine():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    required_fields = ['medicine_id', 'name', 'price', 'quantity_in_stock', 'expiry_date', 'c_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO medicine 
            (medicine_id, name, category, price, quantity_in_stock, expiry_date, c_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data['medicine_id'],
            data['name'],
            data.get('category'),
            data['price'],
            data['quantity_in_stock'],
            data['expiry_date'],
            data['c_id']
        ))
        conn.commit()
        return jsonify({'success': True, 'message': 'Medicine added'})
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@app.route('/purchase', methods=['POST'])
def purchase_medicine():
    if 'customer_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    try:
        medicine_id = data['medicine_id']
        quantity = int(data['quantity'])
        if quantity <= 0:
            raise ValueError
    except (KeyError, ValueError):
        return jsonify({'error': 'Invalid quantity'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()
        
        # Check stock
        cursor.execute("""
            SELECT quantity_in_stock, price, name 
            FROM medicine 
            WHERE medicine_id = %s FOR UPDATE
        """, (medicine_id,))
        medicine = cursor.fetchone()
        
        if not medicine:
            return jsonify({'error': 'Medicine not found'}), 404
        if medicine['quantity_in_stock'] < quantity:
            return jsonify({
                'error': f'Only {medicine["quantity_in_stock"]} available'
            }), 400

        # Update stock
        cursor.execute("""
            UPDATE medicine 
            SET quantity_in_stock = quantity_in_stock - %s 
            WHERE medicine_id = %s
        """, (quantity, medicine_id))

        # Record purchase
        total = medicine['price'] * quantity
        cursor.execute("""
            INSERT INTO purchases 
            (customer_id, medicine_id, quantity, total_price) 
            VALUES (%s, %s, %s, %s)
        """, (session['customer_id'], medicine_id, quantity, total))
        
        conn.commit()
        return jsonify({
            'success': True,
            'message': f'Purchased {quantity} {medicine["name"]} for ${total:.2f}'
        })
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@app.route('/test_medicines')
def show_medicines():
    if 'customer_id' not in session:
        return redirect(url_for('login'))
    
    supplier_id = request.args.get('supplier_id')
    if not supplier_id:
        return redirect(url_for('customer_dashboard'))
    
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', message='Database connection failed'), 500
        
    cursor = conn.cursor(dictionary=True)
    try:
        # Get supplier name
        cursor.execute("SELECT name FROM supplier WHERE supplier_id = %s", (supplier_id,))
        supplier = cursor.fetchone()
        
        # Get medicines with supplier name
        cursor.execute("""
            SELECT m.*, s.name as supplier_name 
            FROM medicine m
            LEFT JOIN supplier s ON m.c_id = s.supplier_id
            WHERE m.c_id = %s AND m.quantity_in_stock > 0
            ORDER BY m.name
        """, (supplier_id,))
        medicines = cursor.fetchall()
        
        # Format expiry dates properly
        for med in medicines:
            if isinstance(med['expiry_date'], str):
                med['expiry_date'] = datetime.strptime(med['expiry_date'], '%Y-%m-%d').date()
        
        return render_template(
            'medicines.html',
            medicines=medicines,
            supplier_name=supplier['name'] if supplier else 'Unknown Supplier'
        )
    except Error as e:
        print(f"Database error: {e}")
        return render_template('error.html', message='Error loading medicines'), 500
    finally:
        cursor.close()
        conn.close()



@app.route('/checkout')
def checkout():
    # Retrieve the cart from session and show the checkout form
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart_view'))  # Redirect to cart if empty

    return render_template('checkout.html', cart=cart)


    
app.route('/update_cart_item', methods=['POST'])
def update_cart_item():
    data = request.get_json()
    medicine_id = data.get('medicine_id')
    quantity = data.get('quantity')

    # Logic to update the cart in the session
    if 'cart' not in session:
        return jsonify({"success": False, "message": "No cart found."}), 400

    cart = session['cart']

    # Find the item in the cart and update quantity
    if medicine_id in cart:
        if quantity <= 0:
            del cart[medicine_id]
        else:
            cart[medicine_id]['quantity'] = quantity
    else:
        return jsonify({"success": False, "message": "Item not found in cart."}), 400

    session['cart'] = cart
    return jsonify({"success": True, "message": "Cart updated."})



@app.route('/buy.html')
def buy_single1():
    medicine_id = request.args.get('medicine_id')
    quantity = request.args.get('quantity', type=int, default=1)
    
    # Find the selected medicine
    medicine = next((m for m in medicines if m['medicine_id'] == medicine_id), None)
    
    if not medicine:
        return redirect(url_for('index'))  # Redirect to the main page if medicine not found
    
    return render_template('buy.html', medicine=medicine, quantity=quantity)


@app.route('/api/cart/count', methods=['GET'])
def cart_count():
    # Return the total quantity of items in the cart
    cart = session.get('cart', {})
    total_count = sum(item['quantity'] for item in cart.values())
    return jsonify({"count": total_count})
    
    
    
    



@app.route('/cart')
def view_cart():
    # Check if user is logged in (using session)
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Retrieve the cart and cart items for this customer
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Query to fetch cart details along with cart items and medicine information
    query = '''
    SELECT c.cart_id, ci.cart_item_id, m.medicine_id, m.name, m.price, ci.quantity
    FROM cart c
    JOIN cart_items ci ON c.cart_id = ci.cart_id
    JOIN medicine m ON ci.medicine_id = m.medicine_id
    WHERE c.customer_id = %s
    '''
    cursor.execute(query, (customer_id,))
    cart_items = cursor.fetchall()

    conn.close()

    # If no cart items found
    if not cart_items:
        return render_template('cart.html', cart_items=[], message="Your cart is empty.")

    # Calculate subtotal
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)

    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401

    data = request.get_json()
    medicine_id = data.get('medicine_id')
    quantity = data.get('quantity', 1)

    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be at least 1'}), 400
    except Exception:
        return jsonify({'success': False, 'message': 'Invalid quantity'}), 400

    customer_id = session['customer_id']
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        # Check medicine exists and stock
        cursor.execute("SELECT quantity_in_stock FROM medicine WHERE medicine_id = %s", (medicine_id,))
        med = cursor.fetchone()
        if not med:
            return jsonify({'success': False, 'message': 'Medicine not found'}), 404
        if med['quantity_in_stock'] < quantity:
            return jsonify({'success': False, 'message': f'Only {med["quantity_in_stock"]} in stock'}), 400

        # Find or create cart for this customer
        cursor.execute("SELECT cart_id FROM cart WHERE customer_id = %s", (customer_id,))
        cart = cursor.fetchone()
        if not cart:
            cursor.execute("INSERT INTO cart (customer_id) VALUES (%s)", (customer_id,))
            conn.commit()
            cart_id = cursor.lastrowid
        else:
            cart_id = cart['cart_id']

        # Check if item already in cart
        cursor.execute("SELECT cart_item_id, quantity FROM cart_items WHERE cart_id = %s AND medicine_id = %s", (cart_id, medicine_id))
        item = cursor.fetchone()
        if item:
            # Check if adding would exceed stock
            if item['quantity'] + quantity > med['quantity_in_stock']:
                return jsonify({'success': False, 'message': f'Cannot add more than {med["quantity_in_stock"]} in total'}), 400
            cursor.execute("UPDATE cart_items SET quantity = quantity + %s WHERE cart_item_id = %s", (quantity, item['cart_item_id']))
        else:
            cursor.execute("INSERT INTO cart_items (cart_id, medicine_id, quantity) VALUES (%s, %s, %s)", (cart_id, medicine_id, quantity))
        conn.commit()

        # Update session cart for cart count API
        session_cart = session.get('cart', {})
        medicine_id_str = str(medicine_id)
        if medicine_id_str in session_cart:
            session_cart[medicine_id_str]['quantity'] += quantity
        else:
            session_cart[medicine_id_str] = {'quantity': quantity}
        session['cart'] = session_cart

        return jsonify({'success': True})
    except Exception as e:
        print("Add to cart error:", e)
        conn.rollback()
        return jsonify({'success': False, 'message': f'Could not add to cart: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()





@app.route('/buy')
def buy_cart():
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = '''
    SELECT m.medicine_id, m.name, m.price, ci.quantity
    FROM cart c
    JOIN cart_items ci ON c.cart_id = ci.cart_id
    JOIN medicine m ON ci.medicine_id = m.medicine_id
    WHERE c.customer_id = %s
    '''
    cursor.execute(query, (customer_id,))
    cart_items = cursor.fetchall()
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    conn.close()

    return render_template('buy.html', cart_items=cart_items, order_total=subtotal)




@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401

    customer_id = session['customer_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get cart_id
        cursor.execute("SELECT cart_id FROM cart WHERE customer_id = %s", (customer_id,))
        cart = cursor.fetchone()
        if not cart:
            return jsonify({'success': False, 'message': 'Cart not found.'}), 400
        cart_id = cart['cart_id']

        # Get all cart items
        cursor.execute("""
            SELECT medicine_id, quantity
            FROM cart_items
            WHERE cart_id = %s
        """, (cart_id,))
        cart_items = cursor.fetchall()

        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty.'}), 400

        # For each item, insert into purchases and update stock
        for item in cart_items:
            # Insert into purchases
            cursor.execute("""
                INSERT INTO purchases (customer_id, medicine_id, quantity, total_price)
                SELECT %s, %s, %s, price * %s FROM medicine WHERE medicine_id = %s
            """, (customer_id, item['medicine_id'], item['quantity'], item['quantity'], item['medicine_id']))
            # Decrease stock
            cursor.execute("""
                UPDATE medicine SET quantity_in_stock = quantity_in_stock - %s
                WHERE medicine_id = %s AND quantity_in_stock >= %s
            """, (item['quantity'], item['medicine_id'], item['quantity']))
            # Optional: check if stock went negative (should not happen)
            cursor.execute("SELECT quantity_in_stock FROM medicine WHERE medicine_id = %s", (item['medicine_id'],))
            stock = cursor.fetchone()
            if stock and stock['quantity_in_stock'] < 0:
                conn.rollback()
                return jsonify({'success': False, 'message': 'Not enough stock for some items.'}), 400

        # Remove all items from cart
        cursor.execute("DELETE FROM cart_items WHERE cart_id = %s", (cart_id,))
        conn.commit()

        # Clear session cart
        session['cart'] = {}

        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        print("Order confirmation error:", e)
        return jsonify({'success': False, 'message': 'Order failed.'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/buy_single/<medicine_id>', methods=['GET'])
def buy_single(medicine_id):
    if 'customer_id' not in session:
        return redirect(url_for('login'))
    quantity = int(request.args.get('quantity', 1))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT m.*, s.name as supplier_name FROM medicine m LEFT JOIN supplier s ON m.c_id = s.supplier_id WHERE m.medicine_id = %s", (medicine_id,))
    medicine = cursor.fetchone()
    conn.close()
    if not medicine:
        return redirect(url_for('customer_dashboard'))
    order_total = medicine['price'] * quantity
    return render_template('buy_single.html', medicine=medicine, quantity=quantity, order_total=order_total)
@app.route('/confirm_single_order', methods=['POST'])
def confirm_single_order():
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401

    data = request.get_json()
    medicine_id = data.get('medicine_id')
    quantity = int(data.get('quantity', 1))
    customer_id = session['customer_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check stock
        cursor.execute("SELECT price, quantity_in_stock FROM medicine WHERE medicine_id = %s", (medicine_id,))
        med = cursor.fetchone()
        if not med:
            return jsonify({'success': False, 'message': 'Medicine not found.'}), 404
        if med['quantity_in_stock'] < quantity:
            return jsonify({'success': False, 'message': f'Only {med['quantity_in_stock']} in stock.'}), 400

        # Insert into purchases
        total_price = med['price'] * quantity
        cursor.execute(
            "INSERT INTO purchases (customer_id, medicine_id, quantity, total_price) VALUES (%s, %s, %s, %s)",
            (customer_id, medicine_id, quantity, total_price)
        )
        # Decrease stock
        cursor.execute(
            "UPDATE medicine SET quantity_in_stock = quantity_in_stock - %s WHERE medicine_id = %s",
            (quantity, medicine_id)
        )
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        print("Buy single error:", e)
        return jsonify({'success': False, 'message': 'Purchase failed.'}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
