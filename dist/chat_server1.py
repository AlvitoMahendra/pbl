from flask import Flask, request, session
from flask_socketio import SocketIO, emit, disconnect
import mysql.connector
from datetime import datetime
from queue import Queue
import threading
import logging
import os
import bleach  # Untuk sanitasi input

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # Gunakan secret key dari env atau random
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5001", "https://yourdomain.com"])  # Batasi CORS

# Struktur data untuk pengguna dan pesan
online_users = {}
offline_messages = {}
message_queue = Queue(maxsize=1000)  # Batas ukuran queue

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fungsi untuk koneksi database
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),  # Ganti 'root' dengan user khusus
        password=os.environ.get('DB_PASSWORD', ''),  # Ganti dengan password aman
        database=os.environ.get('DB_NAME', 'pblrks2')
    )

# Proses pesan di background
def process_queue_background():
    while True:
        if not message_queue.empty():
            message_data = message_queue.get()
            conn = None
            cursor = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tb_messages (sender, receiver, message) VALUES (%s, %s, %s)",
                    (message_data['sender'], message_data['receiver'], message_data['message'])
                )
                conn.commit()
                message_id = cursor.lastrowid
                message_data['id'] = message_id
                logger.info(f"Pesan diproses: {message_data}")

                socketio.emit('receive_message', message_data)
                receiver = message_data['receiver']
                if receiver in online_users:
                    socketio.emit('receive_message', message_data, room=online_users[receiver])
                else:
                    if receiver not in offline_messages:
                        offline_messages[receiver] = Queue(maxsize=100)  # Batas ukuran pesan offline
                    try:
                        offline_messages[receiver].put(message_data, block=False)
                        logger.info(f"Pesan disimpan untuk offline: {receiver}")
                    except Queue.Full:
                        logger.warning(f"Queue offline untuk {receiver} penuh, pesan dibuang")

            except Exception as e:
                logger.error(f"Error memproses pesan: {e}")
                try:
                    message_queue.put(message_data, block=False)  # Kembalikan ke queue jika gagal
                except Queue.Full:
                    logger.error("Queue utama penuh, pesan hilang")
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

# Jalankan proses queue di thread terpisah
thread = threading.Thread(target=process_queue_background, daemon=True)
thread.start()

# Event handler untuk koneksi SocketIO
@socketio.on('connect')
def handle_connect():
    if 'username' not in session:
        disconnect()
        return
    username = session['username']
    sid = request.sid
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tb_user SET socket_id = %s WHERE username = %s", (sid, username))
        conn.commit()
        online_users[username] = sid
        emit('user_status', {'username': username, 'status': 'online'}, broadcast=True)
        if username in offline_messages:
            while not offline_messages[username].empty():
                emit('receive_message', offline_messages[username].get())
            del offline_messages[username]
    except Exception as e:
        logger.error(f"Error saat connect: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@socketio.on('disconnect')
def handle_disconnect():
    if 'username' not in session:
        return
    username = session['username']
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tb_user SET socket_id = NULL WHERE username = %s", (username,))
        conn.commit()
        online_users.pop(username, None)
        emit('user_status', {'username': username, 'status': 'offline'}, broadcast=True)
    except Exception as e:
        logger.error(f"Error saat disconnect: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@socketio.on('send_message')
def handle_send_message(data):
    if 'username' not in session:
        return
    sender = session['username']
    receiver = data.get('receiver')
    message = data.get('message')

    # Validasi input
    if not receiver or not message:
        emit('error', {'message': 'Receiver dan message tidak boleh kosong'})
        return
    
    # Sanitasi pesan
    message = bleach.clean(message)  # Menghapus tag HTML berbahaya
    
    # Verifikasi receiver ada di database
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM tb_user WHERE username = %s", (receiver,))
        if not cursor.fetchone():
            emit('error', {'message': f'Pengguna {receiver} tidak ditemukan'})
            return
    except Exception as e:
        logger.error(f"Error verifikasi receiver: {e}")
        emit('error', {'message': 'Terjadi kesalahan server'})
        return
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    now = datetime.now()
    message_data = {
        'sender': sender,
        'receiver': receiver,
        'message': message,
        'timestamp': now.strftime('%d/%m/%Y %H:%M:%S')
    }
    logger.info(f"Pesan masuk ke queue: {message_data}")
    try:
        message_queue.put(message_data, block=False)
    except Queue.Full:
        logger.error("Queue penuh, pesan ditolak")
        emit('error', {'message': 'Server sibuk, coba lagi nanti'})

if __name__ == '__main__':
    # Gunakan host '127.0.0.1' untuk lokal, atau sesuaikan dengan kebutuhan
    socketio.run(app, host="127.0.0.1", port=5001, debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')