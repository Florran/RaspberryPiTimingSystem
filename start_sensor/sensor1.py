from flask import Flask, request
from gpiozero import MotionSensor
import time
import threading
import requests

pir = MotionSensor(4)
app = Flask(__name__)
lock = threading.Lock()
monitoring = threading.Event()
controller_endpoint= "http://192.168.68.94:5000"

@app.route('/actions', methods=['POST'])
def handle_request():
    global monitoring
    data = request.get_json()
    request_action = data.get('action')

    with lock:
        if  request_action == "start" and not monitoring:
            monitoring.set()
            print("Motion detection activated!")
            threading.Thread(target=monitor_motion).start()
            return 'Motion detection activated!'
        elif  request_action == "stop" and monitoring:
            monitoring.clear()
            return 'Motion detection deactivated!'
        elif    request_action == "reset":
            reset()
            return 'Reset requested!'
        return 'Invalid command or already in desired state.'

def monitor_motion():
    global monitoring
    while monitoring.is_set():
        if pir.motion_detected:
            with lock:
                print("Motion detected!")
                monitoring.clear()
                post_current_time()

        time.sleep(0.001)
    return

def format_time(milliseconds):
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    milliseconds = milliseconds % 1000
    return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

def post_current_time():
    time_of_motion = time.time()
    requests.post(controller_endpoint + '/start_timer', json={'timeOfMotion': time_of_motion})

def reset():
    global monitoring
    monitoring.clear()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
