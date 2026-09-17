import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'cfl_secure_secret_key_12345'

DB_PATH = '/tmp/cfl_database_v6.db'

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
            status TEXT DEFAULT 'Pending',
            is_admin INTEGER DEFAULT 0,
            last_task_time TEXT,
            can_spin INTEGER DEFAULT 0
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
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
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
        cursor.execute("INSERT INTO users (phone, email, password, balance, status, is_admin, can_spin) VALUES ('03000000000', 'admin@cfl.com', 'admin123', 0.00, 'Active', 1, 1)")
    
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('trc20_wallet', 'TXYZ123456789ABCDEFCryptoWalletAddress')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('next_prize', '6')")
    
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
        .chat-box { background: #0b141a; height: 300px; overflow-y: scroll; padding: 10px; border-radius: 8px; border: 1px solid #3b4a54; text-align: right; margin-bottom: 10px; }
        .msg { padding: 8px 12px; margin: 8px 0; border-radius: 8px; font-size: 14px; }
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
            cursor.execute("INSERT INTO users (phone, email, password, balance, status) VALUES (?, ?, ?, 0.00, 'Pending')", (phone, email, password))
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
            <button type="submit">اکاؤنٹ بنائیں</button>
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
    conn.close()
    
    bal = f"${user[4]:.2f}" if user else "$0.00"
    status_text = "ایکٹو (Active)" if user[5] == 'Active' else "انویسٹمنٹ پینڈنگ / تصدیق کا انتظار ہے"
    status_color = "#25d366" if user[5] == 'Active' else "#ffa700"
    
    content = f'''
        <div class="card">
            <p style="font-size: 14px; color: #8696a0;">موجودہ بیلنس</p>
            <div class="balance">{bal}</div>
            <p style="font-size: 13px; color: {status_color}; margin-top: 5px;">اسٹیٹس: {status_text}</p>
        </div>

        <div class="grid">
            <a href="/withdraw" class="menu-btn">💸 Withdraw<br><span style="font-size:11px; color:#8696a0;">رقم نکلوانا</span></a>
            <a href="/topup" class="menu-btn">💳 Top Up<br><span style="font-size:11px; color:#8696a0;">انویسٹمنٹ کریں</span></a>
            <a href="/cashwill" class="menu-btn">🎡 Cash Will<br><span style="font-size:11px; color:#8696a0;">اسپن اینڈ ون</span></a>
            <a href="/tasks" class="menu-btn">📋 Daily Tasks<br><span style="font-size:11px; color:#8696a0;">روزانہ ٹاسک ($0.35)</span></a>
        </div>

        <div style="margin-top: 15px;">
            <a href="/chat" class="menu-btn" style="background: #005c4b; border-color: #00a884; font-size: 16px; padding: 18px;">
                💬 Live Chat With Admin<br><span style="font-size:12px; color:#a5d6a7;">ایڈمن سے لائیو بات چیت کریں</span>
            </a>
        </div>

        <a href="/logout"><button class="btn-danger" style="margin-top: 20px;">لاگ آؤٹ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    phone = session['phone']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        message = request.form['message']
        cursor.execute("INSERT INTO messages (phone, message, sender) VALUES (?, ?, 'user')", (phone, message))
        conn.commit()
    
    cursor.execute("SELECT * FROM messages WHERE phone = ? ORDER BY id ASC", (phone,))
    messages = cursor.fetchall()
    conn.close()
    
    msg_html = ""
    for m in messages:
        m_class = "user-msg" if m[3] == 'user' else "admin-msg"
        sender_label = "آپ" if m[3] == 'user' else "ایڈمن"
        msg_html += f'<div class="msg {m_class}"><b>{sender_label}:</b> {m[2]}</div>'
    
    content = f'''
        <h2>💬 ایڈمن لائیو چیٹ</h2>
        <div class="card" style="text-align: right;">
            <div class="chat-box">{msg_html}</div>
            <form method="POST">
                <input type="text" name="message" placeholder="یہاں اپنا پیغام لکھیں..." required style="margin: 5px 0;">
                <button type="submit">پیغام بھیجیں</button>
            </form>
        </div>
        <a href="/dashboard"><button style="background: #2a3942;">واپس ڈیش بورڈ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/topup', methods=['GET', 'POST'])
def topup():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'trc20_wallet'")
    wallet_addr = cursor.fetchone()[0]
    
    if request.method == 'POST':
        amount = request.form['amount']
        screenshot = request.form['screenshot']
        phone = session['phone']
        cursor.execute("INSERT INTO topups (phone, amount, screenshot, status) VALUES (?, ?, ?, 'Pending')", (phone, amount, screenshot))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    
    content = f'''
        <h2>Top Up / انویسٹمنٹ</h2>
        <div class="card">
            <p style="font-size: 13px; color: #8696a0;">آپ کا ایڈمن کرپٹو والٹ ایڈریس:</p>
            <p style="background: #111b21; padding: 10px; border-radius: 5px; font-family: monospace; color: #00a884; word-break: break-all; margin: 10px 0;">
                <b>USDT (TRC20):</b> {wallet_addr}
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
    
    phone = session['phone']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT status, can_spin FROM users WHERE phone = ?", (phone,))
    user_data = cursor.fetchone()
    status, can_spin = user_data[0], user_data[1]
    
    cursor.execute("SELECT value FROM settings WHERE key = 'next_prize'")
    prize = float(cursor.fetchone()[0])
    
    error_msg = ""
    if request.method == 'POST':
        if status != 'Active':
            error_msg = "یرر: آپ کا اکاؤنٹ ایکٹو نہیں ہے! پہلے ایڈمن سے انویسٹمنٹ منظور کروائیں۔"
        elif can_spin != 1:
            error_msg = "یرر: ایڈمن کی طرف سے تاحال اسپن کی اجازت نہیں ملی۔ براہ کرم لائیو چیٹ پر رابطہ کریں!"
        else:
            cursor.execute("UPDATE users SET balance = balance + ?, can_spin = 0 WHERE phone = ?", (prize, phone))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
            
    conn.close()
    
    content = f'''
        <h2>🎡 Cash Will (اسپن اینڈ ون)</h2>
        <div class="card">
            <p>پہیہ گھمائیں اور شاندار انعامات ($6, $10, $18, $15, $30, $50, $80, $100) جیتیں!</p>
            <p style="color: #ff5c5c; margin-top: 10px;">{error_msg}</p>
            
            <div style="margin: 20px 0;">
                <canvas id="wheel" width="220" height="220" style="background:#111b21; border-radius:50%; border: 4px solid #00a884;"></canvas>
            </div>

            <form method="POST">
                <button type="submit" id="spin-btn">اسپن کریں (Spin Wheel)</button>
            </form>
        </div>
        <br><a href="/dashboard"><button style="background: #2a3942;">واپس ڈیش بورڈ</button></a>

        <script>
            const canvas = document.getElementById('wheel');
            const ctx = canvas.getContext('2d');
            const sectors = [6, 10, 18, 15, 30, 50, 80, 100];
            const colors = ['#00a884', '#202c33', '#005c4b', '#2a3942', '#25d366', '#128c7e', '#34b7f1', '#075e54'];
            const arc = Math.PI / (sectors.length / 2);
            
            function drawWheel() {{
                let startAngle = 0;
                for (let i = 0; i < sectors.length; i++) {{
                    ctx.beginPath();
                    ctx.fillStyle = colors[i];
                    ctx.moveTo(110, 110);
                    ctx.arc(110, 110, 100, startAngle, startAngle + arc, false);
                    ctx.lineTo(110, 110);
                    ctx.fill();
                    ctx.save();
                    
                    ctx.translate(110, 110);
                    ctx.rotate(startAngle + arc / 2);
                    ctx.fillStyle = '#fff';
                    ctx.font = 'bold 14px Tahoma';
                    ctx.fillText('$' + sectors[i], 50, 10);
                    ctx.restore();
                    startAngle += arc;
                }}
            }}
            drawWheel();
        </script>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    phone = session['phone']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status, last_task_time FROM users WHERE phone = ?", (phone,))
    res = cursor.fetchone()
    status, last_time = res[0], res[1]
    
    error_msg = ""
    if request.method == 'POST':
        if status != 'Active':
            error_msg = "یرر: آپ کا اکاؤنٹ غیر فعال ہے! پہلے انویسٹمنٹ ایڈمن سے اپروو کروائیں۔"
        else:
            now = datetime.now()
            can_task = True
            if last_time:
                last_dt = datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
                if now - last_dt < timedelta(hours=24):
                    can_task = False
                    hours_left = 24 - int((now - last_dt).total_seconds() / 3600)
                    error_msg = f"آپ ہر 24 گھنٹے بعد ٹاسک کر سکتے ہیں۔ مزید {hours_left} گھنٹے باقی ہیں۔"
            
            if can_task:
                now_str = now.strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("UPDATE users SET balance = balance + 0.35, last_task_time = ? WHERE phone = ?", (now_str, phone))
                conn.commit()
                conn.close()
                return redirect(url_for('dashboard'))
            
    conn.close()
    
    content = f'''
        <h2>📋 Daily Tasks</h2>
        <div class="card">
            <p>آج کا دستیاب ٹاسک: مکمل کریں اور $0.35 حاصل کریں۔ (صرف ایکٹو اکاؤنٹس کے لیے)</p>
            <p style="color: #ff5c5c; margin-top: 10px;">{error_msg}</p>
            <form method="POST">
                <button type="submit">ٹاسک مکمل کریں</button>
            </form>
        </div>
        <br><a href="/dashboard"><button style="background: #2a3942;">واپس ڈیش بورڈ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    phone = session['phone']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM users WHERE phone = ?", (phone,))
    status = cursor.fetchone()[0]
    conn.close()
    
    error_msg = ""
    if request.method == 'POST':
        if status != 'Active':
            error_msg = "یرر: انویسٹمنٹ کی تصدیق نہ ہونے کی وجہ سے آپ رقم نہیں نکلوا سکتے!"
        else:
            return redirect(url_for('dashboard'))
        
    content = f'''
        <h2>💸 Withdraw (رقم نکلوانا)</h2>
        <div class="card">
            <p style="color: #ff5c5c; margin-bottom: 10px;">{error_msg}</p>
            <p>اپنا کرپٹو والٹ ایڈریس اور رقم درج کریں:</p>
            <form method="POST">
                <input type="number" step="0.01" name="amount" placeholder="رقم درج کریں ($)" required>
                <input type="text" name="wallet" placeholder="آپ کا والٹ ایڈریس" required>
                <button type="submit">ودڈرا کی درخواست بھیجیں</button>
            </form>
        </div>
        <br><a href="/dashboard"><button style="background: #2a3942;">واپس ڈیش بورڈ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        if 'wallet' in request.form:
            new_wallet = request.form['wallet']
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'trc20_wallet'", (new_wallet,))
            conn.commit()
        elif 'prize' in request.form:
            new_prize = request.form['prize']
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'next_prize'", (new_prize,))
            conn.commit()
        elif 'unlock_spin' in request.form:
            spin_phone = request.form['unlock_spin']
            cursor.execute("UPDATE users SET can_spin = 1 WHERE phone = ?", (spin_phone,))
            conn.commit()
            
    cursor.execute("SELECT * FROM topups WHERE status = 'Pending'")
    topups = cursor.fetchall()
    
    cursor.execute("SELECT DISTINCT phone FROM messages")
    chat_users = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT phone, balance, status FROM users WHERE is_admin = 0")
    all_users = cursor.fetchall()
    
    cursor.execute("SELECT value FROM settings WHERE key = 'trc20_wallet'")
    current_wallet = cursor.fetchone()[0]
    
    cursor.execute("SELECT value FROM settings WHERE key = 'next_prize'")
    current_prize = cursor.fetchone()[0]
    
    conn.close()
    
    topup_html = ""
    if topups:
        for t in topups:
            topup_html += f'<p>موبائل: <b>{t[1]}</b> | رقم: <b>${t[2]}</b> | ثبوت: {t[3]}</p>'
            topup_html += f'<a href="/admin/approve/{t[0]}"><button style="padding: 5px; margin: 5px 0; background: #25d366;">اپروو کریں (Approve)</button></a>'
            topup_html += '<hr style="border-color: #3b4a54; margin: 10px 0;">'
    else:
        topup_html = '<p style="color: #8696a0;">کوئی نئی پینڈنگ ریکویسٹ نہیں ہے۔</p>'

    users_html = ""
    for u in all_users:
        users_html += f'<p>موبائل: <b>{u[0]}</b> | بیلنس: ${u[1]} | اسٹیٹس: {u[2]}</p>'
        users_html += f'''
            <form method="POST" style="margin-top:5px;">
                <input type="hidden" name="unlock_spin" value="{u[0]}">
                <button type="submit" style="padding: 5px; background: #34b7f1; font-size: 12px;">اسپن انلاک کریں (Allow Spin)</button>
            </form>
        '''
        users_html += '<hr style="border-color: #3b4a54; margin: 10px 0;">'

    chat_links_html = ""
    if chat_users:
        for cu in chat_users:
            chat_links_html += f'<a href="/admin/chat/{cu}"><button style="background: #2a3942; margin: 5px 0;">یوزر چیٹ: {cu}</button></a>'
    else:
        chat_links_html = '<p style="color: #8696a0;">کوئی نئی چیٹ موجود نہیں ہے۔</p>'

    content = f'''
        <h2>🛡️ ایڈمن کنٹرول پینل</h2>
        
        <div class="card" style="text-align: right;">
            <h3 style="color: #00a884;">⚙️ والٹ ایڈریس تبدیل کریں</h3>
            <form method="POST">
                <input type="text" name="wallet" value="{current_wallet}" required>
                <button type="submit">والٹ ایڈریس اپڈیٹ کریں</button>
            </form>
        </div>

        <div class="card" style="text-align: right;">
            <h3 style="color: #00a884;">🎡 اگلے اسپن (Wheel) کا انعام سیٹ کریں</h3>
            <form method="POST">
                <select name="prize">
                    <option value="6" {'selected' if current_prize=='6' else ''}>$6</option>
                    <option value="10" {'selected' if current_prize=='10' else ''}>$10</option>
                    <option value="15" {'selected' if current_prize=='15' else ''}>$15</option>
                    <option value="18" {'selected' if current_prize=='18' else ''}>$18</option>
                    <option value="30" {'selected' if current_prize=='30' else ''}>$30</option>
                    <option value="50" {'selected' if current_prize=='50' else ''}>$50</option>
                    <option value="80" {'selected' if current_prize=='80' else ''}>$80</option>
                    <option value="100" {'selected' if current_prize=='100' else ''}>$100</option>
                </select>
                <button type="submit">انعام سیٹ کریں</button>
            </form>
        </div>

        <div class="card" style="text-align: right;">
            <h3 style="color: #00a884;">👥 یوزرز کا کنٹرول اور اسپن انلاک</h3>
            {users_html}
        </div>

        <div class="card" style="text-align: right;">
            <h3 style="color: #00a884;">💬 یوزرز کی لائیو چیٹس</h3>
            {chat_links_html}
        </div>

        <div class="card" style="text-align: right;">
            <h3 style="color: #ffa700;">💳 پینڈنگ انویسٹمنٹ / اسکرین شاٹس</h3>
            {topup_html}
        </div>
        <a href="/logout"><button class="btn-danger" style="margin-top: 10px;">لاگ آؤٹ</button></a>
    '''
    return BASE_HTML.replace('%CONTENT%', content)

@app.route('/admin/chat/<user_phone>', methods=['GET', 'POST'])
def admin_chat_detail(user_phone):
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        message = request.form['message']
        cursor.execute("INSERT INTO messages (phone, message, sender) VALUES (?, ?, 'admin')", (user_phone, message))
        conn.commit()
    
    cursor.execute("SELECT * FROM messages WHERE phone = ? ORDER BY id ASC", (user_phone,))
    messages = cursor.fetchall()
    conn.close()
    
    msg_html = ""
    for m in messages:
        m_class = "user-msg" if m[3] == 'user' else "admin-msg"
        sender_label = user_phone if m[3] == 'user' else "آپ (ایڈمن)"
        msg_html += f'<div class="msg {m_class}"><b>{sender_label}:</b> {m[2]}</div>'
        
    content = f'''
        <h2>💬 یوزر کے ساتھ چیٹ: {user_phone}</h2>
        <div class="card" style="text-align: right;">
            <div class="chat-box">{msg_html}</div>
            <form method="POST">
                <input type="text" name="message" placeholder="جواب لکھیں..." required style="margin: 5px 0;">
                <button type="submit">جواب بھیجیں</button>
            </form>
        </div>
        <br><a href="/admin"><button style="background: #2a3942;">واپس ایڈمن پینل</button></a>
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
        # Approve Topup, set user status to Active, and add amount to balance
        cursor.execute("UPDATE users SET balance = balance + ?, status = 'Active' WHERE phone = ?", (amount, phone))
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
