from flask import Flask, request
from gpiozero import MotionSensor
import time
import threading
import requests

pir = MotionSensor(4)
app = Flask(__name__)
lock = threading.Lock()
monitoring = threading.Event()
controller_endpoint= "http://192.168.110.182:5000"

@app.route('/start', methods=['POST'])
def start():
    with lock:
        if not monitoring: 
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

def monitor_motion():
    global monitoring
    while monitoring.is_set():
        if pir.motion_detected:
            with lock:
                print("Motion detected!")
                monitoring.clear()
                threading.Thread(target=signal_movment).start()
                time.sleep(1)
        time.sleep(0.001)
    return

def signal_movment():
    requests.post(controller_endpoint + '/reset_system', json={})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
