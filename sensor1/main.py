from flask import Flask, request
from gpiozero import MotionSensor
import time
import threading

pir = MotionSensor(4)
app = Flask(__name__)
monitoring = False
motion_detected = False

@app.route('/handle_request', methods=['GET'])
def handle_request():
    global monitoring
    global motion_detected
    request_data = request.args.get('data')

    if request_data == "activate" and not monitoring:
        monitoring = True
        print("Motion detection activated!")
        threading.Thread(target=monitor_motion).start()
        return 'Motion detection activated!'
    
    elif request_data == "deactivate" and monitoring:
        monitoring = False
        print("Motion detection deactivated!")
        return 'Motion detection deactivated!'
    
    return 'Invalid command or already in desired state.'

def monitor_motion():
    global motion_detected
    while monitoring:
        if pir.motion_detected:
            print("Motion detected!")
            motion_detected = True
            timer()
            motion_detected = False
        time.sleep(0.1)

def format_time(milliseconds):
    hours = milliseconds // 3600000
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    milliseconds = milliseconds % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

def timer():
    start_time = time.time() * 1000
    while motion_detected:
        elapsed_time = int((time.time() * 1000) - start_time)
        print(format_time(elapsed_time), end='\r')
        time.sleep(0.1)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
