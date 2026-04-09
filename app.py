from flask import Flask, render_template, request, jsonify
from agent import decide_and_execute
from voice import speak
import threading

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    command = data.get("command", "").lower().strip()

    # 🔥 USE YOUR REAL AGENT
    response = decide_and_execute(command)

    # 🔊 Speak in background
    threading.Thread(target=speak, args=(response,)).start()

    return jsonify({
        "status": "success",
        "message": response
    })

if __name__ == "__main__":
    app.run(debug=True)