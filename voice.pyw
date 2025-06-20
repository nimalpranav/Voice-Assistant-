# Voice Assistant with Secret Word Unlock and Website/App Locking (Thread-Safe Version)
import speech_recognition as sr
import pyautogui
import keyboard
import os
import pyttsx3
import threading
import psutil
import ctypes
import webbrowser
from PIL import ImageGrab
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import datetime
import speedtest

SECRET_WORD = "hello"
APP_PASSWORD = "any"
LOCKED_APPS = set()
LOCKED_WEBSITES = set()

APP_ALIASES = {
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "downloads": os.path.expanduser("~\\Downloads"),
    "documents": os.path.expanduser("~\\Documents")
}

WEBSITE_ALIASES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "chatgpt": "https://chat.openai.com",
    "github": "https://github.com"
}

engine = pyttsx3.init()
engine.setProperty('rate', 180)
last_action = None
active = False

class PasswordDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Password")
        self.setFixedSize(300, 100)
        layout = QtWidgets.QVBoxLayout()
        self.label = QtWidgets.QLabel("Type the password to unlock")
        layout.addWidget(self.label)
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.password_input)
        self.ok_button = QtWidgets.QPushButton("Unlock")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def get_password(self):
        return self.password_input.text()

class SystemTrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        menu = QtWidgets.QMenu(parent)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(QtWidgets.qApp.quit)
        self.setContextMenu(menu)

def speak(text):
    engine.say(text)
    engine.runAndWait()

def take_screenshot():
    screenshot = ImageGrab.grab()
    path = os.path.join(os.path.expanduser("~"), "screenshot.png")
    screenshot.save(path)
    speak("Screenshot taken")

def system_control(command):
    if command == "lock system":
        ctypes.windll.user32.LockWorkStation()
    elif command == "shutdown now":
        os.system("shutdown /s /t 1")
    elif command == "restart system":
        os.system("shutdown /r /t 1")

def open_item(name):
    path = APP_ALIASES.get(name.lower())
    if path:
        os.startfile(path)
        speak(f"Opening {name}")
    else:
        speak("I don't know that app or folder.")

def open_website(name):
    if name.lower() in LOCKED_WEBSITES:
        speak(f"Access to {name} is locked")
        return
    url = WEBSITE_ALIASES.get(name.lower())
    if url:
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
        speak(f"Opening {name}")
    else:
        speak("I don't know that website.")

def lock_app(name):
    name = name.lower()
    for proc in psutil.process_iter():
        try:
            if name in proc.name().lower():
                proc.kill()
        except:
            continue
    LOCKED_APPS.add(name)
    speak(f"Locked {name}")

def unlock_app(name):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    dialog = PasswordDialog()
    if dialog.exec_():
        if dialog.get_password() == APP_PASSWORD:
            LOCKED_APPS.discard(name.lower())
            speak(f"Unlocked {name}")
        else:
            speak("Incorrect password")

def lock_website(name):
    LOCKED_WEBSITES.add(name.lower())
    speak(f"Locked website {name}")

def unlock_website(name):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    dialog = PasswordDialog()
    if dialog.exec_():
        if dialog.get_password() == APP_PASSWORD:
            LOCKED_WEBSITES.discard(name.lower())
            speak(f"Unlocked website {name}")
        else:
            speak("Incorrect password")

def repeat_last():
    global last_action
    if last_action:
        last_action()
        speak("Repeated last command")
    else:
        speak("No recent command to repeat")

def app_blocker():
    while True:
        for proc in psutil.process_iter():
            try:
                for locked in LOCKED_APPS:
                    if locked in proc.name().lower():
                        proc.kill()
            except:
                continue

def process_command(cmd):
    global last_action
    if cmd.startswith("press"):
        keys = cmd.replace("press", "").strip().replace("plus", "+")
        keyboard.press_and_release(keys)
        last_action = lambda: keyboard.press_and_release(keys)
    elif cmd.startswith("type"):
        text = cmd.replace("type", "").strip()
        keyboard.write(text)
        last_action = lambda: keyboard.write(text)
    elif "scroll up" in cmd:
        pyautogui.scroll(500)
    elif "scroll down" in cmd:
        pyautogui.scroll(-500)
    elif cmd == "take screenshot":
        take_screenshot()
    elif cmd == "repeat that":
        repeat_last()
    elif cmd in ["lock system", "shutdown now", "restart system"]:
        system_control(cmd)
    elif cmd.startswith("open"):
        name = cmd.replace("open", "").strip()
        if name in WEBSITE_ALIASES:
            open_website(name)
        else:
            open_item(name)
    elif cmd.startswith("lock app"):
        name = cmd.replace("lock app", "").strip()
        lock_app(name)
    elif cmd.startswith("unlock app"):
        name = cmd.replace("unlock app", "").strip()
        unlock_app(name)
    elif cmd.startswith("lock website"):
        name = cmd.replace("lock website", "").strip()
        lock_website(name)
    elif cmd.startswith("unlock website"):
        name = cmd.replace("unlock website", "").strip()
        unlock_website(name)
    elif cmd == "switch window":
        keyboard.press_and_release("alt+tab")
    elif cmd == "show battery":
        battery = psutil.sensors_battery()
        if battery:
            speak(f"Battery level is {battery.percent} percent")
    elif cmd in ["pause music", "play music"]:
        keyboard.press_and_release("play/pause media")
    elif cmd == "what time is it":
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"It's {now}")
    elif cmd == "what day is it":
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        speak(f"Today is {today}")
    elif cmd.startswith("search for"):
        query = cmd.replace("search for", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        speak(f"Searching for {query}")
    elif cmd.startswith("create folder"):
        folder_name = cmd.replace("create folder", "").strip()
        path = os.path.join(os.path.expanduser("~/Desktop"), folder_name)
        try:
            os.makedirs(path, exist_ok=True)
            speak(f"Folder {folder_name} created")
        except:
            speak("Couldn't create the folder")
    elif cmd == "check internet speed":
        st = speedtest.Speedtest()
        down = st.download() / 1_000_000
        up = st.upload() / 1_000_000
        speak(f"Download is {int(down)} Mbps. Upload is {int(up)} Mbps.")
    elif "move mouse" in cmd:
        x, y = pyautogui.position()
        if "left" in cmd:
            pyautogui.moveTo(x - 100, y)
        elif "right" in cmd:
            pyautogui.moveTo(x + 100, y)
        elif "up" in cmd:
            pyautogui.moveTo(x, y - 100)
        elif "down" in cmd:
            pyautogui.moveTo(x, y + 100)
    elif cmd == "click":
        pyautogui.click()
    elif cmd == "double click":
        pyautogui.doubleClick()
    elif cmd == "right click":
        pyautogui.rightClick()
    elif cmd.startswith("open folder"):
        folder = cmd.replace("open folder", "").strip()
        folder_path = os.path.join(os.path.expanduser("~/Desktop"), folder)
        if os.path.exists(folder_path):
            os.startfile(folder_path)
            speak(f"Opening {folder}")
        else:
            speak("Folder not found")

def listen():
    global active
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=10)
            cmd = recognizer.recognize_google(audio).lower()
            print("You said:", cmd)
            if not active:
                if SECRET_WORD in cmd:
                    active = True
                    speak("You can now speak")
            else:
                threading.Thread(target=process_command, args=(cmd,), daemon=True).start()
        except:
            continue

def monitor_stop():
    keyboard.wait('ctrl+p')
    speak("Goodbye")
    os._exit(0)

def start_assistant():
    threading.Thread(target=listen, daemon=True).start()
    threading.Thread(target=monitor_stop, daemon=True).start()
    threading.Thread(target=app_blocker, daemon=True).start()

def start_tray():
    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    trayIcon = SystemTrayApp(QtGui.QIcon("icon.png"), w)
    trayIcon.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    threading.Thread(target=start_assistant, daemon=True).start()
    start_tray()