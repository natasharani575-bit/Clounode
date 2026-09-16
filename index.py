import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Vercel کے لیے سیف ڈیٹا بیس پاتھ
DB_PATH = '/tmp/database.db'

def init_db():
    # اگر ٹمپریری فولڈر میں ڈیٹا بیس نہ ہو تو نیا بنا لیں
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # یوزرز ٹیبل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password TEXT,
                balance REAL DEFAULT 0.0,
                level INTEGER DEFAULT 1
            )
        ''')
        # سیٹنگز ٹیبل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        conn.commit()
        conn.close()

init_db()

@app.route('/')
def home():
    return "CFL Investment Platform is Live and Running!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user'] = email
            return redirect(url_for('dashboard'))
        return "Invalid Credentials, please try again."
        
    return '''
        <h2>Login</h2>
        <form method="POST">
            Email: <input type="email" name="email"><br><br>
            Password: <input type="password" name="password"><br><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return f"Welcome to your Dashboard, {session['user']}! Platform is working perfectly."

if __name__ == '__main__':
    app.run(debug=True)
