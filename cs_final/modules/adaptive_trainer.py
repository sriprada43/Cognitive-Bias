"""modules/adaptive_trainer.py"""
import random
from modules.response_analyzer import get_user_stats, get_weakest_biases

TIPS = {
    'authority':    ["Verify authority requests through a separate, known channel before acting.",
                     "Legitimate authority figures never demand immediate action via email alone.",
                     "Check the actual sender domain — display names are trivially spoofed."],
    'urgency':      ["Urgency is the attacker's primary weapon. A 10-second pause protects you.",
                     "Ask: would this organisation actually lock me out in 2 hours? Usually no.",
                     "Legitimate systems send reminders well in advance, not last-minute panics."],
    'scarcity':     ["Scarcity is artificial. Verify offers directly on official platforms.",
                     "If a spot is truly limited, the official platform will reflect it.",
                     "FOMO is a feeling, not a fact. Breathe before clicking."],
    'social_proof': ["Peer compliance can be fabricated. Verify org-wide changes through intranet.",
                     "Just because everyone else did it does not make the request legitimate.",
                     "Attackers research your org structure — a familiar name proves nothing."],
    'reciprocity':  ["Unsolicited benefits are manipulation tools.",
                     "Never provide payment or credential info to claim an unexpected reward.",
                     "Log into your account directly to verify any credits or upgrades."],
    'familiarity':  ["Attackers use LinkedIn and company websites to fake familiarity.",
                     "A reference to a real colleague does not authenticate a message.",
                     "Always verify through a known direct contact method, not the suspicious one."],
    'fear':         ["Fear shuts down rational thinking — that is exactly what the attacker wants.",
                     "Legitimate organisations do not threaten arrest or suspension via email.",
                     "When threatened, always verify through official channels before acting."],
}

def get_next_difficulty(user_id):
    stats = get_user_stats(user_id)
    s, o  = stats['sessions'], stats['overall_vulnerability']
    if s == 0: return 'easy'
    if s < 2:  return 'medium' if o < 50 else 'easy'
    if s < 4:  return 'hard'   if o < 40 else 'medium'
    return 'hard'

def get_personalized_tips(user_id, top_n=3):
    weakest = get_weakest_biases(user_id, top_n)
    return [{'bias':b,'vulnerability':v,'tip':random.choice(TIPS.get(b,['Stay vigilant.']))}
            for b, v in weakest]

def get_session_summary(results):
    total   = len(results)
    fell    = sum(1 for r in results if r['fell_for'])
    correct = total - fell
    score   = round(correct/total*100 if total else 0)
    bp = {}
    for r in results:
        b = r['bias_type']
        if b not in bp: bp[b] = {'total':0,'fell':0}
        bp[b]['total'] += 1; bp[b]['fell'] += r['fell_for']
    worst = max(bp.items(), key=lambda x: x[1]['fell']/max(x[1]['total'],1))[0] if bp else None
    grade = 'A' if score>=90 else 'B' if score>=75 else 'C' if score>=60 else 'D' if score>=40 else 'F'
    return {'total':total,'correct':correct,'fell':fell,'score':score,'grade':grade,
            'bias_performance':bp,'worst_bias':worst}
