import sqlite3
from datetime import datetime

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
    initial_kb = [
        ("What are the opening hours?", "We are open from 9 AM to 6 PM, Monday to Saturday."),
        ("What services do you offer?", "We offer haircuts, hair coloring, styling, manicures, and pedicures."),
    ]
    try:
        c.executemany("INSERT OR IGNORE INTO knowledge (question, answer) VALUES (?, ?)", initial_kb)
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

def create_help_request(question, caller_id="customer1"):
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute("INSERT INTO help_requests (question, caller_id, status) VALUES (?, ?, 'pending')", (question, caller_id))
    conn.commit()
    request_id = c.lastrowid
    conn.close()
    return request_id

def get_pending_requests():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute("SELECT * FROM help_requests WHERE status = 'pending'")
    reqs = c.fetchall()
    conn.close()
    return reqs

def get_all_requests():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute("SELECT * FROM help_requests")
    reqs = c.fetchall()
    conn.close()
    return reqs

def resolve_request(request_id, answer, question):
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute("UPDATE help_requests SET status = 'resolved', answer = ?, resolved_at = CURRENT_TIMESTAMP WHERE id = ?", (answer, request_id))
    conn.commit()
    conn.close()
    add_to_kb(question, answer)

def add_to_kb(question, answer):
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO knowledge (question, answer) VALUES (?, ?)", (question, answer))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def load_kb():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute("SELECT question, answer FROM knowledge")
    kb = c.fetchall()
    conn.close()
    return "\n".join(f"Q: {q}\nA: {a}" for q, a in kb)

def is_timed_out(created_at):
    dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
    return (datetime.now() - dt).total_seconds() > 3600

if __name__ == "__main__":
    init_db()