from tools import *
from ai_agent import ask_ai, generate_content
from memory import save_fact, get_fact, get_all_facts
import re
import time


# ─── Fact extraction patterns ─────────────────────────────────────────────────
# These catch natural phrases the user drops into any command.
# ─── Common words that look like names/values but aren't ───────────────────
NOT_A_NAME = {
    # verbs
    "going", "coming", "ready", "here", "there", "back", "good", "fine",
    "okay", "ok", "sure", "yes", "no", "well", "also", "just", "not",
    "done", "busy", "free", "happy", "sorry", "trying", "using", "working",
    "thinking", "doing", "saying", "looking", "asking", "getting", "running",
    "leaving", "starting", "stopping", "calling", "waiting", "playing",
    # common words
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "of", "for",
    "and", "or", "but", "so", "with", "from", "by", "up", "down",
    # filler
    "very", "really", "pretty", "quite", "little", "big", "new", "old",
}

FACT_PATTERNS = [
    # Name — only explicit phrases, NOT "I am [verb]"
    (r"\bmy name is ([a-z]{2,20})\b",                    "name"),
    (r"\bcall me ([a-z]{2,20})\b",                        "name"),
    (r"\bpeople call me ([a-z]{2,20})\b",                  "name"),
    (r"\beveryone calls me ([a-z]{2,20})\b",               "name"),

    # Profession / job
    (r"\bi(?:'m| am) a(?:n)? ([a-z ]{3,30}?) (?:by profession|by trade|professionally)", "profession"),
    (r"\bi work as a(?:n)? ([a-z ]{3,30})",               "profession"),
    (r"\bmy (?:job|profession|occupation|role) is ([a-z ]{3,30})", "profession"),
    (r"\bi(?:'m| am) a(?:n)? ([a-z]{3,20}(?:\s[a-z]{3,20})?) (?:developer|engineer|designer|student|teacher|doctor|manager)", "profession"),

    # Age
    (r"\bi(?:'m| am) (\d{1,3}) years? old",               "age"),
    (r"\bmy age is (\d{1,3})\b",                           "age"),

    # Location — stop at end of clause (comma, period, or 3 words)
    (r"\bi(?:'m| am) from ([a-z]{2,20})\b",               "location"),
    (r"\bi live in ([a-z]{2,20})\b",                       "location"),
    (r"\bmy city is ([a-z]{2,20})\b",                      "location"),
    (r"\bi(?:'m| am) from ([a-z]+ [a-z]+)\b",             "location"),

    # Hobbies / interests
    (r"\bi (?:love|like|enjoy|prefer) ([a-z ]{3,30})",    "hobby"),
    (r"\bmy hobby is ([a-z ]{3,30})",                      "hobby"),
    (r"\bmy favorite (\w+) is ([a-z ]{3,30})",            None),

    # Dislikes
    (r"\bi (?:hate|dislike|can't stand) ([a-z ]{3,30})",  "dislike"),
]


def extract_and_save_facts(text):
    """Scan text for personal facts and persist them to DB."""
    text = text.lower().strip()
    saved = []

    for pattern, key in FACT_PATTERNS:
        if key is None:
            m = re.search(pattern, text)
            if m:
                category = m.group(1).strip()
                value    = m.group(2).strip().rstrip(".,!? ")
                if value and value not in NOT_A_NAME and len(value) >= 2:
                    fact_key = f"favorite_{category}"
                    save_fact(fact_key, value)
                    saved.append(f"{fact_key}={value}")
        else:
            m = re.search(pattern, text)
            if m:
                value = m.group(1).strip().rstrip(".,!? ")
                # Skip falsy values, blocklisted words, numbers for name, etc.
                if (len(value) >= 2
                        and value not in NOT_A_NAME
                        and not (key == "name" and (value.isdigit() or len(value) < 2))):
                    save_fact(key, value)
                    saved.append(f"{key}={value}")

    if saved:
        print(f"🧠 Facts extracted: {saved}")



# ─── Main agent ──────────────────────────────────────────────────────────────

def decide_and_execute(command):
    raw_command = command.strip()
    command = raw_command.lower().strip()
    print("🔥 COMMAND:", command)

    # 🧠 Passively extract any facts the user reveals
    extract_and_save_facts(command)

    # ✅ 1. GREETING — personalized if name is known
    if command in ["hi", "hello", "hey", "good morning"]:
        name = get_fact("name")
        if name:
            return f"Hello, {name.capitalize()}! How can I help you?"
        return "Hello! How can I help you?"

    # ❓ 2. Memory recall questions ("what's my name?", "do you know my profession?")
    recall_triggers = [
        ("what is my name", "name"),
        ("what's my name", "name"),
        ("do you know my name", "name"),
        ("my name", "name"),
        ("what is my profession", "profession"),
        ("what's my profession", "profession"),
        ("what do i do", "profession"),
        ("what is my job", "profession"),
        ("what is my age", "age"),
        ("how old am i", "age"),
        ("where am i from", "location"),
        ("where do i live", "location"),
        ("what do i like", "hobby"),
        ("what are my hobbies", "hobby"),
        ("what do i hate", "dislike"),
        ("what do i dislike", "dislike"),
    ]
    for trigger, key in recall_triggers:
        if trigger in command:
            val = get_fact(key)
            if val:
                return f"I remember your {key} is: {val.capitalize()}"
            return f"I don't know your {key} yet. Tell me and I'll remember!"

    # "tell me what you know about me"
    if any(p in command for p in ["what do you know about me", "what do you remember", "tell me about me"]):
        facts = get_all_facts()
        if facts:
            return f"Here's what I know about you: {facts}"
        return "I don't know much about you yet. Tell me your name, job, hobbies — I'll remember!"

    # 🧠 3. AI (multi-step tasks)
    ai_result = ask_ai(raw_command)

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