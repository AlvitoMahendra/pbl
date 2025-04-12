from flask import Flask, request, session
from flask_socketio import SocketIO, emit, disconnect
import mysql.connector
from datetime import datetime
from queue import Queue
import threading
import logging
import os
import bleach

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5000"])  # Izinkan dari website

# Struktur data untuk pengguna dan pesan
online_users = {}
offline_messages = {}
message_queue = Queue(maxsize=1000)

# Setup logging
logging.basicConfig(level=logging.INFO, filename='chat.log')
logger = logging.getLogger(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'pblrks2')
    )

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
                logger.info(f"Processed message: {message_data}")

                socketio.emit('receive_message', message_data)
                receiver = message_data['receiver']
                if receiver in online_users:
                    socketio.emit('receive_message', message_data, room=online_users[receiver])
                else:
                    if receiver not in offline_messages:
                        offline_messages[receiver] = Queue(maxsize=100)
                    try:
                        offline_messages[receiver].put(message_data, block=False)
                        logger.info(f"Stored offline message for: {receiver}")
                    except Queue.Full:
                        logger.warning(f"Offline queue full for {receiver}, message dropped")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                try:
                    message_queue.put(message_data, block=False)
                except Queue.Full:
                    logger.error("Main queue full, message lost")
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

thread = threading.Thread(target=process_queue_background, daemon=True)
thread.start()

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
        logger.error(f"Connect error: {e}")
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
        logger.error(f"Disconnect error: {e}")
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

    if not receiver or not message:
        emit('error', {'message': 'Receiver and message cannot be empty'})
        return
    
    message = bleach.clean(message)
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM tb_user WHERE username = %s", (receiver,))
        if not cursor.fetchone():
            emit('error', {'message': f'User {receiver} not found'})
            return
    except Exception as e:
        logger.error(f"Receiver verification error: {e}")
        emit('error', {'message': 'Server error'})
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
    logger.info(f"Message queued: {message_data}")
    try:
        message_queue.put(message_data, block=False)
    except Queue.Full:
        logger.error("Queue full, message rejected")
        emit('error', {'message': 'Server busy, try again later'})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)