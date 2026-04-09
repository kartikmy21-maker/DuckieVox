import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import pyttsx3
import numpy as np
import noisereduce as nr

model = whisper.load_model("base")

engine = pyttsx3.init('sapi5')  

def record_audio(filename="input.wav", duration=3, fs=16000):
    print("🎤 Listening...")

    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    audio = recording.flatten()

    # 🔥 noise reduction
    reduced = nr.reduce_noise(y=audio, sr=fs)

    reduced = reduced / np.max(np.abs(reduced))

    write(filename, fs, reduced)

def speech_to_text():
    record_audio()

    result = model.transcribe("input.wav", language='en')
    text = result["text"].strip().lower()

    print("🧪 Heard:", text)

    return text

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()