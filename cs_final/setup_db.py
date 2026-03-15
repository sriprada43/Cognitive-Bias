"""setup_db.py — Initialize CognitiveShield SQLite database"""
import sqlite3, os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "data", "users.db")

def init_db():
    os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

        CREATE TABLE IF NOT EXISTS sessions (
            session_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            started_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at  TIMESTAMP,
            total_scenarios INTEGER DEFAULT 0,
            correct_count   INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id));

        CREATE TABLE IF NOT EXISTS responses (
            response_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    INTEGER NOT NULL,
            user_id       INTEGER NOT NULL,
            scenario_id   TEXT NOT NULL,
            bias_type     TEXT NOT NULL,
            difficulty    TEXT NOT NULL,
            user_choice   TEXT NOT NULL,
            fell_for      INTEGER NOT NULL,
            response_time REAL NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (user_id)    REFERENCES users(user_id));

        CREATE TABLE IF NOT EXISTS bias_scores (
            score_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            bias_type     TEXT NOT NULL,
            vulnerability REAL DEFAULT 0.0,
            attempts      INTEGER DEFAULT 0,
            falls         INTEGER DEFAULT 0,
            last_updated  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, bias_type),
            FOREIGN KEY (user_id) REFERENCES users(user_id));

        CREATE TABLE IF NOT EXISTS detections (
            detection_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER,
            input_text    TEXT NOT NULL,
            predicted_bias TEXT NOT NULL,
            confidence    REAL NOT NULL,
            top_biases    TEXT,
            mitre_id      TEXT,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database ready:", DB_PATH)
