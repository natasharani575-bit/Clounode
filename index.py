import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'cfl_secret_key_123'

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE,
                        password TEXT,
                        balance REAL DEFAULT 0.0,
                        investment_status TEXT DEFAULT 'None',
                        screenshot TEXT DEFAULT '',
                        level INTEGER DEFAULT 1,
                        spin_count INTEGER DEFAULT 0
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT,
                        message TEXT,
                        reply TEXT DEFAULT ''
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )''')
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('wallet', 'TRX_DEFAULT_WALLET_ADDRESS')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('spin_fixed_amount', '5')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_whatsapp', '+923000000000')")
    
    cursor.execute("SELECT * FROM users WHERE email = 'admin@cfl.com'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email, password, balance, investment_status, level) VALUES ('admin@cfl.com', '123', 0.0, 'Approved', 1)")
    conn.commit()
    conn.close()

init_db()

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFL - لاگ ان / سائن اپ</title>
    <style>
        body { background-color: #0d1b1e; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding: 20px; }
        .card { background: #1b2a2e; padding: 20px; border-radius: 10px; max-width: 400px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        input, button { width: 90%; padding: 12px; margin: 10px 0; border-radius: 5px; border: none; font-size: 16px; }
        input { background: #0d1b1e; color: #fff; border: 1px solid #334d54; }
        button { background: #00b894; color: #fff; font-weight: bold; cursor: pointer; }
        button:hover { background: #019875; }
    </style>
</head>
<body>
    <div class="card">
        <h2>CFL پلیٹ فارم</h2>
        <form method="POST">
            <input type="email" name="email" placeholder="ایمیل درج کریں" required><br>
            <input type="password" name="password" placeholder="پاسورڈ درج کریں" required><br>
            <button type="submit">لاگ ان / رجسٹر ہوں</button>
        </form>
    </div>
</body>
</html>
'''

USER_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFL - ڈیش بورڈ</title>
    <style>
        body { background-color: #0d1b1e; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding: 10px; }
        .container { max-width: 400px; margin: auto; }
        .balance-box { background: #1b2a2e; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #00b894; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }
        .card { background: #1b2a2e; padding: 15px; border-radius: 10px; text-decoration: none; color: #fff; border: 1px solid #334d54; display: block; }
        .card:hover { border-color: #00b894; }
        .chat-box { background: #1b2a2e; padding: 10px; border-radius: 10px; text-align: right; max-height: 150px; overflow-y: auto; margin-bottom: 15px; border: 1px solid #334d54; }
        input, button { width: 90%; padding: 10px; margin: 5px 0; border-radius: 5px; border: none; }
        input { background: #0d1b1e; color: #fff; border: 1px solid #334d54; }
        .btn-send { background: #00b894; color: #fff; font-weight: bold; cursor: pointer; }
        .logout-btn { background: #d63031; color: #fff; width: 100%; padding: 12px; border-radius: 5px; text-decoration: none; display: block; margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="balance-box">
            <p>موجودہ بیلنس</p>
            <h2>${{ "%.2f"|format(user.balance) }}</h2>
            <p style="color: #ff7675; font-size: 14px;">اسٹیٹس: انویسٹمنٹ {{ user.investment_status }}</p>
        </div>

        <div class="grid">
            <a href="/withdraw" class="card"><h3>Withdraw</h3><p>رقم نکلوانا</p></a>
            <a href="/topup" class="card"><h3>Top Up</h3><p>انویسٹمنٹ کریں</p></a>
            <a href="/cashwheel" class="card"><h3>Cash Will</h3><p>اسپن اینڈ ون</p></a>
            <a href="/tasks" class="card"><h3>Daily Tasks</h3><p>روزانہ ٹاسک (0.35$)</p></a>
        </div>

        <div class="chat-box">
            <h4>ایڈمن لائیو چیت</h4>
            {% for c in chats %}
                <p><b>آپ:</b> {{ c.message }}</p>
                {% if c.reply %}
                    <p style="color: #00b894;"><b>ایڈمن:</b> {{ c.reply }}</p>
                {% endif %}
            {% endfor %}
        </div>

        <form method="POST" action="/chat">
            <input type="text" name="message" placeholder="پیغام لکھیں..." required>
            <button type="submit" class="btn-send">بھیجیں</button>
        </form>

        <a href="/logout" class="logout-btn">لاگ آؤٹ</a>
    </div>
</body>
</html>
'''

TOPUP_HTML = '''
<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFL - ٹاپ اپ</title>
    <style>
        body { background-color: #0d1b1e; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding: 20px; }
        .card { background: #1b2a2e; padding: 20px; border-radius: 10px; max-width: 400px; margin: auto; }
        input, button { width: 90%; padding: 12px; margin: 10px 0; border-radius: 5px; border: none; font-size: 16px; }
        input { background: #0d1b1e; color: #fff; border: 1px solid #334d54; }
        button { background: #00b894; color: #fff; font-weight: bold; cursor: pointer; }
        a { color: #00b894; text-decoration: none; display: block; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>انویسٹمنٹ اور اسکرین شاٹ اپ لوڈ</h2>
        <p>ایڈمن والٹ ایڈریس:</p>
        <code style="background:#0d1b1e; padding:5px; display:block; word-break:break-all;">{{ wallet }}</code>
        <form method="POST" enctype="multipart/form-data">
            <p>ٹرانزیکشن آئی ڈی (TRX ID):</p>
            <input type="text" name="trx_id" placeholder="TRX ID درج کریں" required>
            <p>اسکرین شاٹ اپ لوڈ کریں:</p>
            <input type="file" name="screenshot" accept="image/*" required><br>
            <button type="submit">پئمنٹ جمع کروائیں</button>
        </form>
        <a href="/dashboard">واپس ڈیش بورڈ پر جائیں</a>
    </div>
</body>
</html>
'''

CASHWHEEL_HTML = '''
<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFL - کیش وہیل</title>
    <style>
        body { background-color: #0d1b1e; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding: 20px; }
        .card { background: #1b2a2e; padding: 20px; border-radius: 10px; max-width: 400px; margin: auto; }
        button { background: #00b894; color: #fff; padding: 15px; width: 90%; border-radius: 5px; border: none; font-weight: bold; font-size: 16px; cursor: pointer; }
        a { color: #00b894; text-decoration: none; display: block; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>کیش وہیل (Spin & Win)</h2>
        <p>اسپن کریں اور انعامات حاصل کریں! (لیول {{ user.level }} کے مطابق)</p>
        {% if msg %}
            <h3 style="color: #00b894;">{{ msg }}</h3>
        {% endif %}
        <form method="POST">
            <button type="submit">اسپن گھمائیں</button>
        </form>
        <a href="/dashboard">واپس ڈیش بورڈ پر جائیں</a>
    </div>
</body>
</html>
'''

ADMIN_PANEL_HTML = '''
<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFL - ایڈمن پینل</title>
    <style>
        body { background-color: #0d1b1e; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding: 10px; }
        .container { max-width: 450px; margin: auto; }
        .card { background: #1b2a2e; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #334d54; text-align: right; }
        input, button { width: 100%; padding: 10px; margin: 5px 0; border-radius: 5px; border: none; font-size: 14px; }
        input { background: #0d1b1e; color: #fff; border: 1px solid #334d54; }
        .btn-action { background: #00b894; color: #fff; font-weight: bold; cursor: pointer; }
        .logout-btn { background: #d63031; color: #fff; font-weight: bold; text-decoration: none; display: block; padding: 12px; border-radius: 5px; text-align: center; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>⭐ CFL - ایڈمن پینل ⭐</h2>

        <div class="card">
            <h4>والٹ ایڈریس تبدیل کریں</h4>
            <form method="POST" action="/admin/update_wallet">
                <input type="text" name="wallet_address" value="{{ wallet }}" required>
                <button type="submit" class="btn-action">ایڈریس اپ ڈیٹ کریں</button>
            </form>
        </div>

        <div class="card">
            <h4>کیش وہیل (Spin) رقم کنٹرول</h4>
            <form method="POST" action="/admin/update_spin">
                <input type="number" step="0.01" name="spin_fixed_amount" value="{{ spin_fixed_amount }}" required>
                <button type="submit" class="btn-action">اسپن اماؤنٹ سیٹ کریں</button>
            </form>
        </div>

        <div class="card">
            <h4>یوزر لیول اپ ڈیٹ کریں</h4>
            <form method="POST" action="/admin/update_level">
                <input type="email" name="user_email" placeholder="یوزر ای میل" required>
                <input type="number" name="level" placeholder="لیول (مثلاً 1 یا 2)" required>
                <button type="submit" class="btn-action">لیول اپ ڈیٹ کریں</button>
            </form>
        </div>

        <div class="card">
            <h4>پینڈنگ انویسٹمنٹ اور اسکرین شاٹس ریکویسٹس</h4>
            {% for inv in investments_pending %}
                <p><b>ایمیل:</b> {{ inv.email }} | <b>TRX ID:</b> {{ inv.trx_id }}</p>
                {% if inv.screenshot %}
                    <p><a href="{{ inv.screenshot }}" target="_blank" style="color:#00b894;">اسکرین شاٹ دیکھیں</a></p>
                {% endif %}
                <form method="POST" action="/admin/approve">
                    <input type="hidden" name="email" value="{{ inv.email }}">
                    <button type="submit" class="btn-action">منظور کریں (Approve)</button>
                </form>
                <hr style="border-color:#334d54;">
            {% else %}
                <p>کوئی بھی پینڈنگ درخواست موجود نہیں۔</p>
            {% endfor %}
        </div>

        <a href="/logout" class="logout-btn">ایڈمن لاگ آؤٹ</a>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            if user['password'] == password:
                session['user'] = email
                conn.close()
                if email == 'admin@cfl.com':
                    return redirect(url_for('admin_panel'))
                return redirect(url_for('dashboard'))
        else:
            cursor.execute("INSERT INTO users (email, password, balance, investment_status) VALUES (?, ?, 0.0, 'Pending')", (email, password))
            conn.commit()
            session['user'] = email
            conn.close()
            return redirect(url_for('dashboard'))
        conn.close()
    return render_template_string(LOGIN_HTML)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    email = session['user']
    if email == 'admin@cfl.com':
        return redirect(url_for('admin_panel'))
        
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM chat WHERE email = ?", (email,))
    chats = cursor.fetchall()
    conn.close()
    return render_template_string(USER_DASHBOARD_HTML, user=user, chats=chats)

@app.route('/topup', methods=['GET', 'POST'])
def topup():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == 'POST':
        trx_id = request.form.get('trx_id')
        screenshot = request.files.get('screenshot')
        screenshot_url = ''
        if screenshot:
            screenshot_url = f"/static/{screenshot.filename}"
        cursor.execute("UPDATE users SET investment_status = ?, screenshot = ? WHERE email = ?", 
                       (f"Pending (TRX: {trx_id})", screenshot_url, session['user']))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    
    cursor.execute("SELECT value FROM settings WHERE key = 'wallet'")
    wallet = cursor.fetchone()['value']
    conn.close()
    return render_template_string(TOPUP_HTML, wallet=wallet)

@app.route('/cashwheel', methods=['GET', 'POST'])
def cashwheel():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (session['user'],))
    user = cursor.fetchone()
    
    msg = ''
    if request.method == 'POST':
        cursor.execute("SELECT value FROM settings WHERE key = 'spin_fixed_amount'")
        spin_amt = float(cursor.fetchone()['value']) * user['level']
        new_balance = user['balance'] + spin_amt
        cursor.execute("UPDATE users SET balance = ? WHERE email = ?", (new_balance, session['user']))
        conn.commit()
        msg = f"مبارک ہو! آپ نے اسپن سے ${spin_amt} جیت لیے ہیں۔"
        cursor.execute("SELECT * FROM users WHERE email = ?", (session['user'],))
        user = cursor.fetchone()
    conn.close()
    return render_template_string(CASHWHEEL_HTML, user=user, msg=msg)

@app.route('/tasks')
def tasks():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + 0.35 WHERE email = ?", (session['user'],))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/chat', methods=['POST'])
def chat():
    if 'user' not in session:
        return redirect(url_for('login'))
    message = request.form.get('message')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat (email, message) VALUES (?, ?)", (session['user'], message))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin_panel():
    if 'user' not in session or session['user'] != 'admin@cfl.com':
        return "Unauthorized", 401
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'wallet'")
    wallet = cursor.fetchone()['value']
    cursor.execute("SELECT value FROM settings WHERE key = 'spin_fixed_amount'")
    spin_fixed_amount = cursor.fetchone()['value']
    cursor.execute("SELECT email, investment_status, screenshot FROM users WHERE investment_status LIKE 'Pending%'")
    investments_pending = cursor.fetchall()
    conn.close()
    return render_template_string(ADMIN_PANEL_HTML, wallet=wallet, spin_fixed_amount=spin_fixed_amount, investments_pending=investments_pending)

@app.route('/admin/approve', methods=['POST'])
def admin_approve():
    if 'user' not in session or session['user'] != 'admin@cfl.com':
        return "Unauthorized", 401
    email = request.form.get('email')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET investment_status = 'Approved' WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/update_wallet', methods=['POST'])
def admin_update_wallet():
    if 'user' not in session or session['user'] != 'admin@cfl.com':
        return "Unauthorized", 401
    wallet = request.form.get('wallet_address')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'wallet'", (wallet,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/update_spin', methods=['POST'])
def admin_update_spin():
    if 'user' not in session or session['user'] != 'admin@cfl.com':
        return "Unauthorized", 401
    spin_amt = request.form.get('spin_fixed_amount')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'spin_fixed_amount'", (spin_amt,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/update_level', methods=['POST'])
def admin_update_level():
    if 'user' not in session or session['user'] != 'admin@cfl.com':
        return "Unauthorized", 401
    email = request.form.get('user_email')
    level = request.form.get('level')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET level = ? WHERE email = ?", (level, email))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/withdraw')
def withdraw():
    return "Withdraw feature coming soon!"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
