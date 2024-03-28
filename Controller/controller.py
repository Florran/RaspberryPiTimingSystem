import time
from flask import Flask, request
import requests
import threading

app = Flask(__name__)
freeze_time = False
lock = threading.Lock()

@app.route('/catch_time', methods=['POST'])
def catch_time():
    with lock:
        time_of_motion = request.json.get('timeOfMotion')
        time_of_motion = float(time_of_motion)
        if time_of_motion is not None:
            threading.Thread(target=timer, args=(time_of_motion,)).start()
            return 'Time received and stopwatch started', 200
        else:
            return 'timeOfMotion is of type None', 400

def timer(start_time):
    global freeze_time
    freeze_time = False
    while not freeze_time:
        elapsed_time = time.perf_counter() - start_time
        print(format_time(int(elapsed_time * 1000)), end='\r') # Convert seconds to milliseconds
        time.sleep(0.0001)

def format_time(milliseconds):
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    milliseconds = milliseconds % 1000
    return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

if __name__ == '__main__':
    print(time.perf_counter())
    app.run(host='0.0.0.0', debug=True)
