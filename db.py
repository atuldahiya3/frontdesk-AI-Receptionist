import sqlite3

def init_db():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS help_requests
                 (id INTEGER PRIMARY KEY,
                  question TEXT,
                  caller_id TEXT,
                  status TEXT,
                  answer TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  resolved_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge
                 (id INTEGER PRIMARY KEY,
                  question TEXT UNIQUE,
                  answer TEXT)''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()