import time
from flask import Flask, request
import requests
import threading
from tkinter import Tk, Label, Button, Entry, StringVar

app = Flask(__name__)
freeze_time = False
sensor1_endpoint = "http://192.168.175.189:5000"
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
        elapsed_time = time.time() - start_time
        print(format_time(int(elapsed_time * 1000)), end='\r') # Convert seconds to milliseconds
        time.sleep(0.0001)

def countdown_timer(start_time, countdown_length):
    global got_time_remaining
    end_time = start_time + countdown_length
    got_time_remaining = True
    while time.time() < end_time and got_time_remaining:
        remaining_time = end_time - time.time()
        print(format_time(int(remaining_time * 1000)), end='\r')  # Convert seconds to milliseconds
        time.sleep(0.001)
    got_time_remaining = False
    return
def format_time(milliseconds):
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    milliseconds = milliseconds % 1000
    return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

def start_round(timer_length):
    start_time = time.time()
    requests.post(sensor1_endpoint + '/actions', json={'action': 'activate', 'startTime': start_time,'timerLength': timer_length})
    countdown_timer(start_time, timer_length)

def reset():
    requests.post(sensor1_endpoint + '/actions', json={'action': 'reset'})

class Application:
    def __init__(self, master):
        self.master = master
        self.timer_length = StringVar()

        self.label = Label(master, text="Timer Length:")
        self.label.pack()

        self.entry = Entry(master, textvariable=self.timer_length)
        self.entry.pack()

        self.start_button = Button(master, text="Start", command=self.start)
        self.start_button.pack()

        self.reset_button = Button(master, text="Reset", command=self.reset)
        self.reset_button.pack()

    def start(self):
        timer_length = int(self.timer_length.get())
        start_round(timer_length)
    def reset(self):
        reset()
    
if __name__ == '__main__':
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'debug': False}).start()

    root = Tk()
    app = Application(root)
    root.mainloop()