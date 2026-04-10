import sqlite3
import os

# The name of Duckie's database file
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "duckie_brain.db")


def setup_database():
    """Create all tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # General key-value memories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            item_name TEXT PRIMARY KEY,
            item_detail TEXT
        )
    ''')

    # 🗂️ File path memory — remembers where Duckie found every file
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_paths (
            nickname TEXT PRIMARY KEY,
            full_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            last_opened TEXT DEFAULT (datetime('now'))
        )
    ''')

    # 🧠 Personal facts — names, professions, preferences, anything the user shares
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_facts (
            fact_key   TEXT PRIMARY KEY,   -- e.g. "name", "profession", "hobby"
            fact_value TEXT NOT NULL,      -- e.g. "Ritul", "developer", "gaming"
            updated_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    conn.commit()
    conn.close()
    print("Database ready!")


# ─── General memory ───────────────────────────────────────────────────────────

def save_info(key, value):
    """Store a general key-value memory."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO memories VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()
    print(f"Memory Saved: {key}")


# ─── Personal facts ───────────────────────────────────────────────────────────

def save_fact(key, value):
    """
    Store a personal fact Duckie learned from the user.
    e.g. save_fact("name", "Ritul") or save_fact("profession", "developer")
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO personal_facts (fact_key, fact_value, updated_at)
        VALUES (?, ?, datetime('now'))
    ''', (key.lower().strip(), str(value).strip()))
    conn.commit()
    conn.close()
    print(f"🧠 Fact saved: {key} = {value}")


def get_fact(key):
    """Retrieve one specific fact. Returns the value string or None."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT fact_value FROM personal_facts WHERE fact_key = ?',
                   (key.lower().strip(),))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_all_facts():
    """
    Return all known personal facts as a readable string block.
    Used to inject context into the AI prompt.
    e.g. "name: Ritul | profession: developer | hobby: gaming"
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT fact_key, fact_value FROM personal_facts ORDER BY fact_key')
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return ""
    return " | ".join(f"{k}: {v}" for k, v in rows)


def get_info(key):
    """Retrieve a general key-value memory."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT item_detail FROM memories WHERE item_name = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


# ─── File path memory ─────────────────────────────────────────────────────────

def save_file_path(nickname, full_path):
    """
    Remember where a file lives.
    nickname = what the user searched (e.g. "dune", "me")
    full_path = absolute path on disk
    """
    if not full_path or not os.path.exists(full_path):
        return  # don't cache broken paths
    file_name = os.path.basename(full_path)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO file_paths (nickname, full_path, file_name, last_opened)
        VALUES (?, ?, ?, datetime('now'))
    ''', (nickname.lower().strip(), full_path, file_name))
    conn.commit()
    conn.close()
    print(f"📁 File path saved: {nickname} → {full_path}")


def get_file_path(nickname):
    """
    Exact lookup: was this nickname searched before?
    Returns full_path string or None.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT full_path FROM file_paths WHERE nickname = ?',
        (nickname.lower().strip(),)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def search_file_paths(partial):
    """
    Fuzzy lookup: find any saved file whose nickname OR filename contains 'partial'.
    Returns a list of (nickname, full_path, file_name) tuples.
    """
    partial = partial.lower().strip()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT nickname, full_path, file_name FROM file_paths
           WHERE nickname LIKE ? OR LOWER(file_name) LIKE ?
           ORDER BY last_opened DESC''',
        (f'%{partial}%', f'%{partial}%')
    )
    results = cursor.fetchall()
    conn.close()
    return results  # [(nickname, full_path, file_name), ...]


def forget_file_path(nickname):
    """Remove a stale cached path (called automatically when a path no longer exists)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM file_paths WHERE nickname = ?', (nickname.lower().strip(),))
    conn.commit()
    conn.close()


# ─── Auto-setup ───────────────────────────────────────────────────────────────
setup_database()

if __name__ == "__main__":
    print("Database initialised.")