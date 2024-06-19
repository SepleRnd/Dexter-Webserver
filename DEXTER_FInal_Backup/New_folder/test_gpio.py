import RPi.GPIO as GPIO
import time

# Use BCM GPIO numbering
GPIO.setmode(GPIO.BCM)

# Set up the GPIO pin (e.g., GPIO 17) for output
LED_PIN = 17
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    while True:
        # Turn the LED on
        GPIO.output(LED_PIN, GPIO.HIGH)
        print("LED ON")
        # Wait for 5 seconds
        time.sleep(5)

        # Turn the LED off
        GPIO.output(LED_PIN, GPIO.LOW)
        print("LED OFF")
        # Wait for 5 seconds
        time.sleep(5)

except KeyboardInterrupt:
    # Clean up GPIO settings before exiting
    GPIO.cleanup()
    print("Exiting and cleaning up GPIO")
