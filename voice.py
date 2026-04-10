import numpy as np
import sounddevice as sd
import whisper
import tempfile
import os
import traceback
from difflib import SequenceMatcher
from scipy.io.wavfile import write as wav_write

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import noisereduce as nr
    _HAS_NR = True
except ImportError:
    _HAS_NR = False

try:
    from scipy.signal import butter, sosfilt
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

try:
    import pyttsx3
    _HAS_TTS = True
except ImportError:
    _HAS_TTS = False

try:
    import vosk
    import json
    _HAS_VOSK = True
except ImportError:
    _HAS_VOSK = False

# ── Constants ─────────────────────────────────────────────────────────────────
SAMPLE_RATE      = 16000
CHANNELS         = 1
MAX_SILENCE_SEC  = 2.0
MAX_RECORD_SEC   = 10
MIN_SPEECH_SEC   = 0.3
CHUNK_SEC        = 0.1

# Wake word clip length — short for fast detection
WAKE_CHUNK_SEC   = 1.5

# ── Wake word variants (accent/spelling tolerance) ────────────────────────────
# "Duckie" said with different accents, speeds, and spellings.
# Also includes common Whisper mishearings: "dogi", "the key", "toki", "dogi", etc.
WAKEWORD_VARIANTS = {
    # Full Phrases (Primary triggers)
    "hey duckie", "hey ducky", "hi duckie", "hi ducky", "hello duckie",
    "hey doki", "hi doki", "hey dukie",
    # Phonetic phrase variants
    "the key", "thekey", "da key",
    # Sensitive/Standalone variants
    "duckie", "ducky", "doggie", "dogi", "tucky", "doki", "dukie"
}

# ── Load Whisper models ───────────────────────────────────────────────────────
print("[Brain] Loading Whisper models...")
try:
    _wake_model = whisper.load_model("tiny")    # fast, for wake word only
    print("[Whisper] Whisper 'tiny' (wake) ready.")
except Exception as e:
    print(f"[Warning] Tiny model failed: {e}")
    _wake_model = None

try:
    _cmd_model = whisper.load_model("small")    # accurate, for commands
    print("[Whisper] Whisper 'small' (command) ready.")
except Exception as e:
    print(f"[Warning] Small model failed ({e}), trying base")
    _cmd_model = whisper.load_model("base")

# ── Vosk Setup (for Wake Word) ───────────────────────────────────────────────
_vosk_model = None
_vosk_rec   = None

def _init_vosk():
    global _vosk_model, _vosk_rec
    if not _HAS_VOSK: return
    try:
        if _vosk_model is None:
            print("[Vosk] Loading Vosk wake-word model...")
            # This will download to ~/.cache/vosk if not found
            _vosk_model = vosk.Model(model_name="vosk-model-small-en-us-0.15")
        
        # Grammar now includes 'hey' to support multi-word wake words
        # Added 'ritul' to grammar so the engine can distinguish it from 'duckie'
        grammar = [
            "hey duckie", "hey ducky", "hi duckie", "hello duckie",
            "duckie", "ducky", "dukie", "doki", "dogi", 
            "the key", "da key", "doggie", "hey", "hi", "hello",
            "ritul", 
            "[unk]"
        ]
        _vosk_rec = vosk.KaldiRecognizer(_vosk_model, SAMPLE_RATE, json.dumps(grammar))
        print("[Vosk] Vosk engine ready (Grammar localized).")
    except Exception as e:
        print(f"[Warning] Vosk init failed: {e}")

_init_vosk()

# ── TTS ───────────────────────────────────────────────────────────────────────
def speak(text: str):
    if not _HAS_TTS:
        print(f"[TTS] {text}")
        return
    try:
        engine = pyttsx3.init('sapi5')
        engine.setProperty('rate', 175)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[Error] TTS error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  AUDIO HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))

def _normalize(audio: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(audio))
    return (audio / peak).astype(np.float32) if peak > 1e-6 else audio

def _bandpass(audio: np.ndarray, sr: int) -> np.ndarray:
    if not _HAS_SCIPY:
        return audio
    try:
        sos = butter(4, [80.0, 7800.0], btype='band', fs=sr, output='sos')
        return sosfilt(sos, audio).astype(np.float32)
    except Exception:
        return audio

def _noise_reduce(audio: np.ndarray, sr: int) -> np.ndarray:
    if not _HAS_NR:
        return audio
    try:
        noise_len = min(int(sr * 0.3), len(audio))
        return nr.reduce_noise(y=audio, sr=sr,
                               y_noise=audio[:noise_len],
                               stationary=False,
                               prop_decrease=0.80).astype(np.float32)
    except TypeError:
        try:
            return nr.reduce_noise(y=audio, sr=sr).astype(np.float32)
        except Exception:
            return audio
    except Exception:
        return audio

def _trim_silence(audio: np.ndarray, sr: int, threshold: float) -> np.ndarray:
    frame_len = int(sr * 0.02)
    frames = [audio[i:i+frame_len] for i in range(0, len(audio), frame_len)]
    voiced = [i for i, f in enumerate(frames) if _rms(f) > threshold]
    if not voiced:
        return audio
    start = voiced[0] * frame_len
    end   = min((voiced[-1] + 1) * frame_len, len(audio))
    return audio[start:end]

def _calibrate_noise(stream, calibrate_chunks: int) -> float:
    """Measure ambient noise floor, return dynamic threshold."""
    energies = []
    for _ in range(calibrate_chunks):
        chunk, _ = stream.read(int(SAMPLE_RATE * CHUNK_SEC))
        energies.append(_rms(chunk.flatten()))
    noise_floor = float(np.mean(energies))
    return max(0.015, min(noise_floor * 3.5, 0.12))


# ══════════════════════════════════════════════════════════════════════════════
#  WAKE WORD DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def is_wakeword(text: str) -> bool:
    """
    Fuzzy match against 'Hey Duckie' phrases.
    Enforces the 'Hey/Hi' requirement to stop single-word false triggers (like user names).
    """
    text = text.lower().strip()
    
    # 1. 🛑 Immediate block for user's name or similar sounding words
    if any(blocked in text for blocked in ("ritul", "ritual", "riddle", "riddul")):
        return False

    # 2. 🎯 Exact Phrase Match (Highest priority)
    # The grammar forces specific results, so we look for these first.
    if any(phrase in text for phrase in ("hey duckie", "hey ducky", "hi duckie", "hi ducky", "hello duckie")):
        print(f"[Wake] Phrase match detected: '{text}'")
        return True

    # 3. 🔍 Split for deeper validation
    words = text.replace(",", " ").replace(".", " ").split()
    if not words:
        return False

    # 4. 🧩 Greeting + Variant check
    # Requires a greeting word (Hey/Hi/Hello/Duckie) AND a high-sim match
    has_greeting = any(w in words for w in ("hey", "hi", "hello", "hey!"))
    
    for word in words:
        word = word.strip(".,!?'\"")
        if not word: continue

        # If it's the exact phrase or we have a greeting, check the core word
        for variant in WAKEWORD_VARIANTS:
            # Check if current word sounds like any part of our variants
            sim = _similarity(word, variant.split()[-1]) # match against 'duckie' part
            if sim >= 0.75: # Lowered from 0.82
                # If we have the greeting OR the word is strong enough by itself
                if has_greeting or sim >= 0.82: # Lowered from 0.90
                    print(f"[Wake] Match verified: '{word}' ~ '{variant}' ({sim:.2f})")
                    return True

    # ── Legacy phrase catch ──
    if any(phrase in text for phrase in ("the key", "da key", "da ki")):
        print(f"[Wake] Phrase match: '{text}'")
        return True

    return False

def _transcribe_audio(audio: np.ndarray, model, fast: bool = False) -> str:
    """Save audio to temp WAV and transcribe with given model."""
    if len(audio) / SAMPLE_RATE < MIN_SPEECH_SEC:
        return ""

    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        tmp = f.name
    wav_write(tmp, SAMPLE_RATE, audio_int16)

    try:
        kwargs = dict(language="en", task="transcribe", fp16=False,
                      no_speech_threshold=0.5)
        if not fast:
            kwargs.update(temperature=0.0, beam_size=5,
                          no_speech_threshold=0.6, logprob_threshold=-1.0)
        try:
            kwargs["condition_on_previous_text"] = False
            result = model.transcribe(tmp, **kwargs)
        except TypeError:
            kwargs.pop("condition_on_previous_text", None)
            result = model.transcribe(tmp, **kwargs)
        return result["text"].strip()
    except Exception as e:
        print(f"[Warning] Transcription error: {e}")
        return ""
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass


def listen_for_wakeword(stream, threshold: float) -> bool:
    """
    Read audio from stream and check for wake word using Vosk.
    If Vosk is missing, falls back to Whisper (not recommended).
    """
    chunk_size = int(SAMPLE_RATE * WAKE_CHUNK_SEC)
    data, _ = stream.read(chunk_size)
    audio = data.flatten()

    # Adjusted energy check: lowered to 1.0x to be more sensitive to speech
    if _rms(audio) < threshold * 1.0:
        return False

    if _HAS_VOSK and _vosk_rec:
        # Convert to int16 for Vosk
        audio_int16 = (audio * 32767).astype(np.int16).tobytes()
        if _vosk_rec.AcceptWaveform(audio_int16):
            res = json.loads(_vosk_rec.Result())
            text = res.get("text", "")
        else:
            res = json.loads(_vosk_rec.PartialResult())
            text = res.get("partial", "")
        
        if text:
            print(f"Listening: Vosk heard: {text!r}")
            # With grammar restricted, we can use simpler matching
            return is_wakeword(text)
    
    # Fallback to Whisper
    model = _wake_model if _wake_model else _cmd_model
    text = _transcribe_audio(audio, model, fast=True)
    if text:
        print(f"Listening: Heard (Fallback): {text!r}")
    return is_wakeword(text)


# ══════════════════════════════════════════════════════════════════════════════
#  COMMAND RECORDING (after wake word)
# ══════════════════════════════════════════════════════════════════════════════

def record_command(stream, threshold: float) -> np.ndarray:
    """
    Record user command using VAD until silence.
    Reuses the already-open stream from the wake word loop.
    """
    chunk_size   = int(SAMPLE_RATE * CHUNK_SEC)
    silent_limit = int(MAX_SILENCE_SEC / CHUNK_SEC)
    max_chunks   = int(MAX_RECORD_SEC / CHUNK_SEC)

    chunks = []
    silent_count = 0
    speech_started = False

    for i in range(max_chunks):
        chunk, _ = stream.read(chunk_size)
        chunk = chunk.flatten()
        chunks.append(chunk.copy())

        energy = _rms(chunk)
        if energy > threshold:
            speech_started = True
            silent_count = 0
        elif speech_started:
            silent_count += 1
            if silent_count >= silent_limit:
                print(f"[Done] Command done at {(i+1)*CHUNK_SEC:.1f}s")
                break

    return np.concatenate(chunks) if chunks else np.zeros(chunk_size, dtype='float32')

def clean_and_transcribe(raw: np.ndarray) -> str:
    """Full cleaning pipeline + accurate transcription for commands."""
    audio = raw.astype(np.float32)
    audio = _bandpass(audio, SAMPLE_RATE)
    audio = _noise_reduce(audio, SAMPLE_RATE)
    audio = _trim_silence(audio, SAMPLE_RATE, threshold=0.008)
    audio = _normalize(audio)

    _HALLUCINATIONS = {
        "", ".", "..", "...", "you", "bye", "bye.", "okay",
        "thank you", "thank you.", "thanks", "subscribe",
    }
    text = _transcribe_audio(audio, _cmd_model, fast=False)
    print(f"[Brain] Command text: {text!r}")
    if text.lower().rstrip(".!? ") in _HALLUCINATIONS or len(text) < 2:
        return ""
    return text


# ══════════════════════════════════════════════════════════════════════════════
#  ALWAYS-ON LISTENER LOOP  (runs in a background thread)
# ══════════════════════════════════════════════════════════════════════════════

def always_on_loop(push_event_fn):
    """
    Infinite loop:
      1. Calibrate noise floor (0.5s)
      2. Listen for wake word in 1.5s chunks
      3. On detection → push 'activated' event → record command → execute
    push_event_fn(type, payload) sends events to the SSE queue.
    """
    import time
    calibrate_chunks = int(0.5 / CHUNK_SEC)

    while True:
        try:
            push_event_fn("status", "idle")

            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                                dtype='float32') as stream:

                # Calibrate noise floor each session
                threshold = _calibrate_noise(stream, calibrate_chunks)
                print(f"[Audio] Noise floor calibrated -> threshold: {threshold:.5f}")
                push_event_fn("status", "listening")

                while True:
                    if listen_for_wakeword(stream, threshold):
                        # ── Wake word detected ───────────────────────────────
                        push_event_fn("status", "activated")
                        speak("Yes?")

                        push_event_fn("status", "recording")
                        raw = record_command(stream, threshold)
                        command_text = clean_and_transcribe(raw)

                        if not command_text:
                            push_event_fn("status", "listening")
                            continue

                        push_event_fn("command", command_text)
                        push_event_fn("status", "thinking")

                        # Import here to avoid circular import
                        from agent import decide_and_execute
                        response = decide_and_execute(command_text)

                        push_event_fn("response", response)
                        
                        # Synchronous speak ensures we don't listen to our own voice
                        speak(response)
                        
                        push_event_fn("status", "listening")

        except Exception as e:
            print(f"[Error] always_on_loop error: {e}")
            traceback.print_exc()
            import time
            time.sleep(2)  # brief cooldown before restarting


# ══════════════════════════════════════════════════════════════════════════════
#  LEGACY — still used by /voice manual route
# ══════════════════════════════════════════════════════════════════════════════

def speech_to_text() -> str:
    """Manual voice trigger (fallback for the text-mode mic button)."""
    chunk_size   = int(SAMPLE_RATE * CHUNK_SEC)
    calibrate_n  = int(0.5 / CHUNK_SEC)
    max_chunks   = int(MAX_RECORD_SEC / CHUNK_SEC)
    silent_limit = int(MAX_SILENCE_SEC / CHUNK_SEC)

    chunks, noise_e = [], []
    silent_count, speech_started = 0, False

    print("Manual voice -- calibrating...")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype='float32') as stream:
        for _ in range(calibrate_n):
            c, _ = stream.read(chunk_size)
            noise_e.append(_rms(c.flatten()))
        threshold = max(0.015, min(float(np.mean(noise_e)) * 3.5, 0.12))
        print(f"Manual voice: Listening (threshold={threshold:.4f})")

        for i in range(max_chunks):
            chunk, _ = stream.read(chunk_size)
            chunk = chunk.flatten()
            chunks.append(chunk.copy())
            energy = _rms(chunk)
            if energy > threshold:
                speech_started = True
                silent_count = 0
            elif speech_started:
                silent_count += 1
                if silent_count >= silent_limit:
                    break

    raw = np.concatenate(chunks) if chunks else np.zeros(chunk_size, dtype='float32')
    return clean_and_transcribe(raw)