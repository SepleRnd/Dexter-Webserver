from flask import Flask, render_template, request, jsonify, session, url_for, redirect
import sqlite3
from sqlite3 import Error
import os

app = Flask(__name__)
app.secret_key = "SEPLe"  # Set secret key for session

# Define the path to your SQLite database file
db_file = "sepleDB.db"

def create_connection(db_file):
    """Create a database connection to an SQLite database."""
    conn = None
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, db_file)
        conn = sqlite3.connect(db_path)
        return conn
    except Error as e:
        print(f"Error creating database connection: {e}")
    return conn

@app.after_request
def add_header(response):
    """Control cache and session in the browser."""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

## Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = create_connection("myDatabase.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        if user_data:
            session['username'] = username
            return redirect(url_for('device_config'))
        else:
            return render_template('index.html', ALert_pass=True) 

    return render_template('index.html')

## Reset password route
@app.route('/resetpassword', methods=['GET', 'POST'])
def resetpassword():
    if request.method == 'POST': 
        username = request.form['username']
        password = request.form['password']
        npassword = request.form['newpassword']
        cpassword = request.form['cpassword']
        
        db = create_connection("myDatabase.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        existing_user = cursor.fetchone()
        cursor.close()

        if existing_user:
            if npassword == cpassword:
                cursor = db.cursor()
                cursor.execute("UPDATE users SET password=? WHERE username=?", (npassword, username))
                db.commit()
                cursor.close()
                db.close()
                return render_template('index.html', reset_password=True)
            else:
                return render_template('reset.html', not_same=True)
        else:
            return render_template('reset.html', wrong_password=True)
    return render_template('reset.html')

## Device Config route
@app.route('/device_config')
def device_config():
    if 'username' in session:
        username = session['username']
        db = create_connection("myDatabase.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('device_config.html', user=user_data)
    return redirect(url_for('login'))

## Get zone data route
@app.route('/get_zone')
def get_zone():
    db = create_connection("myDatabase.db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM zone")
    zones_data = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(zones_data)

## Update zone data route
@app.route('/update_zone', methods=['PUT'])
def update_zone():
    if request.method == 'PUT':
        data = request.json
        db = create_connection("myDatabase.db")
        cursor = db.cursor()
        for zone_data in data:    
            zoneId = zone_data['zoneId']
            activated = zone_data['activated']
            selectedDevice = zone_data['selectedDevice']
            buzzerStatus = zone_data['buzzerStatus']
            
            cursor.execute("SELECT * FROM zone WHERE zoneId=?", (zoneId,))
            existing_zone = cursor.fetchone()
            
            if existing_zone:
                cursor.execute("UPDATE zone SET activated=?, selectedDevice=?, buzzerStatus=? WHERE zoneId=?", (activated, selectedDevice, buzzerStatus, zoneId))
            else:
                cursor.execute("INSERT INTO zone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, ?, ?, ?)", (zoneId, activated, selectedDevice, buzzerStatus))
        
        db.commit()
        cursor.close()
        db.close()
    return jsonify({'Message': 'Done'})

## Power Zone route
@app.route('/powerzone_config')
def powerzone_config():
    if 'username' in session:
        username = session['username']
        db = create_connection("myDatabase.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('powerzone_config.html', user=user_data)
    return redirect(url_for('login'))

## Get power zone data route
@app.route('/get_powerzone')
def get_powerzone():
    if 'username' in session:
        db = create_connection("myDatabase.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM powerzone")
        zones_data = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(zones_data)

## Update power zone data route
@app.route('/power_zone', methods=['PUT'])
def power_zone():
    if request.method == 'PUT':
        data = request.json
        db = create_connection("myDatabase.db")
        cursor = db.cursor()
        for zone_data in data:
            zoneId = zone_data['zoneId']
            activated = zone_data['activated']
            selectedDevice = zone_data['selectedDevice']
            buzzerStatus = zone_data['buzzerStatus']
            
            cursor.execute("SELECT * FROM powerzone WHERE zoneId=?", (zoneId,))
            existing_zone = cursor.fetchone()
            
            if existing_zone:
                cursor.execute("UPDATE powerzone SET activated=?, selectedDevice=?, buzzerStatus=? WHERE zoneId=?", (activated, selectedDevice, buzzerStatus, zoneId))
            else:
                cursor.execute("INSERT INTO powerzone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, ?, ?, ?)", (zoneId, activated, selectedDevice, buzzerStatus))
                
        db.commit()
        cursor.close()
        db.close()
    return jsonify({'msg': 'done'})

## Advanced route
@app.route('/advanced')
def advanced():
    if 'username' in session:
        username = session['username']
        db = create_connection("myDatabase.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('advanced.html', user=user_data)
    return redirect(url_for('login'))

## General route
@app.route('/general')
def general():
    if 'username' in session:
        username = session['username']
        db = create_connection("myDatabase.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('general.html', user=user_data)
    return redirect(url_for('login'))

## System Test route
## System Test route
@app.route('/system_test')
def system_test():
    if 'username' in session:
        username = session['username']
        db = create_connection("myDatabase.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('system_test.html', user=user_data)
    return redirect(url_for('login'))

## Logout route
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1')

