"""
modules/nlp_classifier.py
TF-IDF + Logistic Regression bias classifier.
Optional: Ollama local SLM for richer analysis.
"""
import os, pickle, re, json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
import numpy as np

# Get the directory where this module is located
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODULE_DIR, "..", "models", "bias_classifier.pkl")
DATA_PATH  = os.path.join(MODULE_DIR, "..", "data", "bias_messages.csv")

BIAS_TYPES = ['authority','urgency','scarcity','social_proof',
              'reciprocity','familiarity','fear']

MITRE_MAP = {
    'authority':    ('Spear Phishing via Service', 'T1566.003'),
    'urgency':      ('Spear Phishing Link',        'T1566.002'),
    'fear':         ('Phishing for Information',   'T1598'),
    'familiarity':  ('Impersonation',              'T1656'),
    'social_proof': ('Trusted Relationship Abuse', 'T1199'),
    'scarcity':     ('Spear Phishing Attachment',  'T1566.001'),
    'reciprocity':  ('Establish Accounts',         'T1585'),
}

def preprocess(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def train(save=True):
    os.makedirs(os.path.join(MODULE_DIR, "..", "models"), exist_ok=True)
    os.makedirs(os.path.join(MODULE_DIR, "..", "data"), exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    df['clean'] = df['message_text'].apply(preprocess)
    X, y = df['clean'].tolist(), df['bias_type'].tolist()

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1,2), max_features=5000, sublinear_tf=True)),
        ('clf',   LogisticRegression(max_iter=1000, C=1.0, solver='lbfgs'))
    ])

    cv = cross_val_score(pipeline, X, y, cv=5, scoring='accuracy')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    pipeline.fit(X_train, y_train)
    report = classification_report(pipeline.predict(X_test), y_test, zero_division=0)

    if save:
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(pipeline, f)

    return pipeline, round(np.mean(cv)*100, 1), report

def load_model():
    if not os.path.exists(MODEL_PATH):
        m, _, _ = train()
        return m
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)

def predict(text, model=None):
    if model is None: model = load_model()
    clean = preprocess(text)
    bias  = model.predict([clean])[0]
    proba = model.predict_proba([clean])[0]
    conf  = round(float(proba[list(model.classes_).index(bias)]) * 100, 1)
    return bias, conf

def get_top_biases(text, model=None, top_n=4):
    if model is None: model = load_model()
    clean  = preprocess(text)
    proba  = model.predict_proba([clean])[0]
    ranked = sorted(zip(model.classes_, proba), key=lambda x: x[1], reverse=True)
    return [(b, round(p*100,1)) for b, p in ranked[:top_n]]

def full_analysis(text, model=None):
    """Full detection result with MITRE mapping."""
    top     = get_top_biases(text, model, top_n=4)
    primary = top[0][0]
    conf    = top[0][1]
    mitre_name, mitre_id = MITRE_MAP.get(primary, ('Unknown','N/A'))

    # Risk keywords count
    risk_keywords = ['urgent','immediate','verify','confirm','click','suspend',
                     'delete','expire','limited','threat','legal','arrest',
                     'password','credential','account','bank','transfer']
    lower = text.lower()
    kw_hits = [k for k in risk_keywords if k in lower]
    risk_score = min(100, len(kw_hits) * 12 + conf * 0.4)

    return {
        'text':        text,
        'primary_bias': primary,
        'confidence':   conf,
        'top_biases':   top,
        'mitre_name':   mitre_name,
        'mitre_id':     mitre_id,
        'risk_score':   round(risk_score, 1),
        'risk_keywords': kw_hits,
    }

# ── Ollama integration (optional local SLM) ──────────────────────────────────
def ollama_available():
    try:
        import urllib.request
        urllib.request.urlopen('http://localhost:11434/api/tags', timeout=2)
        return True
    except:
        return False

def ollama_analyze(text, model_name='mistral'):
    """Use local Ollama SLM for richer semantic analysis."""
    import urllib.request, json
    prompt = f"""You are a cybersecurity expert analyzing a message for social engineering tactics.

Message: "{text}"

Respond ONLY with valid JSON:
{{
  "bias_type": "one of: authority/urgency/scarcity/social_proof/reciprocity/familiarity/fear",
  "confidence": 0-100,
  "explanation": "one sentence why",
  "is_attack": true/false,
  "red_flags": ["flag1","flag2"]
}}"""

    payload = json.dumps({"model": model_name, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request('http://localhost:11434/api/generate',
                                  data=payload, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            raw  = resp.get('response','{}')
            clean = raw[raw.find('{'):raw.rfind('}')+1]
            return json.loads(clean)
    except:
        return None
