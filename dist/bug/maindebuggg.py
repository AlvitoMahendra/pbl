from flask import Flask, render_template, request, url_for, session, send_from_directory, flash, redirect, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
import MySQLdb.cursors
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, filename='app.log')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "apaja"  # Ganti dengan os.urandom(24) untuk produksi
app.config["MYSQL_HOST"] = 'localhost'
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"] = ''
app.config["MYSQL_DB"] = 'pblrks2'
app.config["MYSQL_CURSORCLASS"] = 'DictCursor'

mysql = MySQL(app)

def get_db_connection():
    try:
        return mysql.connection.cursor()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

@app.route('/')
def index():
    if 'loggedin' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            identifier = request.form.get('identifier', '').strip()  # Perbaiki typo dari 'indentifier'
            password = request.form.get('password', '')
            if not identifier or not password:
                flash("Please fill all fields", "warning")
                return render_template('auth-login-minimal.html')

            cursor = get_db_connection()
            if not cursor:
                flash("Database error occurred", "danger")
                return render_template('auth-login-minimal.html')

            cursor.execute("SELECT * FROM tb_user WHERE username=%s OR email=%s", (identifier, identifier))
            account = cursor.fetchone()
            cursor.close()

            if not account:
                flash("Invalid credentials", "danger")
            elif not check_password_hash(account['password'], password):
                flash("Invalid credentials", "danger")
            else:
                session['loggedin'] = True
                session['username'] = account['username']
                session['email'] = account['email']
                session['level'] = account['level']
                session['user_id'] = account['id']
                logger.info(f"User {account['username']} logged in successfully")
                return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash("An error occurred during login", "danger")
    return render_template('auth-login-minimal.html')

@app.route('/registrasi', methods=['GET', 'POST'])
def registrasi():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            cpassword = request.form.get('cpassword', '')
            fullname = request.form.get('fullname', '').strip()

            if not all([email, username, password, cpassword, fullname]):
                flash("All fields are required", "warning")
                return render_template('auth-register-minimal.html')
            if password != cpassword:
                flash("Passwords do not match", "warning")
                return render_template('auth-register-minimal.html')

            cursor = get_db_connection()
            if not cursor:
                flash("Database error occurred", "danger")
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
            flash("An error occurred during registration", "danger")
    return render_template('auth-register-minimal.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/assets/<path:filename>')
def send_assets(filename):
    return send_from_directory('static/assets', filename)

@app.route('/chat')
def appchat():
    if 'loggedin' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    cursor = get_db_connection()
    if not cursor:
        flash("Database error occurred", "danger")
        return redirect(url_for('index'))

    cursor.execute("SELECT id, username, level FROM tb_user WHERE username != %s", (session['username'],))
    users = cursor.fetchall()
    cursor.close()

    contacts = [{'id': user['id'], 'username': user['username'], 'level': user['level']} for user in users]
    return render_template('apps-chat.html', contacts=contacts, current_user=session['username'])

@app.route('/get_messages/<receiver>')
def get_messages(receiver):
    if 'loggedin' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    sender = session['username']
    cursor = get_db_connection()
    if not cursor:
        return jsonify({'error': 'Database error'}), 500

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

@app.route('/info')
def info():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = get_db_connection()
    if not cursor:
        flash("Database error occurred", "danger")
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM tb_info_user WHERE user_id = %s", (user_id,))
    info_user = cursor.fetchone()
    cursor.close()

    if not info_user:
        flash("User info not found", "warning")
        return redirect(url_for('index'))
    return render_template('leads-view.html', info_user=info_user)

@app.route('/update')
def update():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    username = session['username']
    cursor = get_db_connection()
    if not cursor:
        flash("Database error occurred", "danger")
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM tb_info_user WHERE username = %s", (username,))
    user_data = cursor.fetchone()
    cursor.close()
    return render_template('leads-create.html', user=user_data)

@app.route('/update_data', methods=['POST'])
def update_data():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    try:
        userid = session['user_id']
        cursor = get_db_connection()
        if not cursor:
            flash("Database error occurred", "danger")
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

        if not data['username'] or not data['email']:
            flash("Username and email are required", "warning")
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

if __name__ == '__main__':
    app.run(port=5000, debug=True, host='127.0.0.0')