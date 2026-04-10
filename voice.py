import numpy as np
import sounddevice as sd
import whisper
import tempfile
import os
import traceback
from scipy.io.wavfile import write as wav_write

# ── Optional imports with graceful fallback ────────────────────────────────────
try:
    import noisereduce as nr
    _HAS_NR = True
except ImportError:
    _HAS_NR = False
    print("⚠️  noisereduce not installed — noise reduction disabled")

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
    print("⚠️  pyttsx3 not installed — TTS disabled")


# ── Constants ─────────────────────────────────────────────────────────────────
SAMPLE_RATE       = 16000
CHANNELS          = 1
SILENCE_THRESHOLD = 0.008   # RMS energy — lowered so VAD doesn't stop immediately
MAX_SILENCE_SEC   = 2.0     # stop after this many seconds of consecutive silence
MAX_RECORD_SEC    = 10      # absolute hard cap
MIN_SPEECH_SEC    = 0.3     # discard clips shorter than this
CHUNK_SEC         = 0.1     # VAD window size

# ── Load Whisper once ─────────────────────────────────────────────────────────
print("🧠 Loading Whisper...")
try:
    whisper_model = whisper.load_model("small")
    print("✅ Whisper 'small' ready.")
except Exception:
    print("⚠️  'small' unavailable, falling back to 'base'")
    whisper_model = whisper.load_model("base")


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
        print(f"❌ TTS error: {e}")


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
        # high must be < sr/2 (Nyquist). sr=16000 → max=7999
        sos = butter(4, [80.0, 7800.0], btype='band', fs=sr, output='sos')
        return sosfilt(sos, audio).astype(np.float32)
    except Exception as e:
        print(f"⚠️  Bandpass failed: {e}")
        return audio

def _noise_reduce(audio: np.ndarray, sr: int) -> np.ndarray:
    if not _HAS_NR:
        return audio
    try:
        noise_len = min(int(sr * 0.3), len(audio))
        return nr.reduce_noise(
            y=audio, sr=sr,
            y_noise=audio[:noise_len],
            stationary=False,
            prop_decrease=0.80,
        ).astype(np.float32)
    except TypeError:
        try:
            return nr.reduce_noise(y=audio, sr=sr).astype(np.float32)
        except Exception as e:
            print(f"⚠️  Noise reduce fallback failed: {e}")
            return audio
    except Exception as e:
        print(f"⚠️  Noise reduce failed: {e}")
        return audio

def _trim_silence(audio: np.ndarray, sr: int) -> np.ndarray:
    frame_len = int(sr * 0.02)
    frames = [audio[i:i+frame_len] for i in range(0, len(audio), frame_len)]
    voiced = [i for i, f in enumerate(frames) if _rms(f) > SILENCE_THRESHOLD]
    if not voiced:
        return audio
    start = voiced[0] * frame_len
    end   = min((voiced[-1] + 1) * frame_len, len(audio))
    return audio[start:end]


# ══════════════════════════════════════════════════════════════════════════════
#  SMART VAD RECORDING
# ══════════════════════════════════════════════════════════════════════════════

def record_until_silence() -> np.ndarray:
    chunk_size   = int(SAMPLE_RATE * CHUNK_SEC)
    max_chunks   = int(MAX_RECORD_SEC / CHUNK_SEC)
    silent_limit = int(MAX_SILENCE_SEC / CHUNK_SEC)
    calibrate_chunks = int(0.5 / CHUNK_SEC)  # 0.5s noise floor measurement

    print("🎤 Calibrating noise floor... (stay quiet for 0.5s)")

    chunks = []
    silent_count = 0
    speech_started = False
    peak_energy = 0.0
    noise_energies = []

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype='float32') as stream:

        # ── Phase 1: measure background noise (first 0.5s) ──────────────────
        for _ in range(calibrate_chunks):
            chunk, _ = stream.read(chunk_size)
            noise_energies.append(_rms(chunk.flatten()))

        # Dynamic threshold = noise floor × 3.5 (clamped to reasonable range)
        noise_floor = float(np.mean(noise_energies))
        dynamic_threshold = max(0.015, min(noise_floor * 3.5, 0.12))
        print(f"🔇 Noise floor: {noise_floor:.5f} → Speech threshold: {dynamic_threshold:.5f}")
        print("🎤 Listening... (speak now)")

        # ── Phase 2: actual recording with VAD ──────────────────────────────
        for i in range(max_chunks):
            chunk, _ = stream.read(chunk_size)
            chunk = chunk.flatten()
            chunks.append(chunk.copy())

            energy = _rms(chunk)
            if energy > peak_energy:
                peak_energy = energy

            if energy > dynamic_threshold:
                speech_started = True
                silent_count = 0
            elif speech_started:
                silent_count += 1
                if silent_count >= silent_limit:
                    print(f"🛑 Pause → stopped at {(i+1)*CHUNK_SEC:.1f}s")
                    break

    audio = np.concatenate(chunks) if chunks else np.zeros(chunk_size, dtype='float32')
    duration = len(audio) / SAMPLE_RATE
    print(f"📊 Recorded: {duration:.2f}s | Peak RMS: {peak_energy:.5f} | "
          f"Threshold: {dynamic_threshold:.5f} | Speech: {speech_started}")
    return audio


# ══════════════════════════════════════════════════════════════════════════════
#  CLEANING PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def clean_audio(raw: np.ndarray) -> np.ndarray:
    audio = raw.astype(np.float32)
    audio = _bandpass(audio, SAMPLE_RATE)
    audio = _noise_reduce(audio, SAMPLE_RATE)
    audio = _trim_silence(audio, SAMPLE_RATE)
    audio = _normalize(audio)

    duration = len(audio) / SAMPLE_RATE
    print(f"🧹 After cleaning: {duration:.2f}s")
    return audio


# ══════════════════════════════════════════════════════════════════════════════
#  TRANSCRIPTION
# ══════════════════════════════════════════════════════════════════════════════

_HALLUCINATIONS = {
    "", ".", "..", "...", "you", "bye", "bye.", "okay",
    "thank you", "thank you.", "thanks", "thanks.",
    "thanks for watching", "please subscribe", "subscribe",
}

def _safe_transcribe(tmp_path: str) -> str:
    """Try transcription with full params, fall back to minimal params."""
    base_kwargs = dict(language="en", task="transcribe", fp16=False)

    # Try with all quality params first
    try:
        result = whisper_model.transcribe(
            tmp_path,
            temperature=0.0,
            beam_size=5,
            no_speech_threshold=0.6,
            logprob_threshold=-1.0,
            condition_on_previous_text=False,
            **base_kwargs,
        )
        return result["text"].strip()
    except TypeError as e:
        print(f"⚠️  Full params failed ({e}) — retrying with minimal params")

    # Fallback: minimal params (works on any whisper version)
    result = whisper_model.transcribe(tmp_path, **base_kwargs)
    return result["text"].strip()


def transcribe(audio: np.ndarray) -> str:
    duration = len(audio) / SAMPLE_RATE
    if duration < MIN_SPEECH_SEC:
        print(f"⚠️  Audio too short ({duration:.2f}s) — skipping transcription")
        return ""

    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        tmp = f.name
    wav_write(tmp, SAMPLE_RATE, audio_int16)

    try:
        text = _safe_transcribe(tmp)
        print(f"🧠 Whisper raw output: {text!r}")

        clean = text.lower().rstrip(".!? ")
        if clean in _HALLUCINATIONS or len(text) < 2:
            print("⚠️  Looks like a hallucination — discarding")
            return ""

        return text
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        traceback.print_exc()
        raise
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def speech_to_text() -> str:
    raw   = record_until_silence()
    clean = clean_audio(raw)
    text  = transcribe(clean)
    print(f"✅ Final transcription: {text!r}")
    return text