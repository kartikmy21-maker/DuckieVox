from flask import Flask, render_template, request, jsonify
from agent import decide_and_execute
from voice import speak
import threading
import whisper
import numpy as np
import tempfile
import sounddevice as sd

from scipy.io.wavfile import write 

app = Flask(__name__)
model = whisper.load_model("base")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    command = data.get("command", "").lower().strip()
    response = decide_and_execute(command)
    
    # Duckie bolega
    threading.Thread(target=speak, args=(response,)).start()

    return jsonify({"status": "success", "message": response})

@app.route("/voice", methods=["POST"])
def voice():
    try:
        fs = 44100  # Sample rate
        duration = 4  # Seconds
        
        print("🎤 Recording...")
        # Device ID None rakho taaki default mic use kare
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        
        # Temp file mein save karo
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        
        # 🛑 YAHAN DHAYAN DO: 'write' use karna hai
        write(temp_file.name, fs, recording) 
        
        # Whisper transcription
        result = model.transcribe(temp_file.name)
        text = result["text"].strip()
        
        if not text:
            return jsonify({"status": "error", "message": "Kuch sunayi nahi diya"})

        response = decide_and_execute(text)
        threading.Thread(target=speak, args=(response,)).start()

        return jsonify({
            "status": "success",
            "command": text,
            "message": response
        })
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True)