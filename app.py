from flask import Flask, render_template, request, jsonify
from agent import decide_and_execute
from voice import speak
import threading
import whisper
import tempfile
import sounddevice as sd
from scipy.io.wavfile import write
import os

app = Flask(__name__)

# 🔥 Load Whisper once
model = whisper.load_model("base")


@app.route("/")
def index():
    return render_template("index.html")


# 🔥 TEXT COMMAND
@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    command = data.get("command", "").strip()

    if not command:
        return jsonify({"status": "error", "message": "Empty command"})

    print("💬 Command:", command)

    response = decide_and_execute(command)

    # 🔊 Speak asynchronously (non-blocking)
    threading.Thread(target=speak, args=(response,), daemon=True).start()

    return jsonify({
        "status": "success",
        "command": command,
        "message": response
    })


# 🔥 VOICE COMMAND
@app.route("/voice", methods=["POST"])
def voice():
    try:
        fs = 44100
        duration = 3  # ⚡ reduced for faster response

        print("🎤 Recording...")

        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()

        # 🔥 Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            write(temp_file.name, fs, recording)

            print("🧠 Transcribing...")
            result = model.transcribe(temp_file.name, language="en")
            text = result["text"].strip()

        # 🔥 Clean up
        try:
            os.remove(temp_file.name)
        except:
            pass

        if not text:
            return jsonify({"status": "error", "message": "Didn't catch that"})

        print("🗣️ You said:", text)

        # ⚡ Execute immediately
        response = decide_and_execute(text)

        # 🔊 Speak in background
        threading.Thread(target=speak, args=(response,), daemon=True).start()

        return jsonify({
            "status": "success",
            "command": text,
            "message": response
        })

    except Exception as e:
        print(f"❌ Voice Error: {e}")
        return jsonify({
            "status": "error",
            "message": "Voice processing failed"
        })


if __name__ == "__main__":
    app.run(debug=True)