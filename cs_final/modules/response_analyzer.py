"""modules/response_analyzer.py"""
import sqlite3, os
from datetime import datetime

# Get the directory where this module is located
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(MODULE_DIR, "..", "data", "users.db")

BIAS_TYPES = ['authority','urgency','scarcity','social_proof','reciprocity','familiarity','fear']
FELL_FOR   = {'1','comply','yes','click','sure','ok','okay','will do','done','confirm','provide','give','reset','verify','process'}

def get_or_create_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    conn.commit()
    c.execute("SELECT user_id FROM users WHERE username=?", (username,))
    uid = c.fetchone()[0]
    conn.close()
    return uid

def start_session(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (user_id) VALUES (?)", (user_id,))
    conn.commit()
    sid = c.lastrowid
    conn.close()
    return sid

def end_session(session_id, total, correct):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE sessions SET completed_at=?,total_scenarios=?,correct_count=? WHERE session_id=?",
              (datetime.now(), total, correct, session_id))
    conn.commit()
    conn.close()

def log_response(user_id, session_id, scenario, choice, response_time):
    fell = 1 if str(choice).strip().lower() in FELL_FOR else 0
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO responses(session_id,user_id,scenario_id,bias_type,difficulty,user_choice,fell_for,response_time) VALUES(?,?,?,?,?,?,?,?)",
              (session_id, user_id, scenario['scenario_id'], scenario['bias_type'],
               scenario['difficulty'], str(choice), fell, response_time))
    conn.commit()
    conn.close()
    _update_bias_score(user_id, scenario['bias_type'], fell)
    return fell

def _update_bias_score(user_id, bias_type, fell):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO bias_scores(user_id,bias_type,attempts,falls,vulnerability)
                 VALUES(?,?,1,?,?)
                 ON CONFLICT(user_id,bias_type) DO UPDATE SET
                   attempts=attempts+1, falls=falls+?,
                   vulnerability=CAST(falls+? AS REAL)/CAST(attempts+1 AS REAL),
                   last_updated=CURRENT_TIMESTAMP""",
              (user_id, bias_type, fell, float(fell), fell, fell))
    conn.commit()
    conn.close()

def log_detection(user_id, input_text, result):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    import json
    c.execute("INSERT INTO detections(user_id,input_text,predicted_bias,confidence,top_biases,mitre_id) VALUES(?,?,?,?,?,?)",
              (user_id, input_text[:2000], result['primary_bias'], result['confidence'],
               json.dumps(result['top_biases']), result['mitre_id']))
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*),SUM(fell_for),AVG(response_time) FROM responses WHERE user_id=?", (user_id,))
    row = c.fetchone()
    total, total_fell, avg_time = row[0] or 0, row[1] or 0, round(row[2] or 0, 1)

    c.execute("SELECT bias_type,vulnerability,attempts,falls FROM bias_scores WHERE user_id=? ORDER BY vulnerability DESC", (user_id,))
    bias_rows = c.fetchall()

    c.execute("SELECT COUNT(*) FROM sessions WHERE user_id=?", (user_id,))
    sessions = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM detections WHERE user_id=?", (user_id,))
    detections = c.fetchone()[0]
    conn.close()

    bias_scores = {b: {'vulnerability':0.0,'attempts':0,'falls':0} for b in BIAS_TYPES}
    for bias, vuln, attempts, falls in bias_rows:
        bias_scores[bias] = {'vulnerability': round(vuln*100,1), 'attempts': attempts, 'falls': falls}

    overall = round((total_fell/total*100) if total > 0 else 0, 1)
    return {
        'total_scenarios': total, 'total_fell': total_fell,
        'overall_vulnerability': overall, 'avg_response_time': avg_time,
        'sessions': sessions, 'detections': detections,
        'bias_scores': bias_scores
    }

def get_weakest_biases(user_id, top_n=3):
    stats = get_user_stats(user_id)
    sorted_b = sorted(stats['bias_scores'].items(), key=lambda x: x[1]['vulnerability'], reverse=True)
    return [(b, d['vulnerability']) for b, d in sorted_b[:top_n] if d['attempts'] > 0]
