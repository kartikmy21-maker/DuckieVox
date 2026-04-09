import webbrowser
import urllib.parse
import pyautogui
import time
import webbrowser
import os

def open_file_by_name(filename):
    try:
        folders = [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads")
        ]

        filename = filename.lower()

        for folder in folders:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if filename in file.lower():
                        path = os.path.join(root, file)
                        os.startfile(path)
                        return f"Opening {file}"

        return "File not found"

    except Exception as e:
        return f"Error: {str(e)}"

import subprocess

def open_application(name):
    apps = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "chrome": "chrome.exe",
        "vscode": "code"
    }

    app = apps.get(name.lower())

    if not app:
        return f"App {name} not found"

    try:
        subprocess.Popen(app)
        return f"Opening {name}"
    except Exception as e:
        return f"Error opening {name}: {str(e)}"
    
def type_text(text):
    import pyautogui
    pyautogui.write(text, interval=0.01)
    return "Typed text"

def press_keys(keys):
    import pyautogui
    pyautogui.hotkey(*keys.split("+"))
    return f"Pressed {keys}"

def post_on_linkedin(content):
    """
    Opens LinkedIn and types a post automatically
    """

    try:
        # 🔥 Step 1: Open LinkedIn
        webbrowser.open("https://www.linkedin.com/feed/")
        time.sleep(5)  # wait for page load

        # 🔥 Step 2: Click post box (adjust if needed)
        pyautogui.moveTo(500, 300, duration=0.5)
        pyautogui.click()

        time.sleep(2)

        # 🔥 Step 3: Type content
        pyautogui.write(content, interval=0.01)

        return "Posted on LinkedIn (typed content)"

    except Exception as e:
        return f"Error posting: {str(e)}"

def create_file(name):
    with open(name, "w") as f:
        pass
    return f"Created file {name}"

def write_file(name, content):
    with open(name, "w") as f:
        f.write(content)
    return f"Written to {name}"

def open_website(url):
    webbrowser.open(url)
    return f"Opening {url}"

def search_google(query):
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    return f"Searching {query}"

def open_first_result():
    time.sleep(2)  # wait for Google page to load

    pyautogui.moveTo(500, 350, duration=0.5)
    pyautogui.click()

    return "Opening first result"