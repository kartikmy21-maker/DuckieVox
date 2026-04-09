from tools import *
from ai_agent import ask_ai, generate_content
import memory
import duckie_content
import time
import pyperclip

def decide_and_execute(command):
    command = command.lower().strip()

    # --- 1. FIXED: Notepad Automation ---
    if "open notepad" in command:
        import pyautogui
        import time

        open_application("notepad")
        time.sleep(2.5)

        pyautogui.hotkey("win", "up")
        time.sleep(0.5)

        pyautogui.click(500, 300)
        time.sleep(0.5)

        text = command.replace("open notepad and write", "").strip()

        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")

        return "Opened notepad and wrote text"

    # --- 2. Memory Logic ---
    if "call me" in command:
        name = command.replace("call me", "").strip()
        memory.save_info("user_name", name)
        return f"Got it, I will call you {name}"

    if "my name" in command:
        name = memory.get_info("user_name")
        if name == "None" or not name:
            return "I don't know your name yet"
        return f"Your name is {name}"

    # --- 3. Greeting & Task Chaining ---
    if command in ["hello", "hi", "hey"]:
        return duckie_content.personalize_greeting()

    if "hackathon post" in command:
        return duckie_content.chain_prepare_post(
            "Duckie Assistant",
            "Voice control, AI agent, SQLite memory, task automation"
        )

    if "last post" in command:
        data = memory.get_info("last_post_draft")
        if data == "None":
            return "No post found in memory"
        return data

    # --- 4. Content & Files ---
    if "linkedin post" in command:
        return generate_content("Write a LinkedIn post about an AI hackathon project")

    if "post on linkedin" in command:
        content = generate_content("Write a LinkedIn post about an AI hackathon project")
        return post_on_linkedin(content)

    if "create file" in command:
        return create_file("note.txt")

    if "write on file" in command:
        content = generate_content("Write a short note about AI")
        return write_file("note.txt", content)

    # --- 5. Web Automation ---
    if "open youtube" in command:
        return open_website("https://youtube.com")

    if "search" in command and "first result" in command:
        query = command.replace("search", "").replace("and open first result", "").strip()
        search_google(query)
        return open_first_result()

    if "search" in command:
        query = command.replace("search", "").strip()
        return search_google(query)
    
    if "open" in command and "file" in command:
        name = command.replace("open", "").replace("file", "").replace("from my pc", "").strip()
        return open_file_by_name(name)

    # --- 6. FIXED: AI Fallback Logic ---
    # Ye part tabhi chalega jab upar wala koi 'if' match nahi hoga
    ai_result = ask_ai(command)

    if not ai_result or "steps" not in ai_result:
        return "I did not understand that command."

    results = []
    try:
        for step in ai_result.get("steps", []):
            tool = step.get("tool")
            inp = step.get("input")

            if tool == "open_website":
                results.append(open_website(inp))
            elif tool == "search_google":
                results.append(search_google(inp))
            elif tool == "open_first_result":
                results.append(open_first_result())
            elif tool == "create_file":
                results.append(create_file(inp))
            elif tool == "write_file":
                results.append(write_file("note.txt", inp))
            elif tool == "open_application":
                results.append(open_application(inp))
            elif tool == "type_text":
                results.append(type_text(inp))

        return " | ".join(results) if results else "AI could not execute task"

    except Exception as e:
        return f"AI execution error: {str(e)}"