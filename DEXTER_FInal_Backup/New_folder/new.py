from flask import Flask, render_template, request, redirect, url_for
import RPi.GPIO as GPIO

# Setup
GPIO.setmode(GPIO.BCM)
led_pins = {1: 17, 2: 27, 3: 22}  # Define your GPIO pins here
led_states = {1: False, 2: False, 3: False}

for pin in led_pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

app = Flask(__name__)

@app.route('/')
def led():
    return render_template('led.html', led_states=led_states)

@app.route('/control', methods=['POST'])
def control():
    led_id = int(request.form['led'])
    current_state = led_states[led_id]
    new_state = not current_state
    led_states[led_id] = new_state
    GPIO.output(led_pins[led_id], GPIO.HIGH if new_state else GPIO.LOW)
    return redirect(url_for('led'))

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=4000)
    except KeyboardInterrupt:
        GPIO.cleanup()
