import sqlite3
# The name of Duckie's database file
DB_NAME = "duckie_brain.db"

def setup_database():
    """Job 1: Create the storage box if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Create a table called 'memories' with two columns: item_name and item_detail
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            item_name TEXT PRIMARY KEY, 
            item_detail TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Database ready!")

def save_info(key, value):
    """Job 2: Put a memory into the box."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Insert or Update the information
    cursor.execute('INSERT OR REPLACE INTO memories VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()
    print(f"Memory Saved: {key}")

def get_info(key):
    """Job 3: Take a memory out of the box."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT item_detail FROM memories WHERE item_name = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    # If the memory exists, return it. If not, return "None".
    return result[0] if result else "None"

# This runs the setup automatically if you play this file
if __name__ == "__main__":
    setup_database()