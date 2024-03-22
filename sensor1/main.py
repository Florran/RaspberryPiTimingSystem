from flask import Flask, request
from gpiozero import MotionSensor
import time

#http://localhost:5000/handle_request?data=example_data
#url for test

pir = MotionSensor(4)
app = Flask(__name__)
monitoring = False

@app.route('/handle_request', methods=['GET'])
def handle_request():
    global monitoring
    request_data = request.args.get('data')

    if request_data == "activate" and not monitoring:
        monitoring = True
        print("Motion detection activated!")
        monitor_motion()
        return 'Motion detection activated!'
    
    elif request_data == "deactivate" and monitoring:
        monitoring = False
        print("Motion detection deactivated!")
        return 'Motion detection deactivated!'
    
    return 'Invalid command or already in desired state.'

def monitor_motion():
    while monitoring:
        if pir.motion_detected:
            print("Motion detected!")
            timer()

def format_time(milliseconds):
    hours = milliseconds // 3600000
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    milliseconds = milliseconds % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

def timer():
    start_time = time.time() * 1000
    while True:
        elapsed_time = int((time.time() * 1000) - start_time)
        print(format_time(elapsed_time), end='\r')
        time.sleep(0.1)

if __name__ == '__main__':
    app.run(debug=True)
