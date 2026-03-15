"""app.py — CognitiveShield Flask Dashboard"""
import os, sys, json
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, send_file)

# Get the directory where this app is located
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

from setup_db import init_db
from modules.response_analyzer import (get_or_create_user, get_user_stats,
                                        start_session, end_session,
                                        log_response, log_detection)
from modules.profiler           import generate_report, get_risk_level
from modules.nlp_classifier     import (get_top_biases, full_analysis,
                                         train as train_clf,
                                         ollama_available, ollama_analyze)
from modules.scenario_engine    import get_scenario
from modules.adaptive_trainer   import (get_next_difficulty, get_personalized_tips,
                                         get_session_summary)
from modules.pdf_report         import generate_pdf_report, reportlab_available

app = Flask(__name__)
app.secret_key = 'cs-secret-2025'

SCENARIOS_PER_SESSION = 7
BIAS_ICONS = {'authority':'👔','urgency':'⏰','scarcity':'💎',
              'social_proof':'👥','reciprocity':'🎁','familiarity':'🤝','fear':'😨'}

# ── Boot ─────────────────────────────────────────────────────────────────────
init_db()
os.makedirs(os.path.join(APP_DIR, "models"), exist_ok=True)
os.makedirs(os.path.join(APP_DIR, "data"),   exist_ok=True)
if not os.path.exists(os.path.join(APP_DIR, "models", "bias_classifier.pkl")):
    print("Training NLP classifier...")
    train_clf(save=True)
    print("Classifier ready.")

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username','').strip() or 'trainee'
        user_id  = get_or_create_user(username)
        session['username'] = username
        session['user_id']  = user_id
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('index'))
    uid  = session['user_id']
    stats  = get_user_stats(uid)
    report = generate_report(session['username'], stats)
    tips   = get_personalized_tips(uid, top_n=3)
    has_ollama = ollama_available()
    return render_template('dashboard.html',
        username=session['username'], report=report, stats=stats,
        tips=tips, bias_icons=BIAS_ICONS, has_ollama=has_ollama,
        bias_order=['authority','urgency','fear','scarcity','social_proof','reciprocity','familiarity'])

# ── Training ──────────────────────────────────────────────────────────────────
@app.route('/train')
def train_session():
    if 'user_id' not in session: return redirect(url_for('index'))
    uid = session['user_id']
    session.update({'train_session_id': start_session(uid),
                    'train_results': [], 'train_index': 0})
    return redirect(url_for('train_scenario'))

@app.route('/train/scenario', methods=['GET','POST'])
def train_scenario():
    if 'user_id' not in session: return redirect(url_for('index'))
    uid = session['user_id']
    idx = session.get('train_index', 0)

    if request.method == 'POST':
        choice   = request.form.get('choice','3')
        rt       = float(request.form.get('rt', 5.0))
        scenario = session.get('current_scenario', {})
        if scenario:
            fell = log_response(uid, session['train_session_id'], scenario, choice, rt)
            res  = session.get('train_results', [])
            res.append({**scenario, 'fell_for':fell, 'choice':choice, 'rt':rt})
            session['train_results'] = res
            session['train_index']   = idx + 1
            return redirect(url_for('train_reveal', fell=int(fell)))

    if idx >= SCENARIOS_PER_SESSION:
        return redirect(url_for('train_summary'))

    scenario = get_scenario(uid)
    session['current_scenario'] = scenario
    return render_template('scenario.html', scenario=scenario,
        index=idx+1, total=SCENARIOS_PER_SESSION, bias_icons=BIAS_ICONS,
        channel_icons={'email':'📧','sms':'📱','phone':'📞','browser_popup':'🌐','slack':'💬'})

@app.route('/train/reveal')
def train_reveal():
    if 'user_id' not in session: return redirect(url_for('index'))
    fell    = request.args.get('fell','0') == '1'
    results = session.get('train_results', [])
    last    = results[-1] if results else {}
    idx     = session.get('train_index', 1)
    return render_template('reveal.html', scenario=last, fell=fell,
        index=idx, total=SCENARIOS_PER_SESSION, bias_icons=BIAS_ICONS,
        is_last=(idx >= SCENARIOS_PER_SESSION))

@app.route('/train/summary')
def train_summary():
    if 'user_id' not in session: return redirect(url_for('index'))
    results = session.get('train_results', [])
    sid     = session.get('train_session_id')
    correct = sum(1 for r in results if not r['fell_for'])
    if sid: end_session(sid, len(results), correct)
    summary = get_session_summary(results)
    tips    = get_personalized_tips(session['user_id'], top_n=2)
    return render_template('summary.html', summary=summary, tips=tips,
        bias_icons=BIAS_ICONS, username=session.get('username',''))

# ── Detection module ──────────────────────────────────────────────────────────
@app.route('/detect', methods=['GET','POST'])
def detect():
    if 'user_id' not in session: return redirect(url_for('index'))
    result = None
    ollama_result = None
    has_ollama = ollama_available()

    if request.method == 'POST':
        text = request.form.get('text','').strip()
        if text:
            result = full_analysis(text)
            log_detection(session['user_id'], text, result)
            if has_ollama and request.form.get('use_ollama'):
                ollama_result = ollama_analyze(text)

    return render_template('detect.html', result=result,
        ollama_result=ollama_result, has_ollama=has_ollama,
        bias_icons=BIAS_ICONS)

@app.route('/detect/api', methods=['POST'])
def detect_api():
    """JSON API endpoint for detection."""
    if 'user_id' not in session: return jsonify({'error':'not authenticated'}), 401
    data = request.get_json()
    text = (data or {}).get('text','').strip()
    if not text: return jsonify({'error':'no text'}), 400
    result = full_analysis(text)
    log_detection(session['user_id'], text, result)
    return jsonify(result)

# ── Reports ───────────────────────────────────────────────────────────────────
@app.route('/report')
def threat_report():
    if 'user_id' not in session: return redirect(url_for('index'))
    stats  = get_user_stats(session['user_id'])
    report = generate_report(session['username'], stats)
    return render_template('report.html', report=report,
        username=session['username'], bias_icons=BIAS_ICONS)

@app.route('/report/pdf')
def download_pdf():
    if 'user_id' not in session: return redirect(url_for('index'))
    if not reportlab_available():
        return "reportlab not installed. Run: pip install reportlab", 400
    stats  = get_user_stats(session['user_id'])
    report = generate_report(session['username'], stats)
    path   = generate_pdf_report(report, os.path.join(APP_DIR, "data", f"{session['username']}_report.pdf"))
    if not path: return "PDF generation failed", 500
    return send_file(path, as_attachment=True,
                     download_name=f"CognitiveShield_{session['username']}_ThreatReport.pdf")

# ── Settings ─────────────────────────────────────────────────────────────────
@app.route('/settings')
def settings():
    if 'user_id' not in session: return redirect(url_for('index'))
    return render_template('settings.html',
        username=session['username'],
        has_ollama=ollama_available(),
        has_reportlab=reportlab_available())

@app.route('/settings/retrain', methods=['POST'])
def retrain():
    if 'user_id' not in session: return redirect(url_for('index'))
    _, acc, _ = train_clf(save=True)
    return jsonify({'accuracy': acc})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
