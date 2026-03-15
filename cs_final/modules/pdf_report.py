"""modules/pdf_report.py — Generate PDF threat report using reportlab"""
import os
from datetime import datetime

def generate_pdf_report(report, output_path=None):
    # Get the directory where this module is located
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    if output_path is None:
        output_path = os.path.join(MODULE_DIR, "..", "data", "threat_report.pdf")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                         Table, TableStyle, HRFlowable, PageBreak)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        W, H = A4
        doc  = SimpleDocTemplate(output_path, pagesize=A4,
                                  leftMargin=2*cm, rightMargin=2*cm,
                                  topMargin=2*cm, bottomMargin=2*cm)

        # ── Colour palette ─────────────────────────────────────────────────
        C_DARK  = colors.HexColor('#0a0e1a')
        C_CARD  = colors.HexColor('#111827')
        C_CYAN  = colors.HexColor('#00d4ff')
        C_RED   = colors.HexColor('#ff4757')
        C_GREEN = colors.HexColor('#00ff88')
        C_GOLD  = colors.HexColor('#ffd32a')
        C_WHITE = colors.HexColor('#e8eaf6')
        C_MUTED = colors.HexColor('#8892a4')

        styles = getSampleStyleSheet()
        def S(name, **kw):
            return ParagraphStyle(name, parent=styles['Normal'], **kw)

        title_s  = S('T', fontSize=22, fontName='Helvetica-Bold', textColor=C_CYAN,  spaceAfter=4)
        sub_s    = S('S', fontSize=10, fontName='Helvetica',       textColor=C_MUTED, spaceAfter=12)
        h1_s     = S('H1',fontSize=12, fontName='Helvetica-Bold',  textColor=C_CYAN,  spaceBefore=14, spaceAfter=6)
        h2_s     = S('H2',fontSize=10, fontName='Helvetica-Bold',  textColor=C_GOLD,  spaceBefore=10, spaceAfter=4)
        body_s   = S('B', fontSize=9,  fontName='Helvetica',       textColor=C_WHITE, spaceAfter=4, leading=14)
        red_s    = S('R', fontSize=9,  fontName='Helvetica-Bold',  textColor=C_RED)
        green_s  = S('G', fontSize=9,  fontName='Helvetica-Bold',  textColor=C_GREEN)
        mono_s   = S('M', fontSize=8,  fontName='Courier',         textColor=C_CYAN)

        BIAS_ICONS = {'authority':'[AUTH]','urgency':'[URG]','scarcity':'[SCAR]',
                      'social_proof':'[SOC]','reciprocity':'[RECIP]','familiarity':'[FAM]','fear':'[FEAR]'}

        story = []
        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        username = report['username']
        score    = report['exploitability']
        rl       = report['risk_label']

        # ── Header ──────────────────────────────────────────────────────────
        score_color = C_RED if score>=50 else C_GOLD if score>=30 else C_GREEN
        story += [
            Paragraph("COGNITIVESHIELD", title_s),
            Paragraph("Threat Intelligence Report  |  Social Engineering Vulnerability Assessment", sub_s),
            HRFlowable(width='100%', thickness=1, color=C_CYAN, spaceAfter=10),
            Table([
                ['Subject:', username,  'Generated:', ts],
                ['Risk Level:', rl,     'Exploitability:', f"{score:.0f} / 100"],
                ['Sessions:', str(report['stats']['sessions']),
                 'Scenarios:', str(report['stats']['total_scenarios'])],
            ], colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm],
               style=TableStyle([
                   ('FONTNAME',  (0,0),(-1,-1),'Helvetica'),
                   ('FONTNAME',  (0,0),(0,-1),'Helvetica-Bold'),
                   ('FONTNAME',  (2,0),(2,-1),'Helvetica-Bold'),
                   ('FONTSIZE',  (0,0),(-1,-1),9),
                   ('TEXTCOLOR', (0,0),(-1,-1),C_WHITE),
                   ('TEXTCOLOR', (0,0),(0,-1),C_MUTED),
                   ('TEXTCOLOR', (2,0),(2,-1),C_MUTED),
                   ('BACKGROUND',(0,0),(-1,-1),C_CARD),
                   ('ROWBACKGROUNDS',(0,0),(-1,-1),[C_CARD, colors.HexColor('#0d1320')]),
                   ('BOX',(0,0),(-1,-1),0.5,C_CYAN),
                   ('INNERGRID',(0,0),(-1,-1),0.25,colors.HexColor('#1e2a3a')),
                   ('PADDING',(0,0),(-1,-1),6),
               ])),
            Spacer(1, 14),
        ]

        # ── Bias scores table ───────────────────────────────────────────────
        story.append(Paragraph("BIAS VULNERABILITY SCORES", h1_s))
        bias_order = ['authority','urgency','fear','scarcity','social_proof','reciprocity','familiarity']
        bs = report['bias_scores']
        rows = [['Bias Type','Vulnerability','Attempts','Fell For','Risk']]
        for b in bias_order:
            d    = bs.get(b,{})
            v    = d.get('vulnerability',0)
            risk = 'CRITICAL' if v>=70 else 'HIGH' if v>=50 else 'MEDIUM' if v>=30 else 'LOW'
            rows.append([f"{BIAS_ICONS.get(b,'')} {b.replace('_',' ').title()}",
                         f"{v:.0f}%", str(d.get('attempts',0)),
                         str(d.get('falls',0)), risk])
        story.append(Table(rows, colWidths=[5.5*cm,3.5*cm,2.5*cm,2.5*cm,3*cm],
            style=TableStyle([
                ('FONTNAME',  (0,0),(-1,0),'Helvetica-Bold'),
                ('FONTNAME',  (0,1),(-1,-1),'Helvetica'),
                ('FONTSIZE',  (0,0),(-1,-1),8.5),
                ('TEXTCOLOR', (0,0),(-1,0),C_CYAN),
                ('TEXTCOLOR', (0,1),(-1,-1),C_WHITE),
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0d1320')),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_CARD, colors.HexColor('#0d1320')]),
                ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#1e2a3a')),
                ('INNERGRID',(0,0),(-1,-1),0.25,colors.HexColor('#1e2a3a')),
                ('PADDING',(0,0),(-1,-1),6),
                ('ALIGN',(1,0),(-1,-1),'CENTER'),
            ])))
        story.append(Spacer(1,12))

        # ── Attack surface ──────────────────────────────────────────────────
        story.append(Paragraph("ATTACK SURFACE EXPOSURE", h1_s))
        surf = report['attack_surface']
        surf_rows = [['Attack Vector','Exposure Score','Risk Level']]
        for k,v in surf.items():
            risk = 'HIGH' if v>=60 else 'MEDIUM' if v>=35 else 'LOW'
            surf_rows.append([k.replace('_',' ').title(), f"{v:.0f}%", risk])
        story.append(Table(surf_rows, colWidths=[7*cm,5*cm,5*cm],
            style=TableStyle([
                ('FONTNAME',  (0,0),(-1,0),'Helvetica-Bold'),
                ('FONTNAME',  (0,1),(-1,-1),'Helvetica'),
                ('FONTSIZE',  (0,0),(-1,-1),8.5),
                ('TEXTCOLOR', (0,0),(-1,0),C_CYAN),
                ('TEXTCOLOR', (0,1),(-1,-1),C_WHITE),
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0d1320')),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_CARD,colors.HexColor('#0d1320')]),
                ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#1e2a3a')),
                ('INNERGRID',(0,0),(-1,-1),0.25,colors.HexColor('#1e2a3a')),
                ('PADDING',(0,0),(-1,-1),6),
                ('ALIGN',(1,0),(-1,-1),'CENTER'),
            ])))
        story.append(Spacer(1,12))

        # ── Attacker simulations ────────────────────────────────────────────
        if report['simulations']:
            story.append(PageBreak())
            story.append(Paragraph("ATTACKER SIMULATION — TOP EXPLOIT VECTORS", h1_s))
            for sim in report['simulations']:
                story += [
                    Paragraph(f"{BIAS_ICONS.get(sim['bias'],'')} {sim['bias'].replace('_',' ').upper()}  |  {sim['vulnerability']:.0f}% vulnerable  |  {sim['mitre_id']}", h2_s),
                    Paragraph(f"<b>Observation:</b> {sim['obs']}", body_s),
                    Paragraph(f"<b>Attack:</b> {sim['attack']}", body_s),
                    Paragraph("<b>Likely Vectors:</b>", body_s),
                ]
                for v in sim['vectors']:
                    story.append(Paragraph(f"  • {v}", body_s))
                story += [
                    Paragraph(f"<b>Potential Outcome:</b> {sim['outcome']}", red_s),
                    HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#1e2a3a'), spaceAfter=8),
                ]

        # ── MITRE ATT&CK ────────────────────────────────────────────────────
        story.append(Paragraph("MITRE ATT&CK MAPPING", h1_s))
        mitre_data = {
            'authority':('Spear Phishing via Service','T1566.003'),
            'urgency':  ('Spear Phishing Link','T1566.002'),
            'fear':     ('Phishing for Information','T1598'),
            'familiarity':('Impersonation','T1656'),
            'social_proof':('Trusted Relationship','T1199'),
            'scarcity': ('Spear Phishing Attachment','T1566.001'),
            'reciprocity':('Establish Accounts','T1585'),
        }
        m_rows = [['Bias','Technique','ID','Exposure']]
        for b,(tname,tid) in mitre_data.items():
            v = bs.get(b,{}).get('vulnerability',0)
            m_rows.append([b.replace('_',' ').title(), tname, tid, f"{v:.0f}%"])
        story.append(Table(m_rows, colWidths=[4*cm,6.5*cm,3*cm,3.5*cm],
            style=TableStyle([
                ('FONTNAME',  (0,0),(-1,0),'Helvetica-Bold'),
                ('FONTNAME',  (0,1),(-1,-1),'Helvetica'),
                ('FONTSIZE',  (0,0),(-1,-1),8.5),
                ('TEXTCOLOR', (0,0),(-1,0),C_CYAN),
                ('TEXTCOLOR', (0,1),(-1,-1),C_WHITE),
                ('TEXTCOLOR', (2,1),(2,-1),C_CYAN),
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0d1320')),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_CARD,colors.HexColor('#0d1320')]),
                ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#1e2a3a')),
                ('INNERGRID',(0,0),(-1,-1),0.25,colors.HexColor('#1e2a3a')),
                ('PADDING',(0,0),(-1,-1),6),
                ('ALIGN',(2,0),(-1,-1),'CENTER'),
            ])))
        story.append(Spacer(1,12))

        # ── Recommendations ─────────────────────────────────────────────────
        if report['recommendations']:
            story.append(Paragraph("REMEDIATION RECOMMENDATIONS", h1_s))
            for bias, rec in report['recommendations']:
                story += [
                    Paragraph(f"{BIAS_ICONS.get(bias,'')} {bias.replace('_',' ').upper()}", h2_s),
                    Paragraph(rec, body_s),
                ]

        # ── Footer ──────────────────────────────────────────────────────────
        story += [
            Spacer(1,20),
            HRFlowable(width='100%', thickness=1, color=C_CYAN),
            Spacer(1,6),
            Paragraph(f"CognitiveShield  |  Generated {ts}  |  Confidential — For Security Training Purposes Only",
                      S('F', fontSize=7, textColor=C_MUTED, alignment=TA_CENTER)),
        ]

        doc.build(story)
        return output_path

    except ImportError:
        return None

def reportlab_available():
    try:
        import reportlab
        return True
    except ImportError:
        return False
