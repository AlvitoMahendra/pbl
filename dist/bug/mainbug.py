import os
from flask import Flask, render_template, request, url_for, session, send_from_directory, flash, redirect, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
from flask_socketio import SocketIO, emit, disconnect
from datetime import datetime, timedelta
from functools import wraps
import json
import MySQLdb.cursors
import logging
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect


# Setup logging
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Gunakan secret key yang aman dari environment atau generate secara acak
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config["MYSQL_HOST"] = os.environ.get('MYSQL_HOST', 'localhost')
app.config["MYSQL_USER"] = os.environ.get('MYSQL_USER', 'root')
app.config["MYSQL_PASSWORD"] = os.environ.get('MYSQL_PASSWORD', '')
app.config["MYSQL_DB"] = os.environ.get('MYSQL_DB', 'pblrks2')
app.config["MYSQL_CURSORCLASS"] = 'DictCursor'
app.config["SESSION_COOKIE_SECURE"] = True  # Hanya HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Mencegah akses via JS
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)  # Timeout session

mysql = MySQL(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

# Menyimpan data pengguna yang online
online_users = {}

def get_db_connection():
    """Fungsi bantu untuk mendapatkan koneksi database"""
    try:
        return mysql.connection.cursor()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

def login_required(f):
    """Decorator untuk memastikan user sudah login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    """Validasi format email"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
@csrf.exempt
def login():
    if request.method == 'POST':
        try:
            identifier = request.form.get('identifier', '').strip()
            password = request.form.get('password', '')
            logger.info(f"Login attempt: identifier={identifier}, password={password}")

            if not identifier or not password or len(password) < 8:
                flash("Invalid input. Password must be at least 8 characters.", "warning")
                return render_template('auth-login-minimal.html')

            cursor = get_db_connection()
            if not cursor:
                flash("Service unavailable", "danger")
                return render_template('auth-login-minimal.html')

            cursor.execute("SELECT * FROM tb_user WHERE username=%s OR email=%s", (identifier, identifier))
            account = cursor.fetchone()
            logger.info(f"Account found: {account}")
            cursor.close()

            if not account or not check_password_hash(account['password'], password):
                logger.warning(f"Login failed for {identifier}")
                flash("Invalid credentials", "danger")
            else:
                session.permanent = True
                session['loggedin'] = True
                session['username'] = account['username']
                session['email'] = account['email']
                session['level'] = account['level']
                session['user_id'] = account['id']
                logger.info(f"User {account['username']} logged in")
                return redirect(url_for('index'))

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash("Service unavailable", "danger")

    return render_template('auth-login-minimal.html')


@app.route('/registrasi', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
@csrf.exempt  # Tambahkan CSRF token di form HTML
def registrasi():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            cpassword = request.form.get('cpassword', '')
            fullname = request.form.get('fullname', '').strip()

            if not all([email, username, password, cpassword, fullname]) or len(password) < 8:
                flash("All fields required. Password must be at least 8 characters.", "warning")
                return render_template('auth-register-minimal.html')

            if not validate_email(email):
                flash("Invalid email format", "warning")
                return render_template('auth-register-minimal.html')

            if password != cpassword:
                flash("Passwords do not match", "warning")
                return render_template('auth-register-minimal.html')

            cursor = get_db_connection()
            if not cursor:
                flash("Service unavailable", "danger")
                return render_template('auth-register-minimal.html')

            cursor.execute('SELECT * FROM tb_user WHERE username=%s OR email=%s', (username, email))
            account = cursor.fetchone()

            if account:
                flash("Username or email already exists", 'danger')
            else:
                hashed_password = generate_password_hash(password)
                cursor.execute("INSERT INTO tb_user (username, email, password, fullname) VALUES (%s, %s, %s, %s)",
                              (username, email, hashed_password, fullname))
                user_id = cursor.lastrowid
                user_level = "USER"
                
                cursor.execute("INSERT INTO tb_info_user (user_id, username, email, level, fullname) VALUES (%s, %s, %s, %s, %s)",
                              (user_id, username, email, user_level, fullname))
                
                mysql.connection.commit()
                flash("Registration successful", "success")
                logger.info(f"New user registered: {username}")

            cursor.close()

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            flash("Service unavailable", "danger")

    return render_template('auth-register-minimal.html')

@app.route('/logout')
@login_required
def logout():
    try:
        username = session.get('username')
        if username:
            cursor = get_db_connection()
            if cursor:
                cursor.execute("UPDATE tb_user SET socket_id = NULL WHERE username = %s", (username,))
                mysql.connection.commit()
                cursor.close()
            online_users.pop(username, None)
            logger.info(f"User {username} logged out")
        session.clear()
        return redirect(url_for('login'))

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return redirect(url_for('login'))

@app.route('/assets/<path:filename>')
def send_assets(filename):
    return send_from_directory('static/assets', filename)

@app.route('/chat')
@login_required
def appchat():
    try:
        cursor = get_db_connection()
        if not cursor:
            flash("Service unavailable", "danger")
            return redirect(url_for('index'))

        cursor.execute("SELECT id, username, level, socket_id FROM tb_user WHERE username != %s", (session['username'],))
        users = cursor.fetchall()
        cursor.close()

        contacts = [{'id': user['id'], 'username': user['username'], 
                    'level': user['level'], 'status': 'online' if user['socket_id'] else 'offline'}
                   for user in users]
        
        return render_template('apps-chat.html', contacts=contacts, current_user=session['username'])

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        flash("Error loading chat", "danger")
        return redirect(url_for('index'))

@app.route('/get_messages/<receiver>')
@login_required
def get_messages(receiver):
    try:
        sender = session['username']
        cursor = get_db_connection()
        if not cursor:
            return jsonify({'error': 'Service unavailable'}), 500

        cursor.execute("""
            SELECT * FROM tb_messages 
            WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
            ORDER BY timestamp ASC
        """, (sender, receiver, receiver, sender))
        
        messages = cursor.fetchall()
        cursor.close()

        result = [{'id': msg['id'], 'sender': msg['sender'], 'receiver': msg['receiver'],
                  'message': msg['message'], 'timestamp': msg['timestamp'].strftime('%d/%m/%Y %H:%M:%S') 
                  if msg['timestamp'] else ''} for msg in messages]
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Get messages error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/info')
@login_required
def info():
    try:
        user_id = session['user_id']
        cursor = get_db_connection()
        if not cursor:
            flash("Service unavailable", "danger")
            return redirect(url_for('index'))

        cursor.execute("SELECT * FROM tb_info_user WHERE user_id = %s", (user_id,))
        info_user = cursor.fetchone()
        cursor.close()

        if not info_user:
            flash("User info not found", "warning")
            return redirect(url_for('index'))

        return render_template('leads-view.html', info_user=info_user)

    except Exception as e:
        logger.error(f"Info error: {str(e)}")
        flash("Error loading user info", "danger")
        return redirect(url_for('index'))

@app.route('/update')
@login_required
def update():
    try:
        username = session['username']
        cursor = get_db_connection()
        if not cursor:
            flash("Service unavailable", "danger")
            return redirect(url_for('index'))

        cursor.execute("SELECT * FROM tb_info_user WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()

        return render_template('leads-create.html', user=user_data)

    except Exception as e:
        logger.error(f"Update error: {str(e)}")
        flash("Error loading update page", "danger")
        return redirect(url_for('index'))

@app.route('/update_data', methods=['POST'])
@login_required
@csrf.exempt  # Tambahkan CSRF token di form HTML
def update_data():
    try:
        userid = session['user_id']
        cursor = get_db_connection()
        if not cursor:
            flash("Service unavailable", "danger")
            return redirect(url_for('update'))

        data = {
            'username': request.form.get('username', '').strip(),
            'fullname': request.form.get('fullname', '').strip(),
            'birthday': request.form.get('birthday', ''),
            'email': request.form.get('email', '').strip(),
            'nohp': request.form.get('nohp', ''),
            'city': request.form.get('city', ''),
            'country': request.form.get('country', ''),
            'state': request.form.get('state', ''),
            'address': request.form.get('address', '')
        }

        if not data['username'] or not data['email'] or not validate_email(data['email']):
            flash("Username and valid email are required", "warning")
            return redirect(url_for('update'))

        cursor.execute("""
            UPDATE tb_info_user SET username=%s, fullname=%s, birthday=%s, email=%s, 
            nohp=%s, city=%s, country=%s, state=%s, address=%s WHERE user_id=%s
        """, (*data.values(), userid))

        mysql.connection.commit()
        cursor.close()
        
        flash("Data updated successfully", "success")
        return redirect(url_for('update'))

    except Exception as e:
        logger.error(f"Update data error: {str(e)}")
        flash("Error updating data", "danger")
        return redirect(url_for('update'))

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    if 'username' not in session:
        disconnect()
        return
    
    try:
        username = session['username']
        sid = request.sid
        
        cursor = get_db_connection()
        if cursor:
            cursor.execute("UPDATE tb_user SET socket_id = %s WHERE username = %s", (sid, username))
            mysql.connection.commit()
            cursor.close()
        
        online_users[username] = sid
        emit('user_status', {'username': username, 'status': 'online'}, broadcast=True)
        logger.info(f"User {username} connected")

    except Exception as e:
        logger.error(f"Socket connect error: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    if 'username' not in session:
        return
    
    try:
        username = session['username']
        cursor = get_db_connection()
        if cursor:
            cursor.execute("UPDATE tb_user SET socket_id = NULL WHERE username = %s", (username,))
            mysql.connection.commit()
            cursor.close()
        
        online_users.pop(username, None)
        emit('user_status', {'username': username, 'status': 'offline'}, broadcast=True)
        logger.info(f"User {username} disconnected")

    except Exception as e:
        logger.error(f"Socket disconnect error: {str(e)}")

@socketio.on('send_message')
def handle_send_message(data):
    if 'username' not in session:
        return
    
    try:
        sender = session['username']
        receiver = data.get('receiver', '').strip()
        message = data.get('message', '').strip()
        
        if not receiver or not message or len(message) > 500:  # Batas panjang pesan
            return

        cursor = get_db_connection()
        if not cursor:
            return

        cursor.execute("SELECT username FROM tb_user WHERE username = %s", (receiver,))
        if not cursor.fetchone():
            cursor.close()
            return  # Penerima tidak valid

        cursor.execute("INSERT INTO tb_messages (sender, receiver, message) VALUES (%s, %s, %s)",
                      (sender, receiver, message))
        mysql.connection.commit()
        
        message_id = cursor.lastrowid
        cursor.close()
        
        now = datetime.now()
        timestamp = now.strftime('%d/%m/%Y %H:%M:%S')
        
        message_data = {
            'id': message_id,
            'sender': sender,
            'receiver': receiver,
            'message': message,
            'timestamp': timestamp
        }
        
        emit('receive_message', message_data)
        if receiver in online_users:
            emit('receive_message', message_data, room=online_users[receiver])

    except Exception as e:
        logger.error(f"Send message error: {str(e)}")

if __name__ == '__main__':
    socketio.run(app, port=5000, debug=False, host='0.0.0.0')  # Debug=False untuk produksi