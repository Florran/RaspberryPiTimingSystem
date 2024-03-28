from flask import Flask, request
from gpiozero import MotionSensor
import time
import threading
import requests

pir = MotionSensor(4)
app = Flask(__name__)
lock = threading.Lock()
got_time_remaining = False
monitoring = False
motion_detected = False
reset_requested = False
controller_endpoint= "http://192.168.175.96"

@app.route('/actions', methods=['POST'])
def handle_request():
    global monitoring
    global motion_detected
    global got_time_remaining
    request_action = request.args.get('action')

    with lock:
        if  request_action == "activate" and not monitoring:
            monitoring = True
            print("Motion detection activated!")
            threading.Thread(target=countdown_timer, args=(60,)).start()
            threading.Thread(target=monitor_motion).start()
            return 'Motion detection activated!'
        
        elif    request_action == "reset":
            global reset_requested
            reset()
            return 'Reset requested!'
        return 'Invalid command or already in desired state.'

def monitor_motion():
    global motion_detected
    global monitoring

    while monitoring and got_time_remaining:
        if pir.motion_detected:
            with lock:
                print("Motion detected!")
                motion_detected = True
                monitoring = False
                send_time_of_motion()

        time.sleep(0.001)
    return

def format_time(milliseconds):
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    milliseconds = milliseconds % 1000
    return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

def countdown_timer(start_time, countdown_length):
    global got_time_remaining
    end_time = start_time + countdown_length
    got_time_remaining = True
    while time.perf_counter() < end_time and got_time_remaining:
        remaining_time = end_time - time.perf_counter()
        print(format_time(int(remaining_time * 1000)), end='\r') #Convert seconds to milliseconds
        time.sleep(0.0001)
    got_time_remaining = False
    return

def send_time_of_motion():
    time_of_motion = time.time()
    requests.post(controller_endpoint + '/catch_time', json={'timeOfMotion': time_of_motion})


def reset():
    global monitoring
    global motion_detected
    global got_time_remaining
    monitoring = False
    motion_detected = False
    got_time_remaining = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
