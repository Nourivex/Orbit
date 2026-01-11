# 🌟 ORBIT - Observant Robotic Behavioral Intelligence Tool

**Luna** — Your personal AI desktop assistant that observes, analyzes, and assists without interruption.

![Version](https://img.shields.io/badge/version-0.1.0--mvp-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## 🎯 What is ORBIT?

ORBIT is a **local-first**, **privacy-focused** desktop agent that:
- 👀 **Observes** your work context (active apps, idle time, file changes)
- 🧠 **Analyzes** patterns using AI (with LLM or rule-based logic)
- 💬 **Assists** at the right moment with helpful suggestions
- 🙅 **Respects** your focus (smart cooldowns, easy dismiss, focus mode)

**Luna**, ORBIT's personality, is designed to be **helpful but never intrusive**.

---

## ✨ Features

### Core Capabilities
- ✅ **Context-Aware Monitoring** — Tracks active apps, idle time, file changes
- ✅ **AI-Powered Insights** — Uses Ollama LLM or rule-based dummy mode
- ✅ **Smart Decision Engine** — Confidence thresholds, cooldowns, spam filtering
- ✅ **Behavior State Machine** — Manages when to show, hide, or stay silent
- ✅ **Floating Widget UI** — Non-intrusive bubble chat interface (React + Tauri)
- ✅ **Privacy-First** — 100% local, no cloud, no data collection

### Intelligent Behavior
- 🎯 Only suggests when contextually relevant
- ⏰ Respects cooldowns (per-intent, global, dismiss)
- 🚫 Anti-spam filters (max 5 popups/hour)
- 🧘 Focus mode (cooldown_global state)
- 📉 Confidence decay (learns from dismissals)

---

## 🏗️ Architecture

ORBIT uses a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│          Layer 4: Floating UI (React)       │  ← User Interface
├─────────────────────────────────────────────┤
│       Layer 3: Behavior FSM (States)        │  ← Personality & Timing
├─────────────────────────────────────────────┤
│     Layer 2: Decision Engine (Rules)        │  ← Approval Logic
├─────────────────────────────────────────────┤
│      Layer 1: AI Brain (LLM/Dummy)          │  ← Reasoning
├─────────────────────────────────────────────┤
│    Layer 0: Context Hub (Monitoring)        │  ← Sensors
└─────────────────────────────────────────────┘
```

**Principles:**
- **Behavior > Visual** — Smart timing beats fancy animations
- **Rule-based > LLM** — Reliable fallback without AI
- **Local-first** — Your data stays on your device
- **Non-intrusive** — Easy to ignore or dismiss

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) Ollama for LLM features

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/ORBIT.git
   cd ORBIT
   ```

2. **Setup backend:**
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # Windows
   pip install -r requirements.txt
   ```

3. **Setup frontend:**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Run ORBIT:**
   ```bash
   # From project root
   python main.py
   
   # Or with specific AI mode
   python main.py dummy    # Rule-based only
   python main.py ollama   # Force Ollama LLM
   python main.py auto     # Auto-detect (default)
   ```

---

## 🧪 Testing

### Run all tests:
```bash
cd backend

# Layer 0 (Context Hub)
python test_layer0.py

# Layers 2 & 3 (Decision + FSM)
python test_layer2_3.py

# Full integration
python test_integration.py
```

### Test results:
- ✅ Layer 0: 5/5 tests passed (0ms latency)
- ✅ Layers 2 & 3: 31/31 tests passed
- ✅ Integration: 4/4 scenarios validated

---

## ⚙️ Configuration

Edit `config/orbit_config.json`:

```json
{
  "ai_mode": "auto",              // auto, ollama, dummy
  "polling_interval": 10.0,       // seconds between checks
  "ai_model": "llama3.2",         // Ollama model name
  "behavior": {
    "per_intent_cooldown": 180,   // 3 minutes
    "global_cooldown": 60,        // 1 minute
    "dismiss_cooldown": 600,      // 10 minutes
    "max_popups_per_hour": 5
  },
  "features": {
    "auto_start": false,
    "focus_mode_hotkey": "Ctrl+Shift+F"
  }
}
```

---

## 📊 How It Works

### Example Flow:

1. **Layer 0** detects: *"User idle 5 min in VSCode"*
2. **Layer 1** analyzes: *"Possible stuck or break time"*
3. **Layer 2** evaluates: *"Confidence 0.85, cooldown passed"* ✅
4. **Layer 3** transitions: *idle → observing → suggesting*
5. **Layer 4** shows: *"Kamu idle 5 menit, mau aku rangkum?"*
6. User clicks **"Dismiss"**
7. **Cooldown activated** for 10 minutes

---

## 🎨 UI Modes

### States:
- **idle** — Hidden, waiting for context
- **observing** — Monitoring, icon visible
- **suggesting** — Bubble chat with actions
- **executing** — Processing user action
- **suppressed** — Cooldown after dismiss
- **cooldown_global** — Focus mode (silent)

---

## 🧠 AI Modes

### 1. Ollama Mode (LLM)
- Uses local Ollama server
- Model: llama3.2 or phi-3
- Timeout: 5 seconds
- Falls back to dummy if unavailable

### 2. Dummy Mode (Rule-based)
- No LLM required
- 4 built-in rules:
  - Long idle (5min) → suggest_help
  - Idle + errors → suggest_help
  - Many file changes → info
  - Short idle → remind

### 3. Auto Mode (Hybrid)
- Tries Ollama first
- Falls back to Dummy if needed
- **Recommended for testing**

---

## 📁 Project Structure

```
ORBIT/
├── backend/
│   ├── core/
│   │   ├── context_hub.py        # Layer 0
│   │   ├── ai_brain.py           # Layer 1
│   │   ├── decision_engine.py    # Layer 2
│   │   └── behavior_fsm.py       # Layer 3
│   ├── monitors/
│   │   ├── window_monitor.py
│   │   ├── idle_detector.py
│   │   └── file_watcher.py
│   ├── utils/
│   │   ├── db.py
│   │   └── logger.py
│   └── tests/
├── frontend/                      # React + Vite (Layer 4)
│   ├── src/
│   └── package.json
├── config/
│   └── orbit_config.json
├── docs/
│   ├── RENCANA.md
│   └── PROGRESS.md
├── main.py                        # Orchestrator
└── README.md
```

---

## 🔒 Privacy & Safety

- ✅ **100% local execution** — No cloud, no servers
- ✅ **No telemetry** — Zero data collection
- ✅ **Context limited** — Only basic app names, no content
- ✅ **User control** — Easy disable, pause, focus mode
- ✅ **No sensitive data** — Passwords/forms excluded

---

## 🛣️ Roadmap

### MVP v0.1 (Current)
- ✅ Core monitoring (Layer 0)
- ✅ AI reasoning (Layer 1)
- ✅ Decision logic (Layer 2)
- ✅ Behavior FSM (Layer 3)
- 🟡 Floating UI (Layer 4) — In progress
- 🟡 Full integration

### Future (Post-MVP)
- 🔮 Voice output (TTS)
- 🌐 Multi-language support
- 🔌 Plugin system
- 📱 Mobile companion app
- 🎨 Customizable avatars

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Submit a pull request

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details

---

## 👨‍💻 Author

**Luna (OrbitAgent)** — AI assistant personality  
**Created**: January 11, 2026

---

## 🙏 Acknowledgments

- Ollama for local LLM inference
- Tauri for lightweight desktop framework
- Python community for excellent libraries

---

**⭐ Star this repo if you find ORBIT helpful!**

*Built with ❤️ for developers who value focus and privacy*
