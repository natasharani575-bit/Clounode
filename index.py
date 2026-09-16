import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'cfl_secure_secret_key_12345'

DB_PATH = '/tmp/cfl_database_v3.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0.00,
            status TEXT DEFAULT 'Active',
            is_admin INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            amount REAL NOT NULL,
            screenshot TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            message TEXT NOT NULL,
            sender TEXT NOT NULL
        )
    ''')
    cursor.execute("SELECT * FROM users WHERE phone = '03000000000'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (phone, email, password, balance, is_admin) VALUES ('03000000000', 'admin@cfl.com', 'admin123', 0.00, 1)")
    conn.commit()
    conn.close()

init_db()

BASE_HTML = """
<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFL Investment Platform</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Tahoma, sans-serif; }
        body { background-color: #0b141a; color: #fff; padding: 20px; }
        .container { max-width: 480px; margin: 0 auto; background: #111b21; border-radius: 15px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h2, h3 { text-align: center; color: #00a884; margin-bottom: 20px; }
        input, select, textarea { width: 100%; padding: 12px; margin: 10px 0; background: #222d34; border: 1px solid #3b4a54; color: #fff; border-radius: 8px; }
        button { width: 100%; padding: 12px; background: #00a884; border: none; color: white; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 10px; }
        button:hover { background: #008f6f; }
        .btn-danger { background: #d9534f; }
        .btn-danger:hover { background: #c9302c; }
        .card { background: #202c33; padding: 15px; border-radius: 10px; margin-bottom: 15px; text-align: center; }
        .balance { font-size: 28px; color: #25d366; font-weight: bold; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
        .menu-btn { background: #2a3942; padding: 15px; border-radius: 10px; text-align: center; text-decoration: none; color: #fff; display: block; font-weight: bold; border: 1px solid #3b4a54; }
        .menu-btn:hover { background: #374248; }
        .chat-box { background: #0b141a; height: 150px; overflow-y: scroll; padding: 10px; border-radius: 8px; border: 1px solid #3b4a54; text-align: right; margin-bottom: 10px; }
        .msg { padding: 5px 10px; margin: 5px 0; border-radius: 5px; font-size: 14px; }
        .user-msg { background: #005c4b; text-align: right; }
        .admin-msg { background: #202c33; text-align: left; }
        a { color: #00a884; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        %CONTENT%
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE phone = ? AND password = ?", (phone, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['phone'] = phone
            if user[6] == 1:
                return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        else:
            error = "غلط موبائل نمبر یا پاس ورڈ!"
            
    content = f'''
        <h2>CFL لاگ ان کریں</h2>
        <p style="color: #ff5c5c; text-align: center;">{error}</p>
        <form method="POST">
            <input type="text" name="phone" placeholder="موبائل نمبر درج کریں" required>
            <input type="password" name="password" placeholder="پاس ورڈ درج کریں" required>
            <button type="submit">لاگ ان</button>
        </form>
        <p style="text-align: center; margin-top: 15px;">اکاؤنٹ نہیں ہے؟ <a href="/register">رجسٹر کریں</a></p>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ""
    if request.method == 'POST':
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (phone, email, password, balance) VALUES (?, ?, ?, 0.00)", (phone, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = "یہ موبائل نمبر پہلے سے رجسٹرڈ ہے!"
            
    content = f'''
        <h2>CFL نیا اکاؤنٹ</h2>
        <p style="color: #ff5c5c; text-align: center;">{error}</p>
        <form method="POST">
            <input type="text" name="phone" placeholder="موبائل نمبر لکھیں (مثلاً 0300...)" required>
            <input type="email" name="email" placeholder="اپنی جی میل (Email) لکھیں" required>
            <input type="password" name="password" placeholder="پاس ورڈ چنیں" required>
            <button type="submit">اکاؤنٹ بنائیں (بیلنس: $0.00)</button>
        </form>
        <p style="text-align: center; margin-top: 15px;">پہلے سے اکاؤنٹ ہے؟ <a href="/">لاگ ان کریں</a></p>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/dashboard')
def dashboard():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    phone = session['phone']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    user = cursor.fetchone()
    
    cursor.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 10")
    messages = cursor.fetchall()[::-1]
    conn.close()
    
    msg_html = ""
    for m in messages:
        m_class = "user-msg" if m[3] == 'user' else "admin-msg"
        msg_html += f'<div class="msg {m_class}"><b>{m[1]}:</b> {m[2]}</div>'
    
    bal = f"${user[4]:.2f}" if user else "$0.00"
    
    content = f'''
        <div class="card">
            <p style="font-size: 14px; color: #8696a0;">موجودہ بیلنس</p>
            <div class="balance">{bal}</div>
            <p style="font-size: 13px; color: #ffa700; margin-top: 5px;">اسٹیٹس: انویسٹمنٹ پینڈنگ / تصدیق کا انتظار ہے</p>
        </div>

        <div class="grid">
            <a href="/withdraw" class="menu-btn">💸 Withdraw<br><span style="font-size:11px; color:#8696a0;">رقم نکلوانا</span></a>
            <a href="/topup" class="menu-btn">💳 Top Up<br><span style="font-size:11px; color:#8696a0;">انویسٹمنٹ کریں</span></a>
            <a href="/cashwill" class="menu-btn">🎡 Cash Will<br><span style="font-size:11px; color:#8696a0;">اسپن اینڈ ون ($6)</span></a>
            <a href="/tasks" class="menu-btn">📋 Daily Tasks<br><span style="font-size:11px; color:#8696a0;">روزانہ ٹاسک ($0.35)</span></a>
        </div>

        <div class="card" style="margin-top: 20px; text-align: right;">
            <h4 style="color: #00a884; margin-bottom: 10px;">💬 ایڈمن لائیو چیٹ</h4>
            <div class="chat-box">{msg_html}</div>
            <form method="POST" action="/send_message">
                <input type="text" name="message" placeholder="پیغام لکھیں..." required style="margin: 5px 0;">
                <button type="submit" style="padding: 8px;">بھیجیں</button>
            </form>
        </div>

        <a href="/logout"><button class="btn-danger" style="margin-top: 15px;">لاگ آؤٹ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/topup', methods=['GET', 'POST'])
def topup():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        amount = request.form['amount']
        screenshot = request.form['screenshot']
        phone = session['phone']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO topups (phone, amount, screenshot, status) VALUES (?, ?, ?, 'Pending')", (phone, amount, screenshot))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    
    content = '''
        <h2>Top Up / انویسٹمنٹ</h2>
        <div class="card">
            <p style="font-size: 13px; color: #8696a0;">آپ کا ایڈمن کرپٹو والٹ ایڈریس:</p>
            <p style="background: #111b21; padding: 10px; border-radius: 5px; font-family: monospace; color: #00a884; word-break: break-all; margin: 10px 0;">
                <b>USDT (TRC20):</b> TXYZ123456789ABCDEFCryptoWalletAddress
            </p>
            <p style="font-size: 12px; color: #ffa700;">ڈالر بھیجنے کے بعد نیچے رقم اور اسکرین شاٹ کا نام درج کریں:</p>
        </div>
        <form method="POST">
            <input type="number" step="0.01" name="amount" placeholder="ڈالر کی رقم (مثلاً 50)" required>
            <input type="text" name="screenshot" placeholder="اسکرین شاٹ کا نام (مثلاً proof.jpg)" required>
            <button type="submit">تصدیق کے لیے بھیجیں</button>
        </form>
        <br><a href="/dashboard"><button style="background: #2a3942;">واپس ڈیش بورڈ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/cashwill', methods=['GET', 'POST'])
def cashwill():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        phone = session['phone']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + 6.00 WHERE phone = ?", (phone,))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
        
    content = '''
        <h2>🎡 Cash Will (اسپن اینڈ ون)</h2>
        <div class="card">
            <p>اسپن کریں اور اپنی مقرر کردہ رقم جیتیں!</p>
            <h3 style="color: #25d366; margin: 15px 0;">مقررہ وننگ لمٹ: $6.00</h3>
            <form method="POST">
                <button type="submit">اسپن کریں (Spin Now)</button>
            </form>
        </div>
        <a href="/dashboard"><button style="background: #2a3942;">واپس ڈیش بورڈ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        phone = session['phone']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + 0.35 WHERE phone = ?", (phone,))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
        
    content = '''
        <h2>📋 Daily Tasks</h2>
        <div class="card">
            <p>آج کا دستیاب ٹاسک: مکمل کریں اور $0.35 حاصل کریں۔</p>
            <form method="POST">
                <button type="submit">ٹاسک مکمل کریں</button>
            </form>
        </div>
        <a href="/dashboard"><button style="background: #2a3942;">واپس ڈیش بورڈ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        return redirect(url_for('dashboard'))
        
    content = '''
        <h2>💸 Withdraw (رقم نکلوانا)</h2>
        <div class="card">
            <p>اپنا کرپٹو والٹ ایڈریس اور رقم درج کریں:</p>
            <form method="POST">
                <input type="number" step="0.01" name="amount" placeholder="رقم درج کریں ($)" required>
                <input type="text" name="wallet" placeholder="آپ کا والٹ ایڈریس" required>
                <button type="submit">ودڈرا کی درخواست بھیجیں</button>
            </form>
        </div>
        <a href="/dashboard"><button style="background: #2a3942;">واپس ڈیش بورڈ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    message = request.form['message']
    phone = session['phone']
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (phone, message, sender) VALUES (?, ?, 'user')", (phone, message))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin_panel():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topups WHERE status = 'Pending'")
    topups = cursor.fetchall()
    conn.close()
    
    topup_html = ""
    if topups:
        for t in topups:
            topup_html += f'<p>موبائل: <b>{t[1]}</b> | رقم: <b>${t[2]}</b> | ثبوت: {t[3]}</p>'
            topup_html += f'<a href="/admin/approve/{t[0]}"><button style="padding: 5px; margin: 5px 0; background: #25d366;">اپروو کریں (Approve)</button></a>'
            topup_html += '<hr style="border-color: #3b4a54; margin: 10px 0;">'
    else:
        topup_html = '<p style="color: #8696a0;">کوئی نئی پینڈنگ ریکویسٹ نہیں ہے۔</p>'

    content = f'''
        <h2>🛡️ ایڈمن کنٹرول پینل</h2>
        <div class="card" style="text-align: right;">
            <h3 style="color: #ffa700;">پینڈنگ انویسٹمنٹ / اسکرین شاٹس</h3>
            {topup_html}
        </div>
        <a href="/dashboard"><button style="background: #2a3942;">یوزر ڈیش بورڈ پر جائیں</button></a>
        <a href="/logout"><button class="btn-danger" style="margin-top: 10px;">لاگ آؤٹ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/admin/approve/<int:topup_id>')
def approve_topup(topup_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT phone, amount FROM topups WHERE id = ?", (topup_id,))
    topup = cursor.fetchone()
    if topup:
        phone, amount = topup
        cursor.execute("UPDATE users SET balance = balance + ? WHERE phone = ?", (amount, phone))
        cursor.execute("UPDATE topups SET status = 'Approved' WHERE id = ?", (topup_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.pop('phone', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
