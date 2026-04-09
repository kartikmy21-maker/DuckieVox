import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_content(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You generate high-quality content like LinkedIn posts, captions, etc."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content
        return content

    except Exception as e:
        return f"Error generating content: {str(e)}"

def ask_ai(command):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
You are Duckie AI.

Available tools:
- open_website(url)
- search_google(query)
- open_first_result()

Convert user command into steps.

Respond ONLY in JSON:
{
  "steps": [
    {"tool": "tool_name", "input": "value"}
  ]
}
"""
                },
                {
                    "role": "user",
                    "content": command
                }
            ]
        )

        reply = response.choices[0].message.content
        print("🧠 AI:", reply)

        return json.loads(reply)

    except Exception as e:
        print("AI Error:", e)
        return None