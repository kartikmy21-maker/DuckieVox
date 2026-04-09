from tools import *
from ai_agent import ask_ai, generate_content
import memory
import duckie_content

def decide_and_execute(command):
    command = command.lower().strip()

    # 🧠 MEMORY (SQLite - Person 3)
    if "call me" in command:
        name = command.replace("call me", "").strip()
        memory.save_info("user_name", name)
        return f"Got it, I will call you {name}"

    if "my name" in command:
        name = memory.get_info("user_name")
        if name == "None" or not name:
            return "I don't know your name yet"
        return f"Your name is {name}"

    # 👋 PERSONALIZED GREETING
    if "hello" in command or "hi" in command:
        return duckie_content.personalize_greeting()

    # 🔥 TASK CHAINING (BEST FEATURE)
    if "hackathon post" in command:
        return duckie_content.chain_prepare_post(
            "Duckie Assistant",
            "Voice control, AI agent, SQLite memory, task automation"
        )

    # 🧾 SHOW LAST SAVED POST
    if "last post" in command:
        data = memory.get_info("last_post_draft")
        if data == "None":
            return "No post found in memory"
        return data

    # 🔥 CONTENT GENERATION (AI)
    if "linkedin post" in command:
        return generate_content("Write a LinkedIn post about an AI hackathon project")

    if "post on linkedin" in command:
        content = generate_content("Write a LinkedIn post about an AI hackathon project")
        return post_on_linkedin(content)

    # 📁 FILE SYSTEM
    if "create file" in command:
        return create_file("note.txt")

    if "write file" in command:
        content = generate_content("Write a short note about AI")
        return write_file("note.txt", content)

    # 🌐 WEB AUTOMATION
    if "youtube" in command:
        return open_website("https://youtube.com")

    if "search" in command and "first result" in command:
        query = command.replace("search", "").replace("and open first result", "").strip()
        search_google(query)
        return open_first_result()

    if "search" in command:
        query = command.replace("search", "").strip()
        return search_google(query)

    # 🤖 AI FALLBACK (SMART PART)
    ai_result = ask_ai(command)

    if not ai_result:
        return "I did not understand"

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

        return " | ".join(results) if results else "AI could not execute task"

    except Exception as e:
        return f"AI execution error: {str(e)}"