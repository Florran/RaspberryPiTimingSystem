import time
from flask import Flask, request
import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import threading
import customtkinter
from multiprocessing import Process

flask_app = Flask(__name__)
freeze_time = False
sensor1_endpoint = "http://192.168.175.189:5000"
lock = threading.Lock()
session = Session()
retries = Retry(total=2, backoff_factor=0.1, status_forcelist=[ 500, 502, 503, 504 ])
session.mount('http://', HTTPAdapter(max_retries=retries))

@flask_app.route('/catch_time', methods=['POST'])
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
    global gui
    start_time = time.time()
    try:
        session.post(sensor1_endpoint + '/actions',
        json={'action': 'activate', 'startTime': start_time,'timerLength': timer_length}, 
        timeout=2.5)

        countdown_timer(start_time, timer_length)
    except requests.exceptions.RequestException as e:
        error_message = f"{type(e).__name__}: {str(e)}"
        if gui.error_window is None or not gui.error_window.winfo_exists():
            gui.error_window = error_window(error_message, gui)
        else:
            gui.error_window.focus()

def reset_sensors(from_cleanup=False):
    try:
        requests.post(sensor1_endpoint + '/actions',
        json={'action': 'reset'},
        timeout=0.5)
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if not from_cleanup and gui.winfo_exists():
            if gui.error_window is None or not gui.error_window.winfo_exists():
                gui.error_window = error_window(error_message, gui)
            else:
                gui.error_window.focus()

class main_gui(customtkinter.CTk):
    def __init__(self, flask_process):
        super().__init__()
        self.error_window = None
        self.flask_process = flask_process

        self.bind('<Destroy>', self.cleanup)

        self.geometry("600x500")
        self.title("Main")
        self.timer_length = customtkinter.StringVar()

        self.grid_rowconfigure((0, 3), weight=2)
        self.grid_columnconfigure((0, 3), weight=1)

        self.entry = customtkinter.CTkEntry(self, textvariable=self.timer_length)
        self.entry.grid(row=0, column=2, padx=20, pady=10, sticky="ew")

        self.button = customtkinter.CTkButton(self, text="Start", width=100, height=25, command=self.start)
        self.button.grid(row=1, column=2, padx=20, pady=10, sticky="nsew")

        self.button = customtkinter.CTkButton(self, text="Reset", width=100, height=25, command=self.reset)
        self.button.grid(row=2, column=2, padx=20, pady=10, sticky="nsew")

    def start(self):
        try:
            timer_length = int(self.timer_length.get())
            start_round(timer_length)
        except ValueError:
            if self.error_window is None or not self.error_window.winfo_exists():
                self.error_window = error_window("OBS måste vara tid i sekunder!", self)
            else:
                self.error_window.focus()

    def reset(self):
        reset_sensors()

    def cleanup(self, event=None):
        reset_sensors(from_cleanup=True)
        self.flask_process.terminate()

class error_window(customtkinter.CTkToplevel):
    def __init__(self, error_message, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.label = customtkinter.CTkLabel(self, text=error_message)
        self.label.pack(padx=20, pady=20)

        # Calculate window size based on string length
        window_width = 200 + len(error_message) * 6
        window_height = 100
        self.geometry(f"{window_width}x{window_height}")
        self.title("Error")

        self.lift(master)
        self.focus_force()
        self.grab_set()

def run_flask():
        flask_app.run(host='0.0.0.0', debug=False)

if __name__ == '__main__':
    flask_process = Process(target=run_flask)
    flask_process.start()
    global gui
    gui = main_gui(flask_process)
    gui.mainloop()