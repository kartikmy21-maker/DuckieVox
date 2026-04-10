import os
import sys

# Add current directory to path so we can import voice
sys.path.append(os.getcwd())

try:
    import voice
    import numpy as np
    
    print("Testing Vosk Initialization...")
    if voice._HAS_VOSK and voice._vosk_rec:
        print("Vosk engine initialized successfully.")
        
        # Test a dummy audio chunk (silent/noise)
        dummy_audio = np.zeros(int(16000 * 1.5), dtype=np.float32)
        dummy_bytes = (dummy_audio * 32767).astype(np.int16).tobytes()
        
        voice._vosk_rec.AcceptWaveform(dummy_bytes)
        res = voice._vosk_rec.Result()
        print(f"Result for silence: {res}")
        
        # Test if is_wakeword works with expected variants
        test_words = ["duckie", "doki", "dogi", "the key"]
        for w in test_words:
            if voice.is_wakeword(w):
                print(f"is_wakeword matched core variant: {w}")
            else:
                print(f"is_wakeword failed to match: {w}")
    else:
        print("Vosk engine NOT initialized. Check logs above.")
        
except Exception as e:
    print(f"Verification failed with error: {e}")
    import traceback
    traceback.print_exc()
