import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'cfl_secure_secret_key_12345'

DB_PATH = 'cfl_database_v6.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, genre, content, created_at FROM stories WHERE user_id = ? ORDER BY id DESC', (session['user_id'],))
    stories = cursor.fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ur" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>اردو ڈراما کہانیاں ڈیش بورڈ</title>
        <style>
            body { font-family: 'Jameel Noori Nastaleeq', 'Tahoma', sans-serif; background: #fdfbf7; color: #333; margin: 0; padding: 20px; direction: rtl; }
            .container { max-width: 900px; margin: auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
            h1 { color: #8b0000; text-align: center; margin-bottom: 25px; }
            .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; border-bottom: 2px solid #eee; padding-bottom: 15px; }
            .btn { background: #8b0000; color: #fff; padding: 10px 20px; border: none; border-radius: 6px; text-decoration: none; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #a52a2a; }
            .btn-logout { background: #555; }
            .btn-logout:hover { background: #333; }
            .story-card { background: #faf8f5; border: 1px solid #e3dcd2; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
            .story-title { color: #8b0000; font-size: 20px; margin-bottom: 5px; }
            .story-genre { font-size: 13px; color: #666; background: #eee; padding: 3px 8px; border-radius: 4px; display: inline-block; margin-bottom: 10px; }
            .story-content { white-space: pre-wrap; line-height: 1.8; color: #444; }
            form { display: flex; flex-direction: column; gap: 15px; }
            input, select, textarea { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; font-family: inherit; box-sizing: border-box; }
            textarea { height: 180px; resize: vertical; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="top-bar">
                <span>خوش آمدید، <strong>{{ username }}</strong></span>
                <div>
                    <a href="{{ url_for('add_story') }}" class="btn">نئی کہانی شامل کریں</a>
                    <a href="{{ url_for('logout') }}" class="btn btn-logout">لاگ آؤٹ</a>
                </div>
            </div>
            <h1>اردو ڈراما کہانیاں ڈیش بورڈ</h1>
            {% if stories %}
                {% for story in stories %}
                    <div class="story-card">
                        <div class="story-title">{{ story[1] }}</div>
                        <div class="story-genre">صنف: {{ story[2] }}</div>
                        <div class="story-content">{{ story[3] }}</div>
                    </div>
                {% endfor %}
            {% else %}
                <p style="text-align: center; color: #777;">ابھی تک کوئی کہانی شامل نہیں کی گئی۔ اوپر دیے گئے بٹن سے نئی کہانی شامل کریں!</p>
            {% endif %}
        </div>
    </body>
    </html>
    ''', username=session.get('username'), stories=stories)

@app.route('/add', methods=['GET', 'POST'])
def add_story():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        genre = request.form.get('genre')
        content = request.form.get('content')
        
        if title and content:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO stories (user_id, title, genre, content) VALUES (?, ?, ?, ?)', 
                           (session['user_id'], title, genre, content))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
            
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ur" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>نئی کہانی شامل کریں</title>
        <style>
            body { font-family: 'Jameel Noori Nastaleeq', 'Tahoma', sans-serif; background: #fdfbf7; color: #333; margin: 0; padding: 20px; direction: rtl; }
            .container { max-width: 700px; margin: auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
            h1 { color: #8b0000; text-align: center; margin-bottom: 25px; }
            form { display: flex; flex-direction: column; gap: 15px; }
            label { font-weight: bold; color: #444; }
            input, select, textarea { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; font-family: inherit; box-sizing: border-box; }
            textarea { height: 200px; resize: vertical; }
            .btn { background: #8b0000; color: #fff; padding: 12px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; text-align: center; }
            .btn:hover { background: #a52a2a; }
            .back-link { display: block; text-align: center; margin-top: 15px; color: #666; text-decoration: none; }
            .back-link:hover { color: #333; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>نئی کہانی یا اسکرپٹ شامل کریں</h1>
            <form method="POST">
                <div>
                    <label>عنوان (Title):</label>
                    <input type="text" name="title" required placeholder="کہانی یا ڈرامے کا نام...">
                </div>
                <div>
                    <label>صنف (Genre):</label>
                    <select name="genre">
                        <option value="رومانوی (Romance)">رومانوی (Romance)</option>
                        <option value="سسپنس (Suspense)">سسپنس (Suspense)</option>
                        <option value="خاندانی ڈراما (Family Drama)">خاندانی ڈراما (Family Drama)</option>
                        <option value="جذباتی (Emotional)">جذباتی (Emotional)</option>
                    </select>
                </div>
                <div>
                    <label>تفصیل / اسکرپٹ (Content):</label>
                    <textarea name="content" required placeholder="یہاں اپنی کہانی یا سین لکھیں..."></textarea>
                </div>
                <button type="submit" class="btn">کہانی محفوظ کریں</button>
            </form>
            <a href="{{ url_for('index') }}" class="back-link">← واپس ڈیش بورڈ پر جائیں</a>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[1] == password:
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'نام یا پاس ورڈ غلط ہے!'
            
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ur" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لاگ ان - اردو ڈراما کہانیاں</title>
        <style>
            body { font-family: 'Jameel Noori Nastaleeq', 'Tahoma', sans-serif; background: #fdfbf7; color: #333; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; direction: rtl; }
            .card { background: #fff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); width: 100%; max-width: 400px; }
            h2 { color: #8b0000; text-align: center; margin-bottom: 25px; }
            form { display: flex; flex-direction: column; gap: 15px; }
            input { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; font-family: inherit; box-sizing: border-box; }
            .btn { background: #8b0000; color: #fff; padding: 12px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
            .btn:hover { background: #a52a2a; }
            .error { color: #d9534f; background: #fdf2f2; padding: 10px; border-radius: 6px; text-align: center; margin-bottom: 15px; }
            .register-link { text-align: center; margin-top: 15px; font-size: 14px; }
            .register-link a { color: #8b0000; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>لاگ ان کریں</h2>
            {% if error %}
                <div class="error">{{ error }}</div>
            {% endif %}
            <form method="POST">
                <input type="text" name="username" required placeholder="یوزر نیم...">
                <input type="password" name="password" required placeholder="پاس ورڈ...">
                <button type="submit" class="btn">لاگ ان</button>
            </form>
            <div class="register-link">
                اکاؤنٹ نہیں ہے؟ <a href="{{ url_for('register') }}">نیا اکاؤنٹ بنائیں</a>
            </div>
        </div>
    </body>
    </html>
    ''', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = 'یہ یوزر نیم پہلے سے موجود ہے، کوئی اور چنیں!'
            
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ur" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>رجسٹر - اردو ڈراما کہانیاں</title>
        <style>
            body { font-family: 'Jameel Noori Nastaleeq', 'Tahoma', sans-serif; background: #fdfbf7; color: #333; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; direction: rtl; }
            .card { background: #fff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); width: 100%; max-width: 400px; }
            h2 { color: #8b0000; text-align: center; margin-bottom: 25px; }
            form { display: flex; flex-direction: column; gap: 15px; }
            input { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; font-family: inherit; box-sizing: border-box; }
            .btn { background: #8b0000; color: #fff; padding: 12px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
            .btn:hover { background: #a52a2a; }
            .error { color: #d9534f; background: #fdf2f2; padding: 10px; border-radius: 6px; text-align: center; margin-bottom: 15px; }
            .login-link { text-align: center; margin-top: 15px; font-size: 14px; }
            .login-link a { color: #8b0000; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>نیا اکاؤنٹ بنائیں</h2>
            {% if error %}
                <div class="error">{{ error }}</div>
            {% endif %}
            <form method="POST">
                <input type="text" name="username" required placeholder="یوزر نیم منتخب کریں...">
                <input type="password" name="password" required placeholder="پاس ورڈ درج کریں...">
                <button type="submit" class="btn">رجسٹر کریں</button>
            </form>
            <div class="login-link">
                پہلے سے اکاؤنٹ ہے؟ <a href="{{ url_for('login') }}">لاگ ان کریں</a>
            </div>
        </div>
    </body>
    </html>
    ''', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
