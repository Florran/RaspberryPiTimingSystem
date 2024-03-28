from flask import Flask, request
from gpiozero import MotionSensor
import time
import threading
import requests

Pir = MotionSensor(4)
App = Flask(__name__)
Lock = threading.Lock()
GotTimeRemaining = False
Monitoring = False
MotionDetected = False
ResetRequested = False
ControllerEndpoint = "192.168.175.96:5000"

@App.route('/HandleRequest', methods=['GET'])
def HandleRequest():
    global Monitoring
    global MotionDetected
    global GotTimeRemaining
    RequestData = request.args.get('data')

    with Lock:
        if RequestData == "activate" and not Monitoring:
            Monitoring = True
            print("Motion detection activated!")
            threading.Thread(target=CountdownTimer, args=(60,)).start()
            threading.Thread(target=MonitorMotion).start()
            return 'Motion detection activated!'
        
        elif RequestData == "reset":
            global ResetRequested
            Reset()
            return 'Reset requested!'
        return 'Invalid command or already in desired state.'

def MonitorMotion():
    global MotionDetected
    global Monitoring

    while Monitoring and GotTimeRemaining:
        if Pir.motion_detected:
            with Lock:
                print("Motion detected!")
                MotionDetected = True
                Monitoring = False
                SendTimeOfMotion()

        time.sleep(0.001)
    return

def FormatTime(milliseconds):
    Minutes = (milliseconds % 3600000) // 60000
    Seconds = (milliseconds % 60000) // 1000
    Milliseconds = milliseconds % 1000
    return f"{Minutes:02}:{Seconds:02}.{Milliseconds:03}"

def CountdownTimer(seconds):
    global GotTimeRemaining
    StartTime = time.perf_counter()
    EndTime = StartTime + seconds
    GotTimeRemaining = True
    while time.perf_counter() < EndTime and GotTimeRemaining:
        RemainingTime = EndTime - time.perf_counter()
        print(FormatTime(int(RemainingTime * 1000)), end='\r') #Convert seconds to milliseconds
        time.sleep(0.0001)
    GotTimeRemaining = False
    return

def SendTimeOfMotion():
    TimeOfMotion = time.perf_counter()
    requests.post(ControllerEndpoint + '/catch_time', json={'timeOfMotion': TimeOfMotion})

def Reset():
    global Monitoring
    global MotionDetected
    global GotTimeRemaining
    Monitoring = False
    MotionDetected = False
    GotTimeRemaining = False

if __name__ == '__main__':
    App.run(host='0.0.0.0', debug=True)