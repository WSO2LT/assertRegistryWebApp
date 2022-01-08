import time
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import bcrypt
import re
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'many random bytes'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_assert_registry'

mysql = MySQL(app)

@app.route('/')
def Index():
    if session.get('logged_in') and session['logged_in']:
        cur = mysql.connection.cursor()
        cur.execute("SELECT  * FROM assets")
        data = cur.fetchall()
        cur.close()
        return render_template('index.html', assets=data, page="home" )
    else:
        return redirect(url_for('login'))

@app.route('/login', methods =['GET', 'POST'])
def login():
    if session.get('logged_in') and session['logged_in']:
        flash('You have already logged in!', 'warning')
        return redirect('/')
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        if user:
            if bcrypt.hashpw(password, user["password"].encode('utf-8')) == user["password"].encode('utf-8'):
                session['logged_in'] = True
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                return redirect('/')
        else:
            flash('Incorrect username / password !', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'confirm_password' in request.form :
        username = request.form['username']
        plainpwd = request.form['password']
        confpwd = request.form['confirm_password']
        password = bcrypt.hashpw(plainpwd.encode('utf-8'), bcrypt.gensalt())
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE username=%s', (username,))
        account = cur.fetchone()
        if account:
            flash('Account already exists !', 'danger')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', username):
            flash('Invalid email address !', 'danger')
        elif not (confpwd == confpwd):
            flash('Passwords are not matching', 'danger')
        elif not username or not plainpwd or not confpwd:
            flash('Please fill out the form !', 'danger')
        else:
            cur.execute('INSERT INTO users (username, password, reset_token) VALUES (%s, %s, NULL)', (username, password))
            mysql.connection.commit()
            flash("You have successfully registered ! Please login.", 'success')
            return redirect(url_for('login'))
    elif request.method == 'POST':
        flash("Please fill out the form !", 'danger')
    return render_template('register.html')

@app.route('/insert', methods = ['POST'])
def insert():
    if request.method == "POST":
        flash("New Asset Inserted Successfully")
        name = request.form['name']
        owner = request.form['owner']
        description = request.form['description']
        location = request.form['location']
        criticality = request.form['criticality']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO assets (asset_name, asset_owner, asset_description, asset_location, criticality) VALUES (%s, %s, %s, %s, %s)", (name, owner, description, location, criticality))
        mysql.connection.commit()
        return redirect(url_for('Index'))

@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM assets WHERE asset_id=%s", (id_data))
    mysql.connection.commit()
    return redirect(url_for('Index'))

@app.route('/update',methods=['POST','GET'])
def update():
    if request.method == 'POST':
        id_data = request.form['id']
        name = request.form['name']
        owner = request.form['owner']
        description = request.form['description']
        location = request.form['location']
        criticality = request.form['criticality']
        cur = mysql.connection.cursor()
        cur.execute("""
               UPDATE assets
               SET asset_name=%s, asset_owner=%s, asset_description=%s, asset_location=%s, criticality=%s
               WHERE asset_id=%s
            """, (name, owner, description, location, criticality, id_data))
        flash("Asset Data Updated Successfully")
        mysql.connection.commit()
        return redirect(url_for('Index'))

if __name__ == "__main__":
    app.run(debug=True)
