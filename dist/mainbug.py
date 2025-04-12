from flask import Flask, render_template, request, url_for, session, send_from_directory, flash, redirect, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from datetime import datetime
import json
import MySQLdb.cursors
import queue
import threading

app = Flask(__name__)

app.secret_key = "apaja"
app.config["MYSQL_HOST"] = 'localhost'
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"] = ''
app.config["MYSQL_DB"] = 'pblrks2'

mysql = MySQL(app)
socketio = SocketIO(app)

# Menyimpan data pengguna yang online
online_users = {}

# Inisialisasi Queue untuk pesan
message_queue = queue.Queue()

# Fungsi untuk memproses pesan dari queue
def process_messages():
    while True:
        # Ambil pesan dari queue
        sender, receiver, message = message_queue.get()
        
        # Simpan pesan ke database
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO tb_messages (sender, receiver, message) VALUES (%s, %s, %s)", 
                       (sender, receiver, message))
        mysql.connection.commit()
        
        # Dapatkan ID pesan yang baru saja disimpan
        message_id = cursor.lastrowid
        
        # Format timestamp
        now = datetime.now()
        timestamp = now.strftime('%d/%m/%Y %H:%M:%S')
        
        # Siapkan data pesan
        message_data = {
            'id': message_id,
            'sender': sender,
            'receiver': receiver,
            'message': message,
            'timestamp': timestamp
        }
        
        # Kirim pesan ke pengirim
        socketio.emit('receive_message', message_data, room=online_users.get(sender))
        
        # Kirim pesan ke penerima jika online
        if receiver in online_users:
            socketio.emit('receive_message', message_data, room=online_users[receiver])
        
        # Tandai tugas selesai
        message_queue.task_done()

# Jalankan thread untuk memproses queue
threading.Thread(target=process_messages, daemon=True).start()

@app.route('/')
def index():
    if 'loggedin' in session:
        return render_template('index.html')
    flash('please login first')
    return redirect(url_for('login'))

@app.route('/login', methods=('GET', 'POST'))
def login():    
    if request.method == 'POST':
        identifier = request.form['indentifier']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM tb_user WHERE username=%s OR email=%s", (identifier, identifier))
        account = cursor.fetchone()  

        if account is None:
            flash("Failed login, please try again!", "danger")
        elif not check_password_hash(account[4], password):
            flash("Failed login, please try again!", "danger")
        else:
            session['loggedin'] = True
            session['username'] = account[1]
            session['email'] = account[2]
            session['level'] = account[3]
            session['user_id'] = account[0]
            return redirect(url_for('index'))  
        
    return render_template('auth-login-minimal.html')

@app.route('/registrasi', methods=('GET','POST'))
def registrasi():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        cpassword = request.form['cpassword']
        fullname = request.form['fullname']
        if password != cpassword:
            flash("Confirmation Password is not the same", "warning") 
            return render_template('auth-register-minimal.html')

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tb_user WHERE username=%s OR email=%s', (username, email))
        account = cursor.fetchone()

        if account is None:
            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO tb_user (username, email, password, fullname) VALUES (%s, %s, %s, %s)", 
                           (username, email, hashed_password, fullname))
           
            user_id = cursor.lastrowid
            cursor.execute("SELECT level FROM tb_user WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            user_level = result[0] if result else "USER"
            cursor.execute("INSERT INTO tb_info_user (user_id, username, email, level, fullname) VALUES (%s, %s, %s, %s, %s)",
                           (user_id, username, email, user_level, fullname))

            mysql.connection.commit()
            flash("registrasi berhasil", "success")
        else:
            flash("username dan email sudah ada", 'danger')
            
    return render_template('auth-register-minimal.html')

@app.route('/logout')
def logout():
    if 'loggedin' in session and 'username' in session:
        username = session['username']
        if username in online_users:
            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE tb_user SET socket_id = NULL WHERE username = %s", (username,))
            mysql.connection.commit()
            online_users.pop(username, None)
    
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('level', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/assets/<path:filename>')
def send_assets(filename):
    return send_from_directory('static/assets', filename)

@app.route('/chat')
def appchat():
    if 'loggedin' not in session:
        flash('please login first')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, username, level, socket_id FROM tb_user WHERE username != %s", (session['username'],))
    users = cursor.fetchall()
    contacts = []
    
    for user in users:
        status = "online" if user[3] is not None else "offline"
        contacts.append({
            'id': user[0],
            'username': user[1],
            'level': user[2],
            'status': status
        })
    
    return render_template('apps-chat.html', contacts=contacts, current_user=session['username'])

@app.route('/get_messages/<receiver>')
def get_messages(receiver):
    if 'loggedin' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    sender = session['username']
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT * FROM tb_messages 
        WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
        ORDER BY timestamp ASC
    """, (sender, receiver, receiver, sender))
    
    messages = cursor.fetchall()
    result = []
    
    for message in messages:
        result.append({
            'id': message[0],
            'sender': message[1],
            'receiver': message[2],
            'message': message[3],
            'timestamp': message[4].strftime('%d/%m/%Y %H:%M:%S') if message[4] else ''
        })
    
    return jsonify(result)

@app.route('/info')
def info():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM tb_info_user WHERE user_id = %s", (user_id,))
    info_user = cursor.fetchone()
    cursor.close()

    return render_template('leads-view.html', info_user=info_user)

@app.route('/update')
def update():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    username = session['username']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM tb_info_user WHERE username = %s", (username,))
    user_data = cursor.fetchone()
    cursor.close()

    return render_template('leads-create.html', user=user_data)

@app.route('/update_data', methods=['POST'])
def update_data():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    userid = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    username = request.form['username']
    fullname = request.form['fullname']
    birthday = request.form['birthday']
    email = request.form['email']
    nohp = request.form['nohp']
    city = request.form['city']
    country = request.form['country']
    state = request.form['state']
    address = request.form['address']

    cursor.execute("""
        UPDATE tb_info_user SET username=%s, fullname=%s, birthday=%s, email=%s, nohp=%s, city=%s, country=%s, state=%s, address=%s WHERE user_id=%s
    """, (username, fullname, birthday, email, nohp, city, country, state, address, userid))

    mysql.connection.commit()
    cursor.close()

    flash("Data berhasil diperbarui!", "success")
    return redirect(url_for('update'))

@socketio.on('connect')
def handle_connect():
    if 'username' not in session:
        disconnect()
        return
    
    username = session['username']
    sid = request.sid
    
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE tb_user SET socket_id = %s WHERE username = %s", (sid, username))
    mysql.connection.commit()
    
    online_users[username] = sid
    emit('user_status', {'username': username, 'status': 'online'}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if 'username' not in session:
        return
    
    username = session['username']
    
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE tb_user SET socket_id = NULL WHERE username = %s", (username,))
    mysql.connection.commit()
    
    online_users.pop(username, None)
    emit('user_status', {'username': username, 'status': 'offline'}, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    if 'username' not in session:
        return
    
    sender = session['username']
    receiver = data['receiver']
    message = data['message']
    
    # Tambahkan pesan ke queue untuk diproses secara asynchronous
    message_queue.put((sender, receiver, message))

if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True)