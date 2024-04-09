from flask import Flask, request
from gpiozero import MotionSensor
import time
import threading
import requests

pir = MotionSensor(4)
app = Flask(__name__)
lock = threading.Lock()
monitoring = threading.Event()
controller_endpoint= "http://192.168.68.90:5000"

@app.route('/start', methods=['POST'])
def start():
    with lock:
        if not monitoring.is_set():
            monitoring.set()
            print("Motion detection activated!")
            threading.Thread(target=monitor_motion).start()
            return 'Motion detection activated!'
        return 'Invalid command or already in desired state.'
    
@app.route('/stop', methods=['POST'])
def stop():
    with lock:
        if  monitoring:
            monitoring.clear()
            return 'Motion detection deactivated!'
        return 'Invalid command or already in desired state.'

@app.route('/reset', methods=['POST'])
def reset():
    with lock:
        monitoring.clear()
        time.sleep(1)
        return 'Reset requested!'

def monitor_motion():
    global monitoring
    monitoring.wait()
    while monitoring.is_set():
        if pir.motion_detected:
            with lock:
                print("Motion detected!")
                monitoring.clear()
                post_current_time()
        time.sleep(0.001)
    return

def post_current_time():
    time_of_motion = time.time()
    requests.post(controller_endpoint + '/start_timer', json={'timeOfMotion': time_of_motion})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
