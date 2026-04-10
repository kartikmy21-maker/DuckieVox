import json
import ollama
from memory import get_all_facts


def ask_ai(command, history=None):
    # Load everything Duckie knows about the user
    known_facts = get_all_facts()
    memory_block = f"\n[FACTS ABOUT USER]: {known_facts}" if known_facts else ""
    
    # Prepare conversation context
    history_block = ""
    if history:
        history_block = "\n[RECENT CONVERSATION]:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history])

    prompt = f"""
You are Duckie AI, a friendly and conversational system control assistant.{memory_block}
{history_block}

Your job:
1. Chat with the user in a helpful, witty, and friendly way.
2. Convert user commands into structured JSON steps.

RULES:
- Always return valid JSON.
- Never return null inputs.
- Always provide a conversational 'chat_response'.
- Use the [FACTS ABOUT USER] to be personalized.
- If the user asks a question, answer it in 'chat_response'.
- If the user gives a command, plan the 'steps' AND describe what you're doing in 'chat_response'.

REQUIRED JSON FORMAT:
{{
  "chat_response": "Friendly message to user",
  "steps": [
    {{"action": "action_name", "input": "input_value"}}
  ]
}}

EXAMPLES:

User: hello
Output:
{{
  "chat_response": "Hello! I'm Duckie, your system assistant. How can I help you today?",
  "steps": []
}}

User: open notepad and write my name is Ritul
Output:
{{
  "chat_response": "Sure thing! I've opened Notepad for you and typed out your name.",
  "steps": [
    {{"action": "open_app", "input": "notepad"}},
    {{"action": "type", "input": "My name is Ritul"}}
  ]
}}

User command: {command}
"""

    for _ in range(2):  # light retry
        try:
            messages = [
                {"role": "system", "content": "You are a specialized AI that ONLY outputs JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = ollama.chat(model="llama3", format="json", messages=messages)

            text = response["message"]["content"]
            print("[Brain] Llama RAW:", text)

            data = json.loads(text)

            if "chat_response" in data and "steps" in data:
                return data
            
            # Fallback if AI missed fields
            return {
                "chat_response": data.get("chat_response", "I've processed your request."),
                "steps": data.get("steps", [])
            }

        except Exception as e:
            print("[Warning] Retry:", e)

    return {"chat_response": "I'm sorry, I had a bit of trouble processing that.", "steps": []}


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