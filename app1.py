from flask import Flask, request, render_template, redirect, url_for, jsonify, flash, session
import mysql.connector
# NEW: Import a password hashing library. werkzeug is already part of Flask.
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "a_very_secure_secret_key_should_be_used_here"

class UserDB:
    def connect(self):
        """Establishes a connection to the database."""
        return mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="autoledger project"
        )

    def _get_validated_table(self, role):
        """
        NEW: Validates the role to prevent SQL injection.
        This is a critical security step. It ensures only allowed table names are used.
        """
        allowed_tables = {
            "student": "student",
            "employee": "employ", # Assuming your table for employees is named 'employ'
            "shopkeeper": "shopkeeper"
        }
        return allowed_tables.get(role.lower()) # Return the table name if valid, otherwise None

    def user_exists(self, username, role, email=None):
        """CHANGED: Checks if a user exists in the correct table based on their role."""
        table_name = self._get_validated_table(role)
        if not table_name:
            # If the role is invalid, we can't check, so we assume non-existence for safety.
            return False

        db = self.connect()
        cursor = db.cursor()
        
        # Use an f-string safely because we have validated the table_name
        if email:
            sql = f"SELECT * FROM {table_name} WHERE username=%s OR email=%s"
            cursor.execute(sql, (username, email))
        else:
            sql = f"SELECT * FROM {table_name} WHERE username=%s"
            cursor.execute(sql, (username,))
        
        result = cursor.fetchone()
        db.close()
        return result is not None

    def save_user(self, fname, lname, country, phone, email, username, password, role):
        """CHANGED: Saves a user to the correct table based on their role."""
        table_name = self._get_validated_table(role)
        if not table_name:
            raise ValueError("Invalid role specified.") # Or handle the error more gracefully

        db = self.connect()
        cursor = db.cursor()
        
        # NEW: Hash the password before saving
        hashed_password = generate_password_hash(password)
        
        # Use an f-string safely because we have validated the table_name
        sql = (f"INSERT INTO {table_name} "
               "(First_Name, Last_Name, Country, Phone, Email, Username, Password) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s)")
        
        cursor.execute(sql, (fname, lname, country, phone, email, username, hashed_password))
        db.commit()
        db.close()

    def check_credentials(self, username, password, role):
        """NEW: Verifies user credentials against the correct table for login."""
        table_name = self._get_validated_table(role)
        if not table_name:
            return None # Invalid role

        db = self.connect()
        cursor = db.cursor(dictionary=True) # dictionary=True makes it easy to get columns by name
        
        sql = f"SELECT * FROM {table_name} WHERE username = %s"
        cursor.execute(sql, (username,))
        user = cursor.fetchone()
        db.close()
        
        if user and check_password_hash(user['Password'], password):
            return user # Password matches, return user data
        return None # User not found or password incorrect

# --- Flask Routes ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login_page():
    return render_template('Login.html')

@app.route('/register')
def register_page():
    return render_template('Register.html')

# --- Find and REPLACE this entire function in your app.py ---

@app.route('/login_user', methods=['POST'])
def login_user():
    """
    CHANGED: Handles login via JavaScript and returns a JSON response
    for the pop-up alert.
    """
    # Use .get() to avoid errors if a field is missing
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    # Basic validation
    if not all([username, password, role]):
        return jsonify({"success": False, "message": "Missing username, password, or role."})

    D = UserDB()
    user = D.check_credentials(username, password, role)
    
    if user:
        # User is authenticated, store info in the session
        session['username'] = user['Username']
        session['role'] = role
        
        # Return a SUCCESS JSON response
        return jsonify({
            "success": True, 
            "message": f"Successfully logged in! Welcome back, {user['Username']}.",
            "redirect_url": url_for('home') # URL to redirect to after pop-up
        })
    else:
        # Authentication failed, return an ERROR JSON response
        return jsonify({
            "success": False, 
            "message": "Invalid username, password, or role. Please try again."
        })

@app.route('/check_username', methods=['POST'])
def check_username():
    """CHANGED: Now requires a role to check the correct table."""
    data = request.get_json()
    username = data.get("username")
    role = data.get("role") # The frontend must send the role now

    if not role:
        # Cannot check without a role
        return jsonify({"available": False, "message": "Please select a role first."})

    D = UserDB()
    exists = D.user_exists(username, role)
    return jsonify({"available": not exists})

@app.route('/register_user', methods=['POST'])
def register_user():
    """CHANGED: Passes the role to the database methods."""
    fname = request.form["fname"]
    lname = request.form["lname"]
    country = request.form["country"]
    phone = request.form["phone"]
    email = request.form["email"]
    username = request.form["username"]
    password = request.form["password"]
    role = request.form["role"]

    D = UserDB()

    if D.user_exists(username, role, email):
        flash("Username or Email already exists for this role. Please try another.", "danger")
        return redirect(url_for('register_page'))

    D.save_user(fname, lname, country, phone, email, username, password, role)

    flash("Registration successful! Please log in.", "success")
    return redirect(url_for("login_page"))


if __name__ == "__main__":
    app.run(debug=True)