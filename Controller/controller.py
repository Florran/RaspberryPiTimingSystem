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
freeze_time = threading.Event()
start_motion_detected = threading.Event()
stop_motion_detected = threading.Event()
start_sensor_url = "http://192.168.110.189:5000"
stop_sensor_url = "http://192.168.110.211:5000"
lock = threading.Lock()
session = Session()
retries = Retry(total=2, backoff_factor=0.1, status_forcelist=[ 500, 502, 503, 504 ])
session.mount('http://', HTTPAdapter(max_retries=retries))

@flask_app.route('/start_timer', methods=['POST'])
def start_timer():
    global start_motion_detected
    with lock:
        time_of_motion = time.time()
        start_motion_detected.set()
        threading.Thread(target=timer, args=(time_of_motion,)).start()
        return 'Stopwatch started', 200


@flask_app.route('/stop_timer', methods=['POST'])
def stop_timer():
    global stop_motion_detected
    with lock:
        stop_motion_detected.set()
        return 'Time received and stopwatch stopped', 200


def timer(start_time):
    global stop_motion_detected
    while not stop_motion_detected.is_set():
        elapsed_time = time.time() - start_time
        time_formatted = format_time(int(elapsed_time * 1000)) # Convert seconds to milliseconds
        gui.time_label.configure(text=time_formatted)
        time.sleep(0.001)
    stop_motion_detected.clear()

def countdown(start_time, countdown_length):
    end_time = start_time + countdown_length
    while time.time() < end_time:
        if start_motion_detected.is_set():
            print("Motion detected, stopping countdown.")
            break
        remaining_time = end_time - time.time()
        remaining_time_formatted = format_time(int(remaining_time * 1000))
        gui.time_label.configure(text=remaining_time_formatted)
        time.sleep(0.001)
    start_motion_detected.clear()
    gui.time_label.configure(text="")
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
        session.post(start_sensor_url + '/start',
        json={}, 
        timeout=2.5)
        start_motion_detected.clear()
        stop_motion_detected.clear()
        threading.Thread(target=countdown, args=(start_time, timer_length)).start()
    except requests.exceptions.RequestException as e:
        error_message = f"{type(e).__name__}: {str(e)}"
        if gui.error_window is None or not gui.error_window.winfo_exists():
            gui.error_window = error_window(error_message, gui)
        else:
            gui.error_window.focus()
    return

def start_stopping_of_round():
    try:
        session.post(stop_sensor_url + '/start',
        json={}, 
        timeout=2.5)
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if gui.error_window is None or not gui.error_window.winfo_exists():
            gui.error_window = error_window(error_message, gui)
        else:
            gui.error_window.focus()

@flask_app.route('/reset_system', methods=['POST'])
def reset_system():
    try:
        with lock:
            start_motion_detected.set()
            stop_motion_detected.set()
            session.post(start_sensor_url + '/stop',
            json={}, 
            timeout=2.5)
            session.post(stop_sensor_url + '/stop',
            json={}, 
            timeout=2.5)
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if gui.winfo_exists():
            if gui.error_window is None or not gui.error_window.winfo_exists():
                gui.error_window = error_window(error_message, gui)
            else:
                gui.error_window.focus()

class main_gui(customtkinter.CTk):
    def __init__(self, flask_process):
        super().__init__()
        self.started = False

        self.error_window = None
        self.flask_process = flask_process

        #self.attributes("-fullscreen", True)

        # Start the Flask app on a separate daemon thread
        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()

        self.geometry("600x500")
        self.title("Controller for timing system")

        self.grid_rowconfigure((0, 6), weight=2)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=1)
        
        self.header = customtkinter.CTkLabel(self, text="Timing System", font=("Arial", 24))
        self.header.grid(row=0, column=2, padx=20, pady=10, sticky="ews", columnspan="2")

        self.time_entry = customtkinter.CTkEntry(self, placeholder_text="Countdown Time", width=810, justify="center")
        self.time_entry.grid(row=2, column=2, padx=20, pady=10, sticky="ns", columnspan="2")

        if not self.started:
            self.start_button = customtkinter.CTkButton(self, text="Start", width=400, height=100, command=self.start, font=("Arial", 24), fg_color="#73f09b", hover_color="#4b9d65",text_color="black")
        else:
            self.start_button = customtkinter.CTkButton(self, text="Start Exit Sensor", width=400, height=100, command=self.start_stop_sensor, font=("Arial", 24), fg_color="#73f09b", text_color="black")

        self.start_button.grid(row=3, column=2, padx=5, pady=10, sticky="nse", rowspan="2")

        self.reset_button = customtkinter.CTkButton(self, text="Stop", width=200, height=100, command=self.reset, font=("Arial", 24), fg_color="#f07381", hover_color="#893c44",text_color="black")
        self.reset_button.grid(row=3, column=3, padx=5, pady=10, sticky="nsw", rowspan="2")

        self.zero_button = customtkinter.CTkButton(self, text="Reset", width=190, height=100, command=self.set_time_zero, font=("Arial", 24), fg_color="#f1f76d", hover_color="#c5cd24",text_color="black")
        self.zero_button.grid(row=3, column=3, padx=(210, 0), pady=10, sticky="nsw", rowspan="2")

        self.time_label = customtkinter.CTkLabel(self, text="00:00.000", font=("Arial", 90), anchor="center")
        self.time_label.grid(row=1, column=2, padx=0, pady=10, sticky="nsew", columnspan="2")
        
        self.author_label = customtkinter.CTkLabel(self, text="Made by Anton", font=("Arial", 12))
        self.author_label.grid(row=6, column=2, padx=20, pady=10, sticky="n", columnspan="2")

    def start(self):
        try:
            timer_length = int(self.time_entry.get())
            threading.Thread(target=start_round, args=(timer_length,)).start()
            self.started = True
        except ValueError:
            if self.error_window is None or not self.error_window.winfo_exists():
                self.error_window = error_window("OBS måste vara tid i sekunder!", self)
            else:
                self.error_window.focus()
    def start_stop_sensor(self):
        try:
            start_stopping_of_round()
            self.started = True
        except ValueError:
            if self.error_window is None or not self.error_window.winfo_exists():
                self.error_window = error_window("Något gick fel!", self)
            else:
                self.error_window.focus()
    def reset(self):
        threading.Thread(target=reset_system()).start()
        return
    def set_time_zero(self):
        self.time_label.configure(text="00:00.000")
            
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
    flask_app.run(host='0.0.0.0', debug=False, use_reloader=False)

if __name__ == '__main__':
    flask_process = Process(target=run_flask)
    flask_process.start()
    global gui
    gui = main_gui(flask_process)
    gui.mainloop()