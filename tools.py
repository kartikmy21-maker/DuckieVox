import webbrowser
import urllib.parse
import pyautogui
import time
import os
import subprocess

# Global flag to track the latest launched app so type_text can securely grab focus
last_opened_app_title = ""
last_search_query = ""

# 🔥 OPEN FILE (SMART SEARCH)
def open_file_by_name(name):
    global last_opened_app_title
    folders = [
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Downloads")
    ]

    name = name.lower()

    for folder in folders:
        for root, dirs, files in os.walk(folder):
            # Check folders first
            for d in dirs:
                if name in d.lower():
                    last_opened_app_title = name
                    os.startfile(os.path.join(root, d))
                    return f"Opening folder {d}"
            # Check files
            for f in files:
                if name in f.lower():
                    last_opened_app_title = name
                    os.startfile(os.path.join(root, f))
                    return f"Opening {f}"

    return "File or folder not found"


# 🔥 OPEN APPLICATION (MORE RELIABLE)
def open_application(name):
    global last_opened_app_title
    name = name.lower().strip()
    last_opened_app_title = name

    websites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "facebook": "https://www.facebook.com"
    }
    if name in websites:
        import webbrowser
        webbrowser.open(websites[name])
        return f"Opening {name}"

    import os

    # 🔥 UNIVERSAL START MENU SEARCH (OPENS ALMOST ANY INSTALLED DESKTOP APP)
    try:
        paths = [
            os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), r'Microsoft\Windows\Start Menu\Programs'),
            os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
        ]
        for p in paths:
            if os.path.exists(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        if name.lower() in f.lower() and f.lower().endswith(".lnk"):
                            # Avoid accidental uninstallation executions
                            if "uninstall" not in f.lower() and "setup" not in f.lower():
                                os.startfile(os.path.join(root, f))
                                return f"Opening {f[:-4]}"
    except Exception:
        pass

    # 🔥 DIRECT APPDATA SHORTCUTS FOR TRICKY APPS
    import os
    appdata_local = os.path.expanduser("~\\AppData\\Local")
    appdata_roaming = os.path.expanduser("~\\AppData\\Roaming")
    
    app_shortcuts = {
        "discord": f'"{os.path.join(appdata_local, "Discord", "Update.exe")}" --processStart Discord.exe',
        "zoom": f'"{os.path.join(appdata_roaming, "Zoom", "bin", "Zoom.exe")}"',
        "spotify": f'"{os.path.join(appdata_roaming, "Spotify", "Spotify.exe")}"',
        "slack": f'"{os.path.join(appdata_local, "slack", "slack.exe")}"',
        "whatsapp": "explorer.exe shell:appsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    }
    if name in app_shortcuts:
        os.system(f"start \"\" {app_shortcuts[name]}")
        return f"Opening {name}"

    try:
        subprocess.Popen(name)
        return f"Opening {name}"
    except:
        pass

    try:
        subprocess.Popen(f"{name}.exe")
        return f"Opening {name}"
    except:
        pass

    # 🔥 Try Windows "start" command (VERY IMPORTANT)
    try:
        os.system(f"start {name}")
        return f"Opening {name}"
    except:
        pass

    return None


# 🔥 CLOSE APPLICATION (POLITE)
def close_application(name):
    import pygetwindow as gw
    name = name.lower().strip()
    closed_any = False
    try:
        for w in gw.getAllWindows():
            title = w.title.lower()
            if name in title and title.strip() != "":
                # Ignore loose browser tabs to prevent closing the AI chat
                if title == name or title.endswith(name) or title.endswith(f"- {name}"):
                    w.close()
                    closed_any = True
    except:
        pass
    if closed_any:
        return f"Closed {name}"
    return f"Could not find running application: {name}"

# 🔥 FORCE CLOSE APPLICATION
def force_close_application(name):
    import os
    name = name.lower().strip()
    if not name.endswith(".exe"):
        exe_name = name + ".exe"
    else:
        exe_name = name
    
    exit_code = os.system(f"taskkill /IM {exe_name} /F")
    if exit_code == 0:
        return f"Forcefully closed {name}"
    return f"Failed to forcefully close {name}. It may not be running."


# 🔥 TYPE TEXT (MORE STABLE)
def type_text(text):
    global last_opened_app_title
    import pyautogui
    import time
    try:
        import pygetwindow as gw
    except ImportError:
        gw = None

    # Let the application load fully
    time.sleep(2.5)

    if gw and last_opened_app_title:
        target_w = None
        for w in gw.getAllWindows():
            title = w.title.lower()
            if last_opened_app_title in title:
                target_w = w
                # If it's the exact app or ends with the app name (e.g. 'Untitled - Notepad'), it's a perfect match!
                if title == last_opened_app_title or title.endswith(last_opened_app_title):
                    break
        
        if target_w:
            w = target_w
            try:
                if w.isMinimized:
                    w.restore()
                w.activate()
            except:
                pass
            
            try:
                # Simulating a physical hardware click strictly inside the app guarantees focus.
                x = w.left + (w.width // 2)
                y = w.top + (w.height // 2)
                pyautogui.click(x, y)
                time.sleep(0.5)
            except:
                pass

    pyautogui.write(text, interval=0.02)

    return "Typed text"


# 🔥 KEYBOARD SHORTCUTS
def press_keys(keys):
    try:
        pyautogui.hotkey(*keys.lower().split("+"))
        return f"Pressed {keys}"
    except Exception as e:
        return f"Error pressing keys: {str(e)}"


# 🔥 LINKEDIN POST (MORE STABLE)
def post_on_linkedin(content):
    try:
        webbrowser.open("https://www.linkedin.com/feed/")
        time.sleep(7)  # give more load time

        pyautogui.click(500, 300)
        time.sleep(2)

        pyautogui.write(content, interval=0.01)

        return "Opened LinkedIn and typed post"

    except Exception as e:
        return f"Error posting: {str(e)}"


# 🔥 CREATE FILE
def create_file(name):
    try:
        if not name:
            name = "note.txt"

        with open(name, "w") as f:
            pass

        return f"Created file {name}"

    except Exception as e:
        return f"Error creating file: {str(e)}"


# 🔥 WRITE FILE (AI-COMPATIBLE)
def write_file(data):
    try:
        if isinstance(data, dict):
            name = data.get("name", "note.txt")
            content = data.get("content", "")
        else:
            name = "note.txt"
            content = str(data)

        with open(name, "w") as f:
            f.write(content)

        return f"Written to {name}"

    except Exception as e:
        return f"Error writing file: {str(e)}"


# 🔥 OPEN WEBSITE
def open_website(url):
    webbrowser.open(url)
    return f"Opening {url}"


# 🔥 GOOGLE SEARCH (ENCODE FIXED)
def search_google(query):
    global last_search_query
    last_search_query = query
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    return f"Searching {query}"


# 🔥 PLAY YOUTUBE VIDEO
def play_youtube(query):
    import urllib.request
    import re
    encoded = urllib.parse.quote(query)
    try:
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + encoded)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        if video_ids:
            url = f"https://www.youtube.com/watch?v={video_ids[0]}"
            webbrowser.open(url)
            return f"Playing {query} on YouTube"
    except Exception:
        pass
    
    webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
    return f"Searching YouTube for {query}"


# 🔥 OPEN FIRST RESULT DIRECTLY (ROBUST VERSION)
def open_first_result(query=""):
    global last_search_query
    import urllib.request
    import urllib.parse
    import re
    import webbrowser

    if not query:
        query = last_search_query

    if not query:
        return "No search query provided to open."

    req = urllib.request.Request(
        f'https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        match = re.search(r'a class="result__url" href="([^"]+)"', html)
        if match:
            result = match.group(1)
            if "uddg=" in result:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(result).query)
                if 'uddg' in parsed:
                    webbrowser.open(parsed['uddg'][0])
                    return f"Opened first result for {query}"
            else:
                webbrowser.open(result)
                return f"Opened first result for {query}"
    except Exception:
        pass
    
    # Fallback to standard Google Search if anything fails
    return search_google(query)


# 🔥 SEND EMAIL
def send_email(details):
    import urllib.parse
    to = ""
    subject = ""
    body = ""
    if isinstance(details, dict):
        to = details.get("to", "")
        subject = details.get("subject", "")
        body = details.get("body", "")
    else:
        to = str(details)
    
    url = f"https://mail.google.com/mail/?view=cm&fs=1&to={to}&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    webbrowser.open(url)
    return "Opened email composer"