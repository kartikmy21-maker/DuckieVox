from tools import *
from ai_agent import ask_ai, generate_content
import time


def decide_and_execute(command):
    command = command.lower().strip()
    print("🔥 COMMAND:", command)

    # ✅ 1. GREETING
    if command in ["hi", "hello", "hey", "good morning"]:
        return "Hello! How can I help you?"

    # 🧠 2. AI (HANDLES MULTITASKING & ALL TASKS)
    ai_result = ask_ai(command)

    if not ai_result or "steps" not in ai_result:
        return "I didn't understand that."

    steps = ai_result.get("steps", [])

    if not steps:
        return "Okay 👍"

    results = []
    generated_text = ""

    # ⚙️ 4. EXECUTE STEPS
    for step in steps:
        action = step.get("action")
        inp = step.get("input")

        if not action:
            continue
        
        if inp is None:
            inp = ""

        try:
            if action == "open_app":
                result = open_application(inp)
                if result:
                    results.append(result)
                else:
                    results.append(open_website(f"https://www.google.com/search?q={inp}"))
            
            elif action == "close_app":
                results.append(close_application(inp))
            
            elif action == "force_close_app":
                results.append(force_close_application(inp))

            elif action == "open_file":
                results.append(open_file_by_name(inp))

            elif action == "search":
                results.append(search_google(inp))

            elif action == "play_youtube":
                results.append(play_youtube(inp))

            elif action == "send_email":
                results.append(send_email(inp))

            elif action == "open_url":
                results.append(open_website(inp))

            elif action == "type":
                results.append(type_text(inp))

            elif action == "generate":
                generated_text = generate_content(inp)
                results.append("Generated content")

            elif action == "create_file":
                results.append(create_file(inp))

            elif action == "write_file":
                if isinstance(inp, dict):
                    if not inp.get("content"):
                        inp["content"] = generated_text
                else:
                    inp = {"name": "note.txt", "content": generated_text}

                results.append(write_file(inp))

            elif action == "open_first_result":
                results.append(open_first_result(inp))

            elif action == "press_keys":
                results.append(press_keys(inp))

            elif action == "post_linkedin":
                content = generated_text if generated_text else inp
                results.append(post_on_linkedin(content))

        except Exception as e:
            results.append(f"Error in {action}: {str(e)}")

    return " | ".join(results) if results else "Done"