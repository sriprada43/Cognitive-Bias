# 🛡️ CognitiveShield v2
### ML-Driven Social Engineering Defense Trainer | Purple Team Edition

---

## ⚡ Quick Start

```bash
pip install -r requirements.txt
python app.py
# → open http://localhost:5000
```

---

## 🆕 What's New in v2

| Feature | Description |
|---------|-------------|
| 🔬 **Detection Module** | Paste any text — NLP classifier identifies bias tactic + risk score + MITRE mapping |
| 📥 **PDF Export** | Download a full professional threat intelligence report as PDF |
| 🧠 **Ollama Support** | Optional local SLM (Mistral/Phi-3) for offline semantic analysis |
| 🎨 **Improved UI** | JetBrains Mono + Syne fonts, radar chart, better layouts |
| ⚙️ **Settings Page** | Retrain classifier, check integrations, view setup instructions |

---

## 🧠 Core Features

- **CLI Trainer** (`python cli.py`) — terminal training with adaptive difficulty
- **Flask Dashboard** — web UI with bias heatmaps, radar chart, session history
- **NLP Classifier** — TF-IDF + Logistic Regression, auto-trained on boot
- **ML Profiler** — exploitability score, attack surface mapping, per-bias vulnerability
- **Adaptive Engine** — targets your weakest bias, increases difficulty over sessions
- **MITRE ATT&CK** — every bias maps to a real technique ID

---

## 🏗️ Architecture

```
cognitiveshield/
├── app.py                    # Flask web app
├── cli.py                    # CLI trainer
├── setup_db.py               # DB initializer (auto-runs)
├── requirements.txt
├── data/
│   ├── bias_messages.csv     # 76 labeled attack scenarios
│   └── users.db              # SQLite (auto-created)
├── modules/
│   ├── nlp_classifier.py     # TF-IDF + LR + Ollama support
│   ├── scenario_engine.py    # Adaptive scenario selector
│   ├── response_analyzer.py  # Response logger + DB ops
│   ├── profiler.py           # ML exploitability engine
│   ├── adaptive_trainer.py   # Difficulty + tips engine
│   └── pdf_report.py         # PDF export via reportlab
├── models/
│   └── bias_classifier.pkl   # Saved model (auto-trained)
└── templates/                # Flask HTML templates
```

---

## 🔬 Ollama Local SLM Setup (Optional)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model
ollama pull mistral        # ~4GB, best quality
ollama pull phi3           # ~2GB, faster

# 3. Start server (usually auto-starts)
ollama serve

# 4. CognitiveShield auto-detects it at localhost:11434
```


---

## 📚 Key References

1. "Exploring Heuristics and Biases in Cybersecurity" — MDPI Systems (2025)
2. "Classification of Manipulation Techniques in SE Attacks" — HAL / Thcon25 (2025)
3. "Human Vulnerabilities in Cybersecurity + AI/ML Countermeasures" — JST (2024)
4. "Cognitive Biases in Cyber Attacker Decision Making" — IEEE EuroS&PW (2025)
5. MITRE ATT&CK Framework — https://attack.mitre.org
