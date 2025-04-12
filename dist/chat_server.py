# from flask import Flask, request, session
# from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
# import mysql.connector
# from datetime import datetime
# import json

# # Konfigurasi database
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': '',
#     'database': 'pblrks2'
# }

# app = Flask(__name__)
# app.secret_key = "apaja"
# socketio = SocketIO(app, cors_allowed_origins="*")

# # Menyimpan data pengguna yang online
# online_users = {}

# def get_db_connection():
#     return mysql.connector.connect(**db_config)

# @socketio.on('connect')
# def handle_connect():
#     if 'username' not in session:
#         disconnect()
#         return
    
#     username = session['username']
#     sid = request.sid
    
#     # Update socket_id di database dan simpan di online_users
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("UPDATE tb_user SET socket_id = %s WHERE username = %s", (sid, username))
#     conn.commit()
    
#     online_users[username] = sid
    
#     # Beritahu semua pengguna bahwa pengguna ini online
#     emit('user_status', {'username': username, 'status': 'online'}, broadcast=True)
#     cursor.close()
#     conn.close()

# @socketio.on('disconnect')
# def handle_disconnect():
#     if 'username' not in session:
#         return
    
#     username = session['username']
    
#     # Hapus socket_id dari database dan hapus dari online_users
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("UPDATE tb_user SET socket_id = NULL WHERE username = %s", (username,))
#     conn.commit()
    
#     online_users.pop(username, None)
    
#     # Beritahu semua pengguna bahwa pengguna ini offline
#     emit('user_status', {'username': username, 'status': 'offline'}, broadcast=True)
#     cursor.close()
#     conn.close()

# @socketio.on('send_message')
# def handle_send_message(data):
#     if 'username' not in session:
#         return
    
#     sender = session['username']
#     receiver = data['receiver']
#     message = data['message']
    
#     # Simpan pesan ke database
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("INSERT INTO tb_messages (sender, receiver, message) VALUES (%s, %s, %s)", 
#                   (sender, receiver, message))
#     conn.commit()
    
#     # Dapatkan ID pesan yang baru saja disimpan
#     message_id = cursor.lastrowid
    
#     # Format timestamp
#     now = datetime.now()
#     timestamp = now.strftime('%d/%m/%Y %H:%M:%S')
    
#     # Siapkan data pesan
#     message_data = {
#         'id': message_id,
#         'sender': sender,
#         'receiver': receiver,
#         'message': message,
#         'timestamp': timestamp
#     }
    
#     # Kirim pesan ke pengirim
#     emit('receive_message', message_data)
    
#     # Kirim pesan ke penerima jika online
#     if receiver in online_users:
#         emit('receive_message', message_data, room=online_users[receiver])
    
#     cursor.close()
#     conn.close()

# if __name__ == '__main__':
#     socketio.run(app, host="0.0.0.0", port=5001, debug=True) 



# from flask import Flask, request, session
# from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
# import mysql.connector
# from datetime import datetime
# import json
# from queue import Queue

# # Konfigurasi database
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': '',
#     'database': 'pblrks2'
# }

# app = Flask(__name__)
# app.secret_key = "apaja"
# socketio = SocketIO(app, cors_allowed_origins="*")

# # Menyimpan data pengguna yang online
# online_users = {}

# # Menyimpan pesan offline dalam queue untuk setiap pengguna
# offline_messages = {}  # Dictionary dengan Queue untuk setiap pengguna offline

# # Queue untuk memproses pesan secara berurutan
# message_queue = Queue()

# def get_db_connection():
#     return mysql.connector.connect(**db_config)

# def process_queue():
#     while not message_queue.empty():
#         message_data = message_queue.get()
        
#         # Simpan ke database
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO tb_messages (sender, receiver, message) VALUES (%s, %s, %s)", 
#                       (message_data['sender'], message_data['receiver'], message_data['message']))
#         conn.commit()
#         message_id = cursor.lastrowid
#         message_data['id'] = message_id
        
#         # Kirim pesan ke pengirim
#         emit('receive_message', message_data)
        
#         # Kirim ke penerima jika online, jika tidak simpan ke offline queue
#         receiver = message_data['receiver']
#         if receiver in online_users:
#             emit('receive_message', message_data, room=online_users[receiver])
#         else:
#             if receiver not in offline_messages:
#                 offline_messages[receiver] = Queue()
#             offline_messages[receiver].put(message_data)
        
#         cursor.close()
#         conn.close()

# @socketio.on('connect')
# def handle_connect():
#     if 'username' not in session:
#         disconnect()
#         return
    
#     username = session['username']
#     sid = request.sid
    
#     # Update socket_id di database dan simpan di online_users
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("UPDATE tb_user SET socket_id = %s WHERE username = %s", (sid, username))
#     conn.commit()
    
#     online_users[username] = sid
    
#     # Beritahu semua pengguna bahwa pengguna ini online
#     emit('user_status', {'username': username, 'status': 'online'}, broadcast=True)
    
#     # Kirim pesan offline yang tertunda (jika ada)
#     if username in offline_messages:
#         while not offline_messages[username].empty():
#             emit('receive_message', offline_messages[username].get())
#         del offline_messages[username]
    
#     cursor.close()
#     conn.close()

# @socketio.on('disconnect')
# def handle_disconnect():
#     if 'username' not in session:
#         return
    
#     username = session['username']
    
#     # Hapus socket_id dari database dan hapus dari online_users
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("UPDATE tb_user SET socket_id = NULL WHERE username = %s", (username,))
#     conn.commit()
    
#     online_users.pop(username, None)
    
#     # Beritahu semua pengguna bahwa pengguna ini offline
#     emit('user_status', {'username': username, 'status': 'offline'}, broadcast=True)
#     cursor.close()
#     conn.close()

# @socketio.on('send_message')
# def handle_send_message(data):
#     if 'username' not in session:
#         return
    
#     sender = session['username']
#     receiver = data['receiver']
#     message = data['message']
    
#     # Siapkan data pesan
#     now = datetime.now()
#     message_data = {
#         'sender': sender,
#         'receiver': receiver,
#         'message': message,
#         'timestamp': now.strftime('%d/%m/%Y %H:%M:%S')
#     }
    
#     # Tambahkan pesan ke queue untuk diproses
#     message_queue.put(message_data)
    
#     # Proses queue
#     process_queue()

# if __name__ == '__main__':
#     socketio.run(app, host="0.0.0.0", port=5001, debug=True)


from flask import Flask, request, session
from flask_socketio import SocketIO, emit, disconnect
import mysql.connector
from datetime import datetime
from queue import Queue
import threading
import logging
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
socketio = SocketIO(app, cors_allowed_origins="*")

online_users = {}
offline_messages = {}
message_queue = Queue()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return mysql.connector.connect(host='localhost', user='root', password='', database='pblrks2')

def process_queue_background():
    while True:
        if not message_queue.empty():
            message_data = message_queue.get()
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO tb_messages (sender, receiver, message) VALUES (%s, %s, %s)", 
                              (message_data['sender'], message_data['receiver'], message_data['message']))
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
                        offline_messages[receiver] = Queue()
                    offline_messages[receiver].put(message_data)
                    logger.info(f"Pesan disimpan untuk offline: {receiver}")
                
                cursor.close()
                conn.close()
            except Exception as e:
                logger.error(f"Error memproses pesan: {e}")
                message_queue.put(message_data)  # Kembalikan pesan ke queue jika gagal

# Jalankan proses queue di thread terpisah
thread = threading.Thread(target=process_queue_background, daemon=True)
thread.start()

@socketio.on('connect')
def handle_connect():
    if 'username' not in session:
        disconnect()
        return
    username = session['username']
    sid = request.sid
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
    cursor.close()
    conn.close()

@socketio.on('disconnect')
def handle_disconnect():
    if 'username' not in session:
        return
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tb_user SET socket_id = NULL WHERE username = %s", (username,))
    conn.commit()
    online_users.pop(username, None)
    emit('user_status', {'username': username, 'status': 'offline'}, broadcast=True)
    cursor.close()
    conn.close()

@socketio.on('send_message')
def handle_send_message(data):
    if 'username' not in session:
        return
    sender = session['username']
    receiver = data['receiver']
    message = data['message']
    now = datetime.now()
    message_data = {
        'sender': sender,
        'receiver': receiver,
        'message': message,
        'timestamp': now.strftime('%d/%m/%Y %H:%M:%S')
    }
    logger.info(f"Pesan masuk ke queue: {message_data}")
    message_queue.put(message_data)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)