from tools import *
from ai_agent import ask_ai, generate_content
from memory import save_fact, get_fact, get_all_facts, add_chat_message, get_chat_history
import re
import time


# --- Fact extraction patterns ---
NOT_A_NAME = {
    "going", "coming", "ready", "here", "there", "back", "good", "fine",
    "okay", "ok", "sure", "yes", "no", "well", "also", "just", "not",
    "done", "busy", "free", "happy", "sorry", "trying", "using", "working",
    "thinking", "doing", "saying", "looking", "asking", "getting", "running",
}

FACT_PATTERNS = [
    (r"\bmy name is ([a-z]{2,20})\b",                    "name"),
    (r"\bcall me ([a-z]{2,20})\b",                        "name"),
    (r"\bi(?:'m| am) a(?:n)? ([a-z ]{3,30}?) (?:by profession|by trade|professionally)", "profession"),
    (r"\bi work as a(?:n)? ([a-z ]{3,30})",               "profession"),
    (r"\bi(?:'m| am) (\d{1,3}) years? old",               "age"),
    (r"\bi(?:'m| am) from ([a-z]{2,20})\b",               "location"),
    (r"\bi live in ([a-z]{2,20})\b",                       "location"),
    (r"\bi (?:love|like|enjoy|prefer) ([a-z ]{3,30})",    "hobby"),
    (r"\bmy favorite (\w+) is ([a-z ]{3,30})",            None),
]


def extract_and_save_facts(text):
    """Scan text for personal facts and persist them to DB."""
    text = text.lower().strip()
    saved = []
    for pattern, key in FACT_PATTERNS:
        m = re.search(pattern, text)
        if m:
            if key is None:
                category, value = m.group(1).strip(), m.group(2).strip().rstrip(".,!? ")
                if value and value not in NOT_A_NAME:
                    save_fact(f"favorite_{category}", value)
            else:
                value = m.group(1).strip().rstrip(".,!? ")
                if value and value not in NOT_A_NAME:
                    save_fact(key, value)


# --- Main agent ---

def decide_and_execute(command):
    raw_command = command.strip()
    command_lower = raw_command.lower()
    print("Processing Command:", raw_command)

    # 1. Extract any facts revealed in the message
    extract_and_save_facts(command_lower)

    # 2. Get recent chat history for context
    history = get_chat_history(limit=12)
    
    # 3. Ask AI for conversational response and actions
    ai_result = ask_ai(raw_command, history=history)
    
    chat_response = ai_result.get("chat_response", "I've handled your request.")
    steps = ai_result.get("steps", [])

    # 4. Save conversation to history
    add_chat_message("user", raw_command)
    add_chat_message("assistant", chat_response)

    # 5. Execute Steps (if any)
    if steps:
        print(f"Executing {len(steps)} steps...")
        results = []
        generated_text = ""

        for step in steps:
            action, inp = step.get("action"), step.get("input", "")
            try:
                if action == "open_app":
                    res = open_application(inp)
                    results.append(res if res else open_website(f"https://www.google.com/search?q={inp}"))
                elif action == "close_app": results.append(close_application(inp))
                elif action == "force_close_app": results.append(force_close_application(inp))
                elif action == "open_file": results.append(open_file_by_name(inp))
                elif action == "search": results.append(search_google(inp))
                elif action == "play_youtube": results.append(play_youtube(inp))
                elif action == "send_email": results.append(send_email(inp))
                elif action == "open_url": results.append(open_website(inp))
                elif action == "type": results.append(type_text(inp))
                elif action == "generate": 
                    generated_text = generate_content(inp)
                    results.append("Generated content")
                elif action == "create_file": results.append(create_file(inp))
                elif action == "write_file":
                    content = inp.get("content", generated_text) if isinstance(inp, dict) else generated_text
                    results.append(write_file({"name": inp.get("name", "note.txt") if isinstance(inp, dict) else "note.txt", "content": content}))
                elif action == "open_first_result": results.append(open_first_result(inp))
                elif action == "press_keys": results.append(press_keys(inp))
                elif action == "post_linkedin": results.append(post_on_linkedin(generated_text if generated_text else inp))
            except Exception as e:
                results.append(f"Error in {action}: {str(e)}")
        
        print("Execution complete:", results)

    # 6. Return the friendly conversational response
    return chat_response