from voice import speech_to_text, speak
from agent import decide_and_execute

def run_duckie():
    speak("Hello, I am Duckie")

    while True:
        input("\n👉 Press ENTER and speak...")

        command = speech_to_text()

        if not command:
            print("⚠️ No valid command")
            continue

        if "exit" in command:
            speak("Goodbye!")
            break

        response = decide_and_execute(command)

        print("Duckie:", response)
        speak(response)

if __name__ == "__main__":
    run_duckie()