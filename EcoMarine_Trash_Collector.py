from flask import Flask, Response, request
import RPi.GPIO as GPIO
import cv2
import time

app = Flask(__name__)

ENA = 18    # Left motor enable (PWM)
IN1 = 23    # Left motor direction 1
IN2 = 24    # Left motor direction 2
ENB = 25    # Right motor enable (PWM)
IN3 = 27    # Right motor direction 1
IN4 = 22    # Right motor direction 2

# Conveyor Motor Pin
CONVEYOR_PIN = 17  # Adjust if needed

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
pins = [ENA, IN1, IN2, ENB, IN3, IN4, CONVEYOR_PIN]
for p in pins:
    GPIO.setup(p, GPIO.OUT)

# PWM for both motors
pwmA = GPIO.PWM(ENA, 1000)
pwmB = GPIO.PWM(ENB, 1000)
pwmA.start(0)
pwmB.start(0)

def set_speed(speedA=70, speedB=70):
    pwmA.ChangeDutyCycle(speedA)
    pwmB.ChangeDutyCycle(speedB)

def forward(speed=70):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    set_speed(speed, speed)
    print("Moving Forward")

def left(speed=70):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    set_speed(0, speed)
    print("Turning Left")

def right(speed=70):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    set_speed(speed, 0)
    print("Turning Right")

def stop():
    GPIO.output([IN1, IN2, IN3, IN4], GPIO.LOW)
    set_speed(0, 0)
    print("Stopped")

def conveyor_on():
    GPIO.output(CONVEYOR_PIN, GPIO.HIGH)
    print("Conveyor ON")

def conveyor_off():
    GPIO.output(CONVEYOR_PIN, GPIO.LOW)
    print("Conveyor OFF")


camera = None
for i in [0, 1, 2]:  # try multiple indices automatically
    cam = cv2.VideoCapture(i, cv2.CAP_V4L2)
    if cam.isOpened():
        camera = cam
        print(f"? Using camera index {i}")
        break
    else:
        cam.release()

if camera is None:
    raise RuntimeError("? Cannot open any camera. Check connections.")

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    # Simple HTML page to show the video feed in WebViewer
    return '''
    <html>
      <head>
        <title>EcoMarine Camera Feed</title>
      </head>
      <body style="margin:0; background:black;">
        <img src="/video_feed" width="100%" />
      </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/control')
def control():
    cmd = request.args.get('cmd')
    print(f"Command received: {cmd}")

    if cmd == 'forward':
        forward()
    elif cmd == 'left':
        left()
    elif cmd == 'right':
        right()
    elif cmd == 'stop':
        stop()
    elif cmd == 'conveyor_on':
        conveyor_on()
    elif cmd == 'conveyor_off':
        conveyor_off()

    return "OK"


if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        if camera is not None:
            camera.release()
        pwmA.stop()
        pwmB.stop()
        GPIO.cleanup()
        print("? GPIO and camera cleaned up.")




