import time
from flask import Flask, request
import requests
import threading

app = Flask(__name__)
freeze_time = False
lock = threading.Lock()

@app.route('/catch_time', methods=['POST'])
def CatchTime():
    timeOfMotion = request.json.get('timeOfMotion')
    if timeOfMotion is not None:
        timeOfMotion = float(timeOfMotion)
        threading.Thread(target=Timer, args=(timeOfMotion,)).start()
        return 'Time received and stopwatch started', 200
    else:
        return 'timeOfMotion is of type None', 400

def Timer(startTime):
    global freezeTime
    freezeTime = False
    while not freezeTime:
        elapsedTime = time.perf_counter() - startTime
        print(FormatTime(int(elapsedTime * 1000)), end='\r') # Convert seconds to milliseconds
        time.sleep(0.0001)

def FormatTime(milliseconds):
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    milliseconds = milliseconds % 1000
    return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

if __name__ == '__main__':
    print(time.perf_counter())
    app.run(host='0.0.0.0', debug=True)