from flask import Flask, render_template, request, url_for, session, send_from_directory, flash, redirect
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)

app.secret_key = "apaja"
app.config["MYSQL_HOST"] = 'localhost'
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"] = ''
app.config["MYSQL_DB"] = 'pblrks2'

mysql = MySQL(app)


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

        # cek data username
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM tb_user WHERE username=%s OR email=%s", (identifier, identifier))
        account = cursor.fetchone()  

        # stored_password = account[4]  # Ambil password hash dari database

        if account is None:  # Sama seperti di registrasi
            flash("Failed login, please try again!", "danger")
        elif not check_password_hash(account[4], password):
            flash("Failed login, please try again!", "danger")
        
        else:
            # if check_password_hash(stored_password, password):
            session['loggedin'] = True
            session['username'] = account[1]  # Simpan username ke session
            session['email'] = account[2]  # Simpan email ke session
            session['level'] = account[3] #level
            return redirect(url_for('index'))  
        
    return render_template('auth-login-minimal.html')



@app.route('/registrasi', methods=('GET','POST'))
def registrasi():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        cpassword = request.form['cpassword']
        if password != cpassword:
            flash("Confirmation Password is not the same", "warning") 
            return render_template('auth-register-minimal.html')



        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tb_user WHERE username=%s OR email=%s', (username, email))
        account = cursor.fetchone()


        if account is None:
            hashed_password = generate_password_hash(password)  # Hash password dulu
            cursor.execute("INSERT INTO tb_user (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
            # cursor.execute("INSERT INTO tb_user VALUES(NULL, %s, %s, %s)", (username, email, generate_password_hash(password)))
            mysql.connection.commit()
            flash("registrasi berhasil", "success")
        else:
            flash("username dan email sudah ada", 'danger')
            
    return render_template('auth-register-minimal.html')

# fungsi logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('level', None)
    return redirect(url_for('login'))



@app.route('/assets/<path:filename>')
def send_assets(filename):
    return send_from_directory('static/assets', filename)



# FITUR USER
@app.route('/chat')
def appchat():
    return render_template('apps-chat.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
