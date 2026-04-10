from flask import Flask, render_template, request, jsonify, Response
from agent import decide_and_execute
from voice import speech_to_text, speak, always_on_loop
import threading
import queue
import json
import traceback

app = Flask(__name__)

# ── Shared event queue (background → SSE → frontend) ─────────────────────────
_event_queue: queue.Queue = queue.Queue(maxsize=100)

def push_event(etype: str, payload):
    """Put an event on the queue. Drops oldest if full."""
    try:
        _event_queue.put_nowait({"type": etype, "data": payload})
    except queue.Full:
        try:
            _event_queue.get_nowait()
            _event_queue.put_nowait({"type": etype, "data": payload})
        except Exception:
            pass


# ── Start always-on listener in background ────────────────────────────────────
def _start_listener():
    always_on_loop(push_event)

_listener_thread = threading.Thread(target=_start_listener, daemon=True, name="DuckieListener")
_listener_thread.start()
print("🦆 Always-on listener started.")


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/events")
def events():
    """SSE endpoint — streams status/command/response to frontend."""
    def generate():
        while True:
            try:
                event = _event_queue.get(timeout=25)
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                yield "data: {\"type\":\"ping\"}\n\n"   # keep-alive
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"})


@app.route("/execute", methods=["POST"])
def execute():
    data    = request.json
    command = data.get("command", "").strip()
    if not command:
        return jsonify({"status": "error", "message": "Empty command"})

    print("💬 Text command:", command)
    push_event("command", command)
    push_event("status", "thinking")

    response = decide_and_execute(command)

    push_event("response", response)
    push_event("status", "listening")
    threading.Thread(target=speak, args=(response,), daemon=True).start()

    return jsonify({"status": "success", "command": command, "message": response})


@app.route("/voice", methods=["POST"])
def voice():
    """Manual mic trigger (fallback — always-on is preferred)."""
    try:
        text = speech_to_text()
        if not text:
            return jsonify({"status": "error", "message": "Didn't catch that."})

        push_event("command", text)
        push_event("status", "thinking")

        response = decide_and_execute(text)

        push_event("response", response)
        push_event("status", "listening")
        threading.Thread(target=speak, args=(response,), daemon=True).start()

        return jsonify({"status": "success", "command": text, "message": response})
    except Exception as e:
        print(f"❌ Voice Error:\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"Voice failed: {str(e)}"})


if __name__ == "__main__":
    app.run(debug=False, threaded=True)   # debug=False prevents double-thread start