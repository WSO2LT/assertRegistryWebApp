import time
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import bcrypt
import re
import MySQLdb.cursors
import redis
from flask_paginate import Pagination

app = Flask(__name__)
app.secret_key = 'many random bytes'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_assert_registry'

r = redis.Redis(host='', port=6379, password='')

mysql = MySQL(app)
@app.route('/', methods = ['POST','GET'])
def Index(limit=10):
    if request.method == 'POST':
        searchStr = '%'+request.form['searchStr']+'%'
        if(r.exists(searchStr)):
            data = eval(r.get(searchStr))
            print("from Cache")
        else:
            print("Search triggered")
            cur = mysql.connection.cursor()
            cur.execute("SELECT  * FROM assets WHERE concat('.',asset_name, '.',asset_owner, '.', criticality, '.',asset_location, '.')  LIKE %s ",(searchStr,))
            data = cur.fetchall()
            cur.close()
            r.psetex(searchStr, 10000, str(data))
        page = int(request.args.get("page", 1))
        start = (page - 1) * limit
        end = page * limit if len(data) > page * limit else len(data)
        paginate = Pagination(page=page, total=len(data))
        ret = data[start:end]
        
        return render_template('index.html', assets=ret, page="home",paginate=paginate )
    else:
        if session.get('logged_in') and session['logged_in']:
            if(r.exists("assets")):
                data = eval(r.get("assets"))
                print("from cache")
            else:
                cur = mysql.connection.cursor()
                cur.execute("SELECT  * FROM assets")
                data = cur.fetchall()
                cur.close()
                r.psetex("assets", 10000, str(data))
            page = int(request.args.get("page", 1))
            start = (page - 1) * limit
            end = page * limit if len(data) > page * limit else len(data)
            paginate = Pagination(page=page, total=len(data))
            ret = data[start:end]
            
            return render_template('index.html', assets=ret, page="home",paginate=paginate )
        else:
            return redirect(url_for('login'))

@app.route('/login', methods =['GET', 'POST'])
def login():
    if session.get('logged_in') and session['logged_in']:
        flash('You have already logged in!', 'warning')
        return redirect('/')
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        if user:
            if bcrypt.hashpw(password, user["password"].encode('utf-8')) == user["password"].encode('utf-8'):
                session['logged_in'] = True
                session['user_id'] = user['user_id']
                session['username'] = user['name']
                session['level']=user['access_level']
                return redirect('/')
        else:
            flash('Incorrect Email / Password ! ', 'danger')
            flash('Contact an administrator to reset your password ', 'warning')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('level', None)
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
    if (session['level']=='Admin') or (session['level']=='Editor'):
        if request.method == "POST":
            flash("New Asset Inserted Successfully", 'success')
            name = request.form['name']
            owner = request.form['owner']
            description = request.form['description']
            location = request.form['location']
            criticality = request.form['criticality']
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO assets (asset_name, asset_owner, asset_description, asset_location, criticality) VALUES (%s, %s, %s, %s, %s)", (name, owner, description, location, criticality))
            mysql.connection.commit()
            return redirect(url_for('Index'))
    else:
        flash("You are not authorized", 'danger')
        return redirect(url_for('Index'))



@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    if (session['level']=='Admin') or (session['level']=='Editor'):
        flash("Record Has Been Deleted Successfully", 'success')
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM assets WHERE asset_id=%s", (id_data))
        mysql.connection.commit()
        return redirect(url_for('Index'))
    else:
        flash("You are not authorized", 'danger')
        return redirect(url_for('Index'))

@app.route('/update',methods=['POST','GET'])
def update():
    if (session['level']=='Admin') or (session['level']=='Editor'):
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
            flash("Asset Data Updated Successfully", 'success')
            mysql.connection.commit()
            return redirect(url_for('Index'))
    else:
        flash("You are not authorized", 'danger')
        return redirect(url_for('Index'))

@app.route('/users', methods =['GET', 'POST'])
def users():
    if session.get('logged_in') and session['logged_in'] and (session['level']=='Admin'):
        cur = mysql.connection.cursor()
        cur.execute("SELECT  * FROM users")
        data = cur.fetchall()
        cur.close()
        return render_template('users.html', assets=data, page="users" )
    else:
        flash("Not Authorized" ,'danger')
        return redirect(url_for('login'))


@app.route('/adduser', methods = ['POST'])
def adduser():
    if request.method == "POST":
        if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form and 'emp_id' in request.form and 'level' in request.form :
            name = request.form['name']
            plainpwd = request.form['password']
            email = request.form['email']
            empid = request.form['emp_id']
            accesslevel = request.form['level']
            password = bcrypt.hashpw(plainpwd.encode('utf-8'), bcrypt.gensalt())
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM users WHERE email=%s', (email,))
            account = cur.fetchone()
        if account:
            flash('Account already exists !', 'danger')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address !', 'danger')
        elif not name or not plainpwd or not email:
            flash('Please fill out the form !', 'danger')
        else:
            cur.execute('INSERT INTO users (name,email,emp_id, password,access_level, reset_token) VALUES (%s,%s,%s, %s,%s, NULL)', (name,email,empid,password,accesslevel))
            mysql.connection.commit()
            flash("User has been successfully added", 'success')
            return redirect(url_for('users'))      
    elif request.method == 'POST':
        flash("Please fill out the form !", 'danger')
    return redirect(url_for('users'))


@app.route('/deleteUser/<string:id_data>', methods = ['GET'])
def deleteUser(id_data):
    flash("Record Has Been Deleted Successfully",'success')
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE user_id=%s", (id_data))
    mysql.connection.commit()
    return redirect(url_for('users'))

@app.route('/editUserInfo',methods=['POST','GET'])
def editUserInfo():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        empid = request.form['emp_id']
        accesslevel = request.form['level']
        user_id = request.form['user_id']
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address !', 'danger')
        elif not name or not empid or not email:
            flash('Please fill out the form !', 'danger')
        else:
            cur = mysql.connection.cursor()
            cur.execute("""UPDATE users SET name=%s, email=%s, emp_id=%s, access_level=%s WHERE user_id=%s """, (name, email, empid, accesslevel, user_id))
            flash("User Data Updated Successfully",'success')
            mysql.connection.commit()
        return redirect(url_for('users'))

@app.route('/changePass', methods =['GET', 'POST'])
def changePass():
    if request.method == 'POST' and 'password' in request.form and 'user_id' in request.form  and 'passwordConf' in request.form :
        plainpwd = request.form['password']
        user_id = request.form['user_id']
        confpwd = request.form['passwordConf']
        password = bcrypt.hashpw(plainpwd.encode('utf-8'), bcrypt.gensalt())
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE user_id=%s', (user_id,))
        account = cur.fetchone()
        if not (confpwd == confpwd):
            flash('Passwords are not matching', 'danger')
        else:
            cur.execute("""UPDATE users SET password=%s WHERE user_id=%s """, (password, user_id))
            mysql.connection.commit()
            flash("You have successfully changed the password", 'success')
            return redirect(url_for('users'))
    elif request.method == 'POST':
        flash("Please fill out the form !", 'danger')
    return redirect(url_for('users'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
