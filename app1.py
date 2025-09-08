from flask import Flask, request, render_template, redirect, url_for, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = "my_secret_key"   # Needed for sessions if using flash

class UserDB:
    def connect(self):
        return mysql.connector.connect(host="localhost",user="root",passwd="",database="manav_database")

    def user_exists(self, username, email=None):
        db = self.connect()
        cursor = db.cursor()
        if email:
            sql = "SELECT * FROM users WHERE username=%s OR email=%s"
            cursor.execute(sql, (username, email))
        else:
            sql = "SELECT * FROM users WHERE username=%s"
            cursor.execute(sql, (username,))
        result = cursor.fetchone()
        db.close()
        return result is not None

    def save_user(self, fname, lname, country, phone, email, username, password):
        db = self.connect()
        cursor = db.cursor()
        sql = ("INSERT INTO users (First_Name, Last_Name, Country, Phone, Email, Username, Password) VALUES (%s, %s, %s, %s, %s, %s, %s)")
        cursor.execute(sql, (fname, lname, country, phone, email, username, password))
        db.commit()
        db.close()


@app.route('/')
def home():
    return render_template('Login.html')   # your login page


@app.route('/register')
def register_page():
    return render_template('Register.html')  # registration form


@app.route('/check_username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get("username")
    D = UserDB()
    exists = D.user_exists(username)
    return jsonify({"available": not exists})


@app.route('/register_user', methods=['POST'])
def register_user():
    fname = request.form["fname"]
    lname = request.form["lname"]
    country = request.form["country"]
    phone = request.form["phone"]
    email = request.form["email"]
    username = request.form["username"]
    password = request.form["password"]

    D = UserDB()

    # ❌ Check if username/email already exists
    if D.user_exists(username, email):
        return "Username or Email already exists. Please try again.", 400

    # ✅ Save user
    D.save_user(fname, lname, country, phone, email, username, password)

    # Redirect to login page after success
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
