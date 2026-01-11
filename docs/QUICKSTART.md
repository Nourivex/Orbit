# Quick Start Guide — ORBIT MVP v0.1

## Prerequisites
- Python 3.11+ dengan venv
- Node.js 18+ dan npm
- Windows 10/11 (untuk Windows API support)

## Installation

### 1. Setup Backend
```powershell
# Navigate to ORBIT directory
cd H:\AiProject\ORBIT

# Activate Python virtual environment
cd backend
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt
```

### 2. Setup Frontend
```powershell
# Navigate to frontend directory
cd ..\frontend

# Install npm dependencies (if not already installed)
npm install
```

## Running ORBIT

### Terminal 1 — Backend
```powershell
# Activate venv
cd backend
.\venv\Scripts\Activate.ps1

# Run orchestrator
cd ..
python main_v2.py
```

**Expected Output:**
```
🚀 Starting ORBIT Agent - Luna v0.1
✅ IPC Server started on ws://localhost:8765
✅ Context monitoring started
🔄 Entering main orchestration loop
```

### Terminal 2 — Frontend
```powershell
# Navigate to frontend
cd frontend

# Start Vite dev server
npm run dev
```

**Expected Output:**
```
  VITE v6.0.5  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## Testing ORBIT

1. **Open browser** → Navigate to `http://localhost:5173/`
2. **Check console** → Should see: `✅ Connected to ORBIT backend`
3. **Wait 10-15 seconds** → Backend will detect idle time
4. **Luna appears** → Floating widget dengan bubble chat
5. **Test actions** → Click `Ya`, `Nanti`, or `Dismiss`

## Expected Behavior

### Luna States:
- **Idle** (🤖) — Default, observing silently
- **Observing** (👀) — Monitoring with pulse animation
- **Suggesting** (🌟) — Shows bubble chat with recommendations
- **Executing** (⚙️) — Processing user request (spinning)
- **Suppressed** — Hidden after dismiss (10 min cooldown)

### Sample Scenario:
```
1. You open VSCode
2. Luna observes (idle → observing)
3. After 5min idle, Luna suggests help (observing → suggesting)
4. Bubble appears: "Kamu idle 5 menit, mau aku rangkum progress hari ini?"
5. User clicks "Ya" → Luna executes
6. User clicks "Dismiss" → Luna suppressed for 10min
```

## Configuration

Edit `config/orbit_config.json` to customize:
```json
{
  "ai_mode": "dummy",           // "dummy" or "ollama"
  "polling_interval": 10,       // Seconds between checks
  "behavior": {
    "cooldown_per_intent": 180, // 3 minutes
    "cooldown_global": 60,      // 1 minute
    "cooldown_dismiss": 600     // 10 minutes
  },
  "ui": {
    "position": "bottom-right",
    "opacity": 0.95,
    "animation_speed": "normal"
  }
}
```

## Troubleshooting

### Backend not starting
```powershell
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r backend/requirements.txt --force-reinstall
```

### Frontend not connecting
```powershell
# Check if backend IPC server is running
# Should see: "✅ IPC Server started on ws://localhost:8765"

# Check WebSocket in browser console
# Should NOT see connection errors
```

### No Luna widget appearing
1. Check browser console for errors
2. Verify WebSocket connection (green ✅ in console)
3. Wait longer (dummy mode triggers at 5min idle)
4. Check backend logs for intent generation

## Development Commands

### Backend Testing
```powershell
cd backend
python -m pytest test_layer0.py -v
python -m pytest test_layer2_3.py -v
python -m pytest test_integration.py -v
```

### Frontend Development
```powershell
cd frontend
npm run dev      # Start dev server with HMR
npm run build    # Build for production
npm run preview  # Preview production build
```

## Architecture Quick Reference

```
Layer 0 (Context Hub)    → Collects system context (apps, idle, files)
        ↓
Layer 1 (AI Brain)       → Generates intents (suggest_help, remind, info)
        ↓
Layer 2 (Decision Engine)→ Approves/rejects based on confidence & cooldowns
        ↓
Layer 3 (Behavior FSM)   → Manages state transitions (idle → suggesting)
        ↓
Layer 4 (Frontend UI)    → Renders Luna widget & bubble chat
```

## Next Steps After MVP
1. Add voice output (text-to-speech)
2. Implement action execution (actual help, not just logging)
3. Add system tray icon & settings panel
4. Package as standalone .exe (PyInstaller + Tauri)
5. Auto-start on Windows boot

---

**Version**: MVP v0.1  
**Author**: Luna (OrbitAgent)  
**Last Updated**: 11 Januari 2026
