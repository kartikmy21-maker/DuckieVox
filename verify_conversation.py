import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

import agent
import memory

def test_conversation():
    print("Testing Conversational Logic...")
    
    # 1. Clear history for clean test
    memory.clear_chat_history()
    
    # 2. Add a fact
    memory.save_fact("name", "Ritul")
    
    # 3. Test first interaction (Ask for greeting)
    print("\n--- Test 1: First Interaction ---")
    response1 = agent.decide_and_execute("hello")
    print(f"User: hello")
    print(f"Duckie: {response1}")
    
    # 4. Test continuity (Ask something that implies context)
    print("\n--- Test 2: Contextual Interaction ---")
    response2 = agent.decide_and_execute("how are you doing today?")
    print(f"User: how are you doing today?")
    print(f"Duckie: {response2}")
    
    # 5. Check if history is being saved
    history = memory.get_chat_history()
    print(f"\nSaved history count: {len(history)}")
    for msg in history:
        print(f"  [{msg['role']}]: {msg['content'][:50]}...")

if __name__ == "__main__":
    try:
        test_conversation()
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
