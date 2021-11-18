from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'many random bytes'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_assert_registry'

mysql = MySQL(app)

@app.route('/')
def Index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT  * FROM assets")
    data = cur.fetchall()
    cur.close()
    return render_template('index.html', students=data )

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
    cur.execute("DELETE FROM assets WHERE asset_id=%s", (id_data,))
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
