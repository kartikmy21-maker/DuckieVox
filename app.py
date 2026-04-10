from flask import Flask, render_template, request, jsonify
from agent import decide_and_execute
from voice import speech_to_text, speak
import threading
import traceback

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


# ── TEXT COMMAND ──────────────────────────────────────────────────────────────
@app.route("/execute", methods=["POST"])
def execute():
    data    = request.json
    command = data.get("command", "").strip()

    if not command:
        return jsonify({"status": "error", "message": "Empty command"})

    print("💬 Command:", command)
    response = decide_and_execute(command)
    threading.Thread(target=speak, args=(response,), daemon=True).start()

    return jsonify({"status": "success", "command": command, "message": response})


# ── VOICE COMMAND ─────────────────────────────────────────────────────────────
@app.route("/voice", methods=["POST"])
def voice():
    try:
        text = speech_to_text()

        if not text:
            return jsonify({"status": "error", "message": "Didn't catch that — please try again."})

        print("🗣️ You said:", text)
        response = decide_and_execute(text)
        threading.Thread(target=speak, args=(response,), daemon=True).start()

        return jsonify({"status": "success", "command": text, "message": response})

    except Exception as e:
        print(f"❌ Voice Error:\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"Voice failed: {str(e)}"})


if __name__ == "__main__":
    app.run(debug=True)