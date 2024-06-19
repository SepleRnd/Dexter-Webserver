from flask import Flask, render_template, request, jsonify, session, url_for, redirect
import sqlite3
from sqlite3 import Error
import os
import sys
from main import led_states, toggle_led, cleanup, setup_gpio
from datetime import timedelta
import threading




setup_gpio()


app = Flask(__name__)
app.secret_key = "SEPLe"  ## set secret key for session

db_file = "sepleDB.db"

def create_connection(db_file):
    conn = None
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, db_file)
        conn = sqlite3.connect(db_path)
        return conn
    except Error as e:
        ##print("Error connecting to database:", e)
        return None

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
    
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = create_connection(db_file)
        if db is None:
            return "Failed to connect to database"
        
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user_data = cursor.fetchone()
            cursor.close()
            db.close()
            if user_data:
                session['username'] = username
                return redirect(url_for('device_config'))
            else:
                return render_template('index.html', alert_userpass=True) 
        except Error as e:
            #print("Error executing SQL query:", e)
            return None

    return render_template('index.html')


@app.route('/resetpassword', methods=['GET', 'POST'])
def resetpassword():
    if request.method == 'POST': 
        username = request.form['username']
        password = request.form['password']
        npassword = request.form['newpassword']
        cpassword = request.form['cpassword']
        
        db = create_connection(db_file)
        if db is None:
            return "Failed to connect to database"
        
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            existing_user = cursor.fetchone()
            if existing_user:
                if npassword == cpassword:
                    cursor.execute("UPDATE users SET password=? WHERE username=?", (npassword, username))
                    db.commit()
                    cursor.close()
                    db.close()
                    return render_template('index.html', reset_password=True)
                else:
                    return render_template('reset.html', not_same=True)
            else:
                return render_template('reset.html', wrong_password=True)
        except Error as e:
            #print("Error executing SQL query:", e)
            return "Error executing SQL query"

    return render_template('reset.html')



def restart_server():
    """Restart the Flask application."""
    python = sys.executable
    os.execl(python, python, *sys.argv)
    
def session_clear():
    session.pop('username',None)
    


@app.route('/restart')    
def restart():
      # Restart the Flask application
    session_clear()  # Clear session data
     # Redirect to login page

    threading.Timer(10.0, lambda: restart_server()).start()  # Restart server in 10 second
    return render_template('index.html', restart=True)


@app.route('/terminate', methods=['POST', 'GET'])
def terminate():
    session_clear()
    threading.Timer(1.0, lambda: terminate_server()).start()
    return render_template('index.html', poweroff = True)
    
    



def terminate_server():
    """Terminate the Flask application."""
    os._exit(0)
    



@app.route('/device_config')
def device_config():
    """Device Config route."""
    if 'username' in session:
        username = session['username']
        db = create_connection(db_file)
        if db:
            try:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM users WHERE username=?", (username,))
                user_data = cursor.fetchone()
                cursor.close()
                db.close()
                return render_template('device_config.html', user=user_data)
            except Error as e:
                #print(f"Database query error: {e}")
                return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/get_zone', methods=['GET','PUT'])
def get_zone():
    db = create_connection(db_file)
    if db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM zone")
        zones_data = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(zones_data)
    else:
        return jsonify([])

@app.route('/update_zone', methods=['PUT'])
def update_zone():
    if request.method == 'PUT':
        data = request.json  # Assuming JSON data is sent from the client-side
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            try:
                for zone_data in data:    
                    zoneId = zone_data.get('zoneId')
                    activated = zone_data.get('activated')
                    selectedDevice = zone_data.get('selectedDevice')
                    buzzerStatus = zone_data.get('buzzerStatus')
                    
                    if zoneId:
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
            except Error as e:
                #print(f"Error executing SQL query: {e}")
                return jsonify({'error': str(e)}), 500
        else:
            return "Failed to connect to database"

    return jsonify({'error': 'Invalid request method'}), 405



@app.route('/powerzone_config')
def powerzone_config():
    if 'username' in session:
        username = session['username']
        db = create_connection(db_file)
        if db:
            try:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM users WHERE username=?", (username,))
                user_data = cursor.fetchone()
                cursor.close()
                db.close()
                return render_template('powerzone_config.html', user=user_data)
            except Error as e:
                #print(f"Database query error: {e}")
                return redirect(url_for('login'))
    return redirect(url_for('login'))

## Get power zone data route
@app.route('/get_powerzone', methods=['GET','PUT'])
def get_powerzone():
    if 'username' in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM powerzone")
            zones_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(zones_data)
        else:
            return jsonify([])

## Update power zone data route
@app.route('/power_zone', methods=['PUT'])
def power_zone():
    if request.method == 'PUT':
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            try:    
                for zone_data in data:
                    zoneId = zone_data['zoneId']
                    activated = zone_data['activated']
                    selectedDevice = zone_data['selectedDevice']
                    buzzerStatus = zone_data['buzzerStatus']
                    if zoneId:
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
            except Error as e:
                #print(f"Error executing SQL query: {e}")
                return jsonify({'error': str(e)}), 500
            
        else:
            return "Failed to connect database"
    return jsonify({'error': 'Invalid request method'})


@app.route('/advanced')
def advanced():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('advanced.html', user=user_data)
    return redirect(url_for('login'))


@app.route('/general')
def general():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor2 = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        cursor2.execute("SELECT * FROM general")
        user_data = cursor.fetchone()
        user_data2 = cursor2.fetchall()
        cursor.close()
        db.close()
        return render_template('general.html', user=user_data, user2 = user_data2)
    return redirect(url_for('login'))


@app.route('/general_data', methods=['GET','POST'])
def general_data():
    if request.method == 'POST':
        brand_name =request.form['brandName']
        site_name = request.form['siteName']
        
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM general WHERE ID=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE general SET brand_name=?, site_name=? WHERE ID=1", (brand_name, site_name))
            else:
                cursor.execute("INSERT INTO general (brand_name, site_name) VALUES (?,?)", (brand_name, site_name))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('general'))
            

#@app.route('/system_test', methods=['GET'])
#def system_test():
    #if 'username' in session:
        #username = session['username']
        #db = create_connection("sepleDB.db")
        #cursor = db.cursor()
        #cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        #user_data = cursor.fetchone()
        #cursor.close()
        #db.close()
                
        #led_id = int(request.form['led'])
        #current_state = led_states[led_id]
        #new_state = not current_state
        #led_states[led_id] = new_state
        #GPIO.output(led_pins[led_id], GPIO.HIGH if new_state else GPIO.LOW)
        #print ("changed")
        #return render_template('system_test.html', user=user_data)
    #return redirect(url_for('login'))



@app.route('/system_test')
def system_test():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('system_test.html',user = user_data, led_states=led_states)
    return redirect(url_for('login'))

@app.route('/control', methods=['POST'])
def control():
    if request.method == 'POST':
        led_id = int(request.form['led'])
        toggle_led(led_id)
        return redirect(url_for('system_test'))
    


@app.route('/logs')
def logs():
    if 'username' in session:
        username = session['username']
        
        # Connect to the first database (sepleDB.db)
        db1 = create_connection("sepleDB.db")
        cursor1 = db1.cursor()
        cursor1.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor1.fetchone()
        cursor1.close()
        db1.close()
        
        # Connect to the second database (anotherDB.db)
        db2 = create_connection("dexterpanel2.db")
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM systemLogs")
        logs_data = cursor2.fetchall()
        cursor2.close()
        db2.close()
        
        return render_template('logs.html', user=user_data, logs=logs_data)
    return redirect(url_for('login'))



@app.route('/reports')
def reports():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?",(username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()
        return render_template('reports.html', user=user_data)
    return redirect(url_for('login'))

@app.route('/net_eSim')
def net_eSim():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()
        return render_template('net_eSim.html', user = user_data)
    return redirect(url_for('login')) 

@app.route('/get_eSim')
def get_eSim():
    if 'username' in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM eSim")
            net_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(net_data)
        else:
            return jsonify([])


@app.route('/neteSim_data', methods=['PUT'])
def neteSim_data():
    if request.method == 'PUT':
        data = request.json 
        eSim_activated = data.get('eSim_activated')
        select_network = data.get('select_network')
        id = 1
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * from eSim WHERE ID=1")
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE eSim SET eSim_activated=?, select_network=? WHERE ID=1",(eSim_activated, select_network))
            else:
                cursor.execute("INSERT INTO eSim (eSim_activated, select_network, ID) VALUES (?, ?, ?)",(eSim_activated, select_network, id))
        db.commit()
        cursor.close()
        db.close()
        return ({"done":"data"})
   
    
    
@app.route('/gnss')
def gnss():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()
        return render_template('net_Gnss.html', user = user_data)
    return redirect(url_for('login'))


@app.route('/get_gnss')
def get_gnss():
    if 'username' in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gnss")
            gnss_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(gnss_data)
        else:
            return jsonify([])
        
@app.route('/net_gnss', methods=['PUT'])
def net_gnss():
    if request.method == 'PUT':
        data = request.json
        gnss_activated = data.get('gnss_activated')
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gnss WHERE ID=1")
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE gnss SET gnss_activated=? WHERE ID=1", (gnss_activated,))
            else:
                cursor.execute("INSERT INTO gnss (gnss_activated) VALUES (?)", (gnss_activated,))
        db.commit()
        cursor.close()
        db.close()
        return ({"data": "done"})










@app.route('/lan')
def lan():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor2 = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        cursor2.execute("SELECT * FROM lan")
        user2_data= cursor2.fetchall()
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()
        return render_template('Lan.html', user = user_data, user2 = user2_data)
    return redirect(url_for('login'))

@app.route('/data2_lan', methods=['PUT'])
def data2_lan():
    if request.method == 'PUT':
        data = request.json
        network_led_sts = data.get('network_led_sts')
        wireless_lan = data.get('wireless_lan')
        ip_module = data.get('ip_module')
        static_or_dynamic = data.get('static_or_dynamic')
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM lan WHERE ID=1")
            
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE lan SET network_led_sts=?, wireless_lan=?,ip_module=?, static_or_dynamic=? WHERE ID=1", (network_led_sts,wireless_lan,ip_module, static_or_dynamic))
            else:
                cursor.execute("INSERT INTO lan (network_led_sts,wireless_lan,ip_module,static_or_dynamic) VALUES (?,?,?,?)", (network_led_sts ,wireless_lan,ip_module,static_or_dynamic))
        db.commit()
        cursor.close()
        db.close()
        return jsonify([])
    
@app.route('/get_data2lan')
def get_data2lan():
    if 'username' in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT network_led_sts,wireless_lan,ip_module,static_or_dynamic  FROM lan")
            get_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(get_data)




@app.route('/data_lan', methods =['POST'])
def data_lan():
    if request.method == 'POST':
        set_ip_address = request.form['set_ip_address']
        set_port_no = request.form['set_port_no']
        subnet_mask = request.form['subnet_mask']
        gate_way = request.form['gate_way']
        dns_setups = request.form['dns_setups']
        apn_settings = request.form['apn_settings']
        
        
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM lan WHERE ID=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE lan SET set_ip_address=?,set_port_no=?,subnet_mask=?,gate_way=?, dns_setups=?, apn_settings =? WHERE ID=1",(set_ip_address,set_port_no,subnet_mask,gate_way,dns_setups,apn_settings))
            else:
                cursor.execute("INSERT INTO lan (set_ip_address, set_port_no, subnet_mask, gate_way, dns_setups, apn_settings) VALUES(?,?,?,?,?,?)",(set_ip_address,set_port_no,subnet_mask,gate_way,dns_setups,apn_settings))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('lan'))
    # return ({"data":"send"})

@app.route('/net_gsm')
def net_gsm():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()
        return render_template('net_Gsm.html', user = user_data)
    return redirect(url_for('login'))


@app.route('/get_gsm')
def get_gsm():
    if 'username' in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gsm")
            gsm_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(gsm_data)
        else:
            return jsonify({"data": "error"})
            


@app.route('/netdata_gsm', methods=['PUT'])
def netdata_gsm():
    if request.method == 'PUT':
        data = request.json
        gsm_activated = data.get('gsm_activated')
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gsm WHERE ID=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE gsm SET gsm_activated=? WHERE ID=1", (gsm_activated,))
            else:
                cursor.execute("INSERT INTO gsm (gsm_activated) VALUES (?)", (gsm_activated,))
        db.commit()
        cursor.close()
        db.close()
        return ({"data":"send"})
    
@app.route('/come_soon')
def come_soon():
    return render_template('coming_soon.html')




@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True, host="192.168.0.83",port='5000')
