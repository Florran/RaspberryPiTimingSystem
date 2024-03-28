from flask import Flask, request
from gpiozero import MotionSensor
import time
import threading

pir = MotionSensor(4)
app = Flask(__name__)
lock = threading.Lock()
monitoring = False
motion_detected = False
reset_requested = False

@app.route('/handle_request', methods=['GET'])
def handle_request():
    global monitoring
    global motion_detected
    global reset_requested
    global got_time_remaining
    request_data = request.args.get('data')

    with lock:
        if request_data == "activate" and not monitoring:
            monitoring = True
            print("Motion detection activated!")
            threading.Thread(target=monitor_motion).start()
            threading.Thread(target=countdown_timer, args=(60,)).start()
            threading.Thread(target=when_motion_detected).start()
            return 'Motion detection activated!'
        
        elif request_data == "deactivate" and monitoring:
            monitoring = False
            print("Motion detection deactivated!")
            return 'Motion detection deactivated!'
        
        elif request_data == "reset":
            reset()
            reset_requested = True
            return 'Reset requested!'
        
        return 'Invalid command or already in desired state.'

def monitor_motion():
    global motion_detected
    global reset_requested
    global monitoring

    while monitoring:
        if pir.motion_detected:
            with lock:
                print("Motion detected!")
                motion_detected = True
                monitoring = False
        time.sleep(0.01)
    return

def when_motion_detected():
    global motion_detected
    global got_time_remaining
    while got_time_remaining:
        if motion_detected:
            print("Motion detected!")
            break
    return

def format_time(milliseconds):
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    milliseconds = milliseconds % 1000
    return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

def timer():
    start_time = time.time() * 1000
    while motion_detected:
        elapsed_time = int((time.time() * 1000) - start_time)
        print(format_time(elapsed_time), end='\r')
        time.sleep(0.1)
        if reset_requested:
            return

def countdown_timer(seconds):
    global got_time_remaining
    start_time = time.time()
    end_time = start_time + seconds
    got_time_remaining = True
    while time.time() < end_time and not reset_requested:
        remaining_time = end_time - time.time()
        print(format_time(int(remaining_time * 1000)), end='\r')
        time.sleep(0.001)
    got_time_remaining = False
    return


def reset():
    global reset_requested
    global monitoring
    global motion_detected
    global got_time_remaining
    reset_requested = False
    monitoring = False
    motion_detected = False
    got_time_remaining = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
