"""modules/scenario_engine.py"""
import pandas as pd, random, sqlite3, os

# Get the directory where this module is located
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(MODULE_DIR, "..", "data", "bias_messages.csv")
DB_PATH   = os.path.join(MODULE_DIR, "..", "data", "users.db")

BIAS_TYPES = ['authority','urgency','scarcity','social_proof','reciprocity','familiarity','fear']

def _seen(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT scenario_id FROM responses WHERE user_id=?", (user_id,))
        seen = {r[0] for r in c.fetchall()}
        conn.close()
        return seen
    except: return set()

def _session_count(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sessions WHERE user_id=?", (user_id,))
        n = c.fetchone()[0]
        conn.close()
        return n
    except: return 0

def _weakest_bias(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT bias_type FROM bias_scores WHERE user_id=? ORDER BY vulnerability DESC LIMIT 1", (user_id,))
        r = c.fetchone()
        conn.close()
        return r[0] if r else None
    except: return None

def get_scenario(user_id, force_bias=None, force_difficulty=None):
    df   = pd.read_csv(DATA_PATH)
    seen = _seen(user_id)
    sc   = _session_count(user_id)

    diff = force_difficulty or (
        random.choice(['easy','medium']) if sc < 2 else
        random.choice(['medium','hard']) if sc < 4 else 'hard'
    )
    weakest = _weakest_bias(user_id)
    if force_bias:
        bias = force_bias
    elif weakest and sc >= 2 and random.random() < 0.7:
        bias = weakest
    else:
        bias = random.choice(BIAS_TYPES)

    pool = df[(df['bias_type']==bias) & (df['difficulty']==diff)]
    unseen = pool[~pool['scenario_id'].isin(seen)]
    if len(unseen) > 0:    row = unseen.sample(1).iloc[0]
    elif len(pool) > 0:    row = pool.sample(1).iloc[0]
    else:
        fb = df[~df['scenario_id'].isin(seen)]
        row = (fb if len(fb) > 0 else df).sample(1).iloc[0]
    return row.to_dict()
