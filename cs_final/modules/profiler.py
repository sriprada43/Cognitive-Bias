"""modules/profiler.py"""

BIAS_TYPES = ['authority','urgency','scarcity','social_proof','reciprocity','familiarity','fear']
BIAS_WEIGHTS = {'authority':0.20,'urgency':0.20,'fear':0.15,'scarcity':0.15,
                'social_proof':0.10,'reciprocity':0.10,'familiarity':0.10}
MITRE_MAP = {
    'authority':    ('Spear Phishing via Service','T1566.003'),
    'urgency':      ('Spear Phishing Link','T1566.002'),
    'fear':         ('Phishing for Information','T1598'),
    'familiarity':  ('Impersonation','T1656'),
    'social_proof': ('Trusted Relationship Abuse','T1199'),
    'scarcity':     ('Spear Phishing Attachment','T1566.001'),
    'reciprocity':  ('Establish Accounts','T1585'),
}
BIAS_TO_SURFACE = {
    'authority':    ['social_engineering','phishing'],
    'urgency':      ['phishing','account_takeover'],
    'scarcity':     ['phishing','social_engineering'],
    'social_proof': ['social_engineering','account_takeover'],
    'reciprocity':  ['identity_theft','phishing'],
    'familiarity':  ['social_engineering','identity_theft'],
    'fear':         ['account_takeover','identity_theft'],
}

def compute_exploitability(bias_scores):
    score = 0.0
    for bias, w in BIAS_WEIGHTS.items():
        v = bias_scores.get(bias,{}).get('vulnerability',0)/100.0
        score += v * w
    return round(score*100, 1)

def get_risk_level(score):
    if score >= 70: return ('CRITICAL','🔴')
    if score >= 50: return ('HIGH','🟠')
    if score >= 30: return ('MEDIUM','🟡')
    return ('LOW','🟢')

def compute_attack_surface(bias_scores):
    surfaces = {k:0.0 for k in ['identity_theft','social_engineering','phishing','account_takeover']}
    counts   = {k:0   for k in surfaces}
    for bias, surfs in BIAS_TO_SURFACE.items():
        v = bias_scores.get(bias,{}).get('vulnerability',0)/100.0
        for s in surfs:
            surfaces[s] += v; counts[s] += 1
    return {k: round((surfaces[k]/counts[k])*100,1) if counts[k] else 0 for k in surfaces}

EXPLOIT_TEMPLATES = {
    'authority':    {'obs':'Victim responds to authority figures without verification',
                     'attack':'Impersonate IT/HR/CEO via spoofed email',
                     'vectors':['Fake CEO wire transfer request','Fake IT helpdesk reset','Fraudulent HR compliance form'],
                     'outcome':'Credential theft or unauthorized wire transfer'},
    'urgency':      {'obs':'Victim makes fast decisions under time pressure',
                     'attack':'Create artificial deadlines to bypass critical thinking',
                     'vectors':['Fake account suspension notice','Countdown phishing link','Fake 2FA expiry SMS'],
                     'outcome':'Impulsive credential entry or malicious link click'},
    'scarcity':     {'obs':'Victim acts on limited-availability offers without verification',
                     'attack':'Fabricate exclusive or expiring access to trigger FOMO',
                     'vectors':['Fake training seat reservation','Expiring upgrade link','Limited compliance certificate'],
                     'outcome':'Malware download or credential phishing'},
    'social_proof': {'obs':'Victim complies when told peers have already done so',
                     'attack':'Use fabricated peer consensus to normalize malicious requests',
                     'vectors':['Fake team verification notice','Spoofed colleague NDA request','Fake org-wide tool install'],
                     'outcome':'Malicious software installation or credential submission'},
    'reciprocity':  {'obs':'Victim feels obligated to give information after receiving something',
                     'attack':'Gift a small benefit then request sensitive data',
                     'vectors':['Fake credit requiring payment confirmation','Free upgrade requiring re-verification','Fake referral bonus'],
                     'outcome':'Financial data theft or account takeover'},
    'familiarity':  {'obs':'Victim trusts messages referencing known people or past events',
                     'attack':'Use OSINT to craft highly targeted spear phishing',
                     'vectors':['Manager name-drop with malicious attachment','Fake helpdesk callback','LinkedIn-targeted job attachment'],
                     'outcome':'Malware execution or credential theft'},
    'fear':         {'obs':'Victim panics and acts without thinking when threatened',
                     'attack':'Use legal, financial, or reputational threats to force compliance',
                     'vectors':['Fake legal action notice','Dark web data exposure scare','Fake manager escalation'],
                     'outcome':'Ransom payment or credential submission'},
}

def generate_exploit_simulation(bias_scores):
    sims = []
    sorted_b = sorted([(b, bias_scores.get(b,{}).get('vulnerability',0)) for b in BIAS_TYPES],
                       key=lambda x: x[1], reverse=True)
    for bias, vuln in sorted_b[:3]:
        if vuln > 0 and bias in EXPLOIT_TEMPLATES:
            t = EXPLOIT_TEMPLATES[bias]
            mn, mi = MITRE_MAP.get(bias,('Unknown','N/A'))
            sims.append({'bias':bias,'vulnerability':vuln,'mitre_name':mn,'mitre_id':mi,**t})
    return sims

RECS = {
    'authority':    'Always verify authority requests through a secondary channel (phone call to known number).',
    'urgency':      'Pause before acting on urgent requests. Legitimate systems allow time to verify.',
    'scarcity':     'Treat scarcity-framed messages with skepticism. Verify offers through official portals.',
    'social_proof': 'Do not assume peer actions are real. Verify org-wide changes through official intranet.',
    'reciprocity':  'An unsolicited benefit is a manipulation tool. Never provide data to claim it.',
    'familiarity':  'Familiarity can be fabricated using OSINT. Verify senders independently.',
    'fear':         'Fear messages bypass rational thinking. Pause and verify through official channels.',
}

def generate_report(username, stats):
    bs  = stats['bias_scores']
    exp = compute_exploitability(bs)
    rl, ri = get_risk_level(exp)
    sims = generate_exploit_simulation(bs)
    recs = [(b,RECS[b]) for b,d in sorted(bs.items(),key=lambda x:x[1].get('vulnerability',0),reverse=True)
            if d.get('attempts',0)>0 and d.get('vulnerability',0)>20 and b in RECS]
    return {
        'username':username,'exploitability':exp,'risk_label':rl,'risk_icon':ri,
        'attack_surface':compute_attack_surface(bs),'simulations':sims,
        'recommendations':recs,'stats':stats,'bias_scores':bs,
    }
