import webbrowser
import urllib.parse
import pyautogui
import time
import webbrowser

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