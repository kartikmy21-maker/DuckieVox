import json
import ollama
from memory import get_all_facts


def ask_ai(command):
    # 🧠 Load everything Duckie knows about the user
    known_facts = get_all_facts()
    memory_block = f"\nWhat I know about the user: {known_facts}" if known_facts else ""

    prompt = f"""
You are Duckie AI, a system control assistant.{memory_block}

Your job:
Convert user commands into structured JSON steps.

RULES:
- Always return valid JSON
- Do NOT include any explanation
- Only return JSON
- Never return null inputs
- Break tasks into clear steps

GREETING:
If user says:
hello, hi, hey, good morning
→ return:
{{ "steps": [] }}

EXAMPLES:

User: open notepad
Output:
{{
  "steps": [
    {{"action": "open_app", "input": "notepad"}}
  ]
}}

User: open youtube
Output:
{{
  "steps": [
    {{"action": "open_app", "input": "youtube"}}
  ]
}}

User: open notepad and write hello
Output:
{{
  "steps": [
    {{"action": "open_app", "input": "notepad"}},
    {{"action": "type", "input": "hello"}}
  ]
}}
If the command contains "and", you MUST split it into multiple steps.

Example:

User: open youtube and play lofi music

Output:
{{
  "steps": [
    {{"action": "play_youtube", "input": "lofi music"}}
  ]
}}

Example:

User: send an email to boss about the meeting

Output:
{{
  "steps": [
    {{"action": "send_email", "input": {{"to": "boss", "subject": "Meeting", "body": "Hello, wanted to discuss the meeting."}}}}
  ]
}}

Example:

User: search for AI tools and open the first result

Output:
{{
  "steps": [
    {{"action": "open_first_result", "input": "AI tools"}}
  ]
}}

Example:

User: close notepad please

Output:
{{
  "steps": [
    {{"action": "close_app", "input": "notepad"}}
  ]
}}

Example:

User: forcefully kill notepad

Output:
{{
  "steps": [
    {{"action": "force_close_app", "input": "notepad"}}
  ]
}}

AVAILABLE ACTIONS:
- open_app
- close_app
- force_close_app
- open_file
- open_url
- search
- play_youtube
- send_email
- type
- generate
- create_file
- write_file
- press_keys
- post_linkedin
- open_first_result

User command: {command}
"""

    for _ in range(2):  # light retry
        try:
            response = ollama.chat(
                model="llama3",
                format="json",
                messages=[
                    {"role": "system", "content": "You must strictly return JSON under all circumstances."},
                    {"role": "user", "content": prompt}
                ]
            )

            text = response["message"]["content"]
            print("🧠 Llama RAW:", text)

            # Extract JSON safely
            start = text.find("{")
            end = text.rfind("}") + 1

            if start == -1 or end == -1:
                continue

            json_text = text[start:end]
            data = json.loads(json_text)

            if "steps" in data:
                return data

        except Exception as e:
            print("⚠️ Retry:", e)

    return {"steps": []}


def generate_content(prompt):
    try:
        response = ollama.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": "You generate clean, high-quality content."},
                {"role": "user", "content": prompt}
            ]
        )

        return response["message"]["content"]

    except Exception as e:
        return f"Error generating content: {str(e)}"