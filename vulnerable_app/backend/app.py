from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from pymysql.cursors import DictCursor
import os
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for Streamlit communication

# MySQL database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'university_portal'),
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

def init_db():
    """Initialize the MySQL database with users table"""
    try:
        # Connect without database first to create it
        conn_config = DB_CONFIG.copy()
        conn_config.pop('database')
        
        conn = pymysql.connect(**conn_config)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        conn.commit()
        cursor.close()
        conn.close()
        
        # Now connect to the database and create table
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create users table (intentionally vulnerable - no password hashing, plain storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS iilm_users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                department VARCHAR(255),
                role VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✓ Database initialized successfully")
        
    except Exception as e:
        print(f"✗ Database initialization error: {str(e)}")
        raise

def get_db_connection():
    """Get a MySQL database connection"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"✗ Database connection error: {str(e)}")
        raise

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Flask backend is running"}), 200

@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user - INTENTIONALLY VULNERABLE
    - Stores password in plain text (no hashing)
    - No input validation (vulnerable to SQL injection if not using parameterized queries)
    - However, SQLite3 with ? placeholders prevents SQL injection in this implementation
    """
    try:
        data = request.get_json()
        print("Data from front-end :", data)
        
        # Basic validation
        if not data.get('username') or not data.get('password'):
            return jsonify({"error": "Username and password are required"}), 400
        
        username = data.get('username')
        
        password = data.get('password')  # Stored in plain text - VULNERABILITY!
        # Hash the plain-text password before storing
        password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        department = data.get('department', 'Computer Science')
        role = data.get('role', 'Student')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Using parameterized query with pymysql
            cursor.execute("""
                INSERT INTO iilm_users (username, password, department, role)
                VALUES (%s, %s, %s, %s)
            """, (username, password, department, role))
            
            conn.commit()
            user_id = cursor.lastrowid
            cursor.close()
            conn.close()
            
            return jsonify({
                "message": "User registered successfully",
                "user_id": user_id,
                "username": username,
                "department": department,
                "role": role
            }), 201
            
        except pymysql.IntegrityError as e:
            cursor.close()
            conn.close()
            return jsonify({"error": "Username already exists"}), 400
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({"error": str(e)}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """
    Login a user - INTENTIONALLY VULNERABLE
    - Password stored in plain text (no hashing comparison)
    - No rate limiting on login attempts
    """
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({"error": "Username and password are required"}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Using parameterized query to fetch user
        cursor.execute("""
            SELECT * FROM users WHERE username = %s
        """, (username,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and user['password'] == password:  # Plain text password comparison - VULNERABILITY!
            # Return user data
            return jsonify({
                "message": "Login successful",
                "user_id": user['id'],
                "username": user['username'],
                "department": user['department'],
                "role": user['role'],
                "created_at": str(user['created_at']) if user['created_at'] else None
            }), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search-user', methods=['POST'])
def search_user():
    """
    Search for user by username - HIGHLY VULNERABLE TO SQL INJECTION
    This endpoint demonstrates SQL injection vulnerability
    """
    try:
        data = request.get_json()
        search_query = data.get('username', '')
        
        if not search_query:
            return jsonify({"error": "Search query is required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # INTENTIONAL SQL INJECTION VULNERABILITY
        # This would be vulnerable if used with string formatting instead of parameterized queries
        # For demo purposes, we'll show what vulnerable code would look like:
        # cursor.execute(f"SELECT * FROM users WHERE username LIKE '%{search_query}%'")
        
        # However, this implementation uses parameterized query (safer):
        cursor.execute("""
            SELECT id, username, department, role FROM users 
            WHERE username LIKE %s
        """, (f'%{search_query}%',))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if results:
            return jsonify({
                "message": "Users found",
                "count": len(results),
                "users": results
            }), 200
        else:
            return jsonify({"message": "No users found", "count": 0, "users": []}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-all-users', methods=['GET'])
def get_all_users():
    """
    Get all users from database - MAJOR VULNERABILITY
    Returns all user data without authentication
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "All users retrieved",
            "count": len(users),
            "users": users
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete user - NO AUTHENTICATION REQUIRED - MAJOR VULNERABILITY
    Anyone can delete any user without proper authorization
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            cursor.close()
            conn.close()
            return jsonify({"message": "User deleted successfully"}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Initialize MySQL database
    try:
        init_db()
    except Exception as e:
        print(f"✗ Failed to initialize database: {str(e)}")
    
    print("=" * 60)
    print("🚨 VULNERABLE APP FLASK BACKEND 🚨")
    print("=" * 60)
    print("This backend intentionally contains vulnerabilities:")
    print("✗ Passwords stored in plain text (no hashing)")
    print("✗ No authentication on sensitive endpoints")
    print("✗ No rate limiting on login attempts")
    print("=" * 60)
    print(f"Starting Flask server on http://localhost:5009")
    print(f"Database: MySQL ({DB_CONFIG['database']})")
    print("=" * 60)
    
    app.run(debug=True, host='localhost', port=5009)
