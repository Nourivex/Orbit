# RENCANA MVP v0.2 — ORBIT Evolution

**Status**: 🟡 In Progress  
**Version**: 0.2.0  
**Start Date**: 11 Januari 2026  
**Target Completion**: 18 Januari 2026 (1 minggu)  

---

## 🎯 Vision Statement

MVP v0.2 adalah evolusi dari v0.1 yang **fokus pada production-readiness**, **AI intelligence**, dan **native desktop experience**. Bukan lagi web app di browser, tapi **true desktop companion** dengan AI brain yang smart.

### Core Upgrades:
1. **🧠 Brain Upgrade**: Ollama LLM integration dengan graceful fallback
2. **🖥️ Body Upgrade**: Tauri desktop app (transparent, always-on-top)
3. **🎨 UI Polish**: Mascot + smart bubble timing + smooth animations

---

## 📐 Architecture Enhancements

```
┌─────────────────────────────────────────────────────┐
│   Layer 4 - Tauri Desktop App                       │
│   (Transparent Window, Always-on-Top, Native)       │
│   • Mascot mascot (bukan emoji lagi)               │
│   • Smart bubble timer (reading speed estimation)   │
│   • Click-through + Hover interaction               │
└────────────────┬────────────────────────────────────┘
                 │ IPC (ws://localhost:8765)
┌────────────────▼────────────────────────────────────┐
│   Layer 3 - Behavior FSM                            │
│   (Unchanged from v0.1)                             │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│   Layer 2 - Decision Engine (Enhanced)              │
│   • Confidence Decay Algorithm                      │
│   • User preference learning                        │
│   • Smart cooldown adjustment                       │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│   Layer 1 - AI Brain (UPGRADED)                     │
│   • OllamaClient with health check                  │
│   • Dynamic context-aware prompting                 │
│   • Variatif dummy responses pool                   │
│   • Automatic mode switching (Ollama ↔ Dummy)       │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│   Layer 0 - Context Hub                             │
│   (Unchanged from v0.1)                             │
└─────────────────────────────────────────────────────┘
```

---

## 📋 PHASE BREAKDOWN

### PHASE 1: Planning & Documentation ✅
**Tujuan**: Establish clear roadmap dan update tracking documents

**Tasks:**
1. ✅ Create `docs/RENCANA_v0.2.md` (this file)
2. ⏳ Update `docs/PROGRESS.md` to mark v0.2 start
3. ⏳ Commit: `docs: initialize MVP v0.2 planning`

**Deliverables:**
- RENCANA_v0.2.md dengan fase-fase jelas
- PROGRESS.md updated
- Git commit untuk documentation

**Timeline**: 30 minutes

---

### PHASE 2: AI Brain Upgrade (Hybrid Logic) 🧠
**Tujuan**: Integrasi Ollama dengan graceful fallback ke Dummy mode

**Tasks:**
1. Install `ollama` Python library (`pip install ollama`)
2. Implement `OllamaClient` class di `ai_brain.py`:
   ```python
   class OllamaClient:
       def __init__(self, model="llama3.2"):
           self.model = model
           self.available = False
           self.check_health()
       
       def check_health(self) -> bool:
           # Try to ping Ollama API
           # Return True if available, False if not
           pass
       
       def generate_intent(self, context) -> Intent:
           # Dynamic prompt based on context
           pass
   ```
3. Refactor `AIBrain` class:
   - Auto-detect Ollama availability on init
   - Switch mode dynamically if Ollama goes down
   - Add retry logic (1x) before fallback
4. Enhance Dummy mode:
   - Pool of 15+ variatif responses (tidak monoton)
   - Randomized confidence scores (0.70-0.90)
   - Context-aware dummy logic (lebih smart)
5. Testing:
   - Test Ollama ON → Should use AI responses
   - Test Ollama OFF → Should fallback to Dummy gracefully
   - Test Ollama RESTART → Should auto-recover

**Prompt Template (Ollama):**
```
You are Luna, a helpful AI desktop assistant observing user activity.

Current context:
- Active window: {active_app}
- Idle time: {idle_time} seconds
- Recent file changes: {file_changes}
- Time of day: {time_of_day}

Based on this context, decide on ONE action:
1. "suggest_help" - User might need assistance
2. "remind" - Gentle reminder about task/break
3. "info" - Interesting context-based insight
4. "none" - No action needed (user is focused)

Respond in JSON:
{
  "intent": "suggest_help",
  "confidence": 0.85,
  "reasoning": "User idle 5min in coding app, might be stuck",
  "message": "Kamu lagi stuck? Mau aku bantu debug atau cari solusi?"
}

Keep message in Bahasa Indonesia, casual tone, max 100 chars.
```

**Success Criteria:**
- Ollama responds dalam <5s or fallback ke Dummy
- No crashes jika Ollama mati
- Confidence scores realistis (0.7-0.95)
- Messages variatif dan context-aware

**Timeline**: 4 hours

---

### PHASE 3: Decision Engine Enhancement 🔧
**Tujuan**: Implementasi confidence decay dan user preference learning

**Tasks:**
1. Implement `ConfidenceDecay` class (sudah ada, enhance):
   ```python
   class ConfidenceDecayV2:
       def __init__(self):
           self.dismiss_history = {}  # intent_type -> dismiss_count
           self.accept_history = {}   # intent_type -> accept_count
       
       def apply_decay(self, intent: Intent) -> float:
           # Jika intent sering di-dismiss, kurangi confidence
           dismiss_count = self.dismiss_history.get(intent.type, 0)
           accept_count = self.accept_history.get(intent.type, 0)
           
           if dismiss_count > accept_count:
               decay_factor = 1 - (dismiss_count * 0.1)  # Max 50% decay
               return intent.confidence * max(decay_factor, 0.5)
           return intent.confidence
       
       def record_dismiss(self, intent_type: str):
           self.dismiss_history[intent_type] = self.dismiss_history.get(intent_type, 0) + 1
       
       def record_accept(self, intent_type: str):
           self.accept_history[intent_type] = self.accept_history.get(intent_type, 0) + 1
   ```
2. Integrate dengan `DecisionEngine.evaluate()`:
   - Apply decay sebelum confidence threshold check
   - Persist history ke SQLite (optional, for v0.3)
3. Add stats endpoint untuk monitoring decay values
4. Testing:
   - Dismiss "suggest_help" 3x → Confidence harus turun
   - Accept "info" 2x → Confidence harus stabil/naik

**Success Criteria:**
- User yang sering dismiss suatu intent akan jarang menerimanya
- Decay algorithm tidak terlalu agresif (max 50% reduction)
- History tracking berjalan stabil

**Timeline**: 2 hours

---

### PHASE 4: Tauri Migration (The Body) 🖥️
**Tujuan**: Convert web app → native desktop app dengan Tauri

**Tasks:**
1. **Setup Tauri**:
   ```bash
   cd frontend
   npm install @tauri-apps/cli@latest @tauri-apps/api@latest
   npm run tauri init
   ```
2. **Configure `src-tauri/tauri.conf.json`**:
   ```json
   {
     "build": {
       "devPath": "http://localhost:5173",
       "distDir": "../dist"
     },
     "tauri": {
       "windows": [
         {
           "title": "ORBIT - Luna",
           "width": 400,
           "height": 500,
           "resizable": false,
           "fullscreen": false,
           "transparent": true,
           "decorations": false,
           "alwaysOnTop": true,
           "skipTaskbar": true,
           "visible": true,
           "x": null,
           "y": null,
           "focus": false
         }
       ],
       "allowlist": {
         "all": false,
         "window": {
           "all": true,
           "setPosition": true,
           "setSize": true
         }
       }
     }
   }
   ```
3. **Update CSS untuk transparency**:
   - Set `background: transparent` di root
   - Handle click-through areas
4. **Position window to bottom-right**:
   ```javascript
   import { appWindow } from '@tauri-apps/api/window';
   
   appWindow.setPosition({
     type: 'Physical',
     x: screenWidth - 420,
     y: screenHeight - 520
   });
   ```
5. **Backend integration**:
   - Keep Python backend as separate process (no sidecar for MVP v0.2)
   - User runs both `start_backend.bat` + Tauri app
   - (Future: Bundle Python as sidecar in v0.3)
6. **Build testing**:
   ```bash
   npm run tauri dev   # Development mode
   npm run tauri build # Production .exe
   ```

**Success Criteria:**
- Tauri window transparent dengan Luna floating di pojok kanan bawah
- Always-on-top berfungsi (tidak tertutup window lain)
- Tidak ada taskbar button (skipTaskbar: true)
- Click-through pada area kosong, interactive di widget
- .exe build berhasil dan berjalan standalone

**Timeline**: 5 hours

---

### PHASE 5: UI/UX Refinement 🎨
**Tujuan**: Polish UI dengan mascot, smart timing, dan animations

**Tasks:**
1. **Mascot Mascot (Replace Emoji)**:
   - Design simple SVG mascot Luna (robot/AI character)
   - Alternativ: Find free mascot from Freepik/Flaticon
   - Replace `🤖🌟👀⚙️` dengan animated mascot
   - States: idle (neutral), observing (eyes follow), suggesting (excited), executing (working)
2. **Smart Bubble Timer**:
   ```javascript
   const calculateBubbleDuration = (text) => {
     const charCount = text.length;
     const readingSpeed = 15; // chars per second
     const baseDuration = 2000; // 2 seconds minimum
     
     return (charCount / readingSpeed) * 1000 + baseDuration;
   };
   
   // Auto-dismiss bubble after reading time
   useEffect(() => {
     if (bubble && visible) {
       const duration = calculateBubbleDuration(bubble.text);
       const timer = setTimeout(() => {
         setVisible(false);
       }, duration);
       return () => clearTimeout(timer);
     }
   }, [bubble, visible]);
   ```
3. **Enhanced Animations**:
   - Bubble: slide-in from right + fade
   - Mascot: subtle breathing animation (scale 1.0 ↔ 1.02)
   - Hover effect: mascot looks at cursor
   - Click effect: bounce animation
4. **Polish CSS**:
   - Smoother transitions (ease-in-out)
   - Better shadow/glow effects
   - Dark mode support (optional)
5. **Sound effects (optional)**:
   - Gentle "ding" saat bubble muncul
   - Soft click sound untuk user action
   - Toggle on/off via settings

**Success Criteria:**
- Mascot terlihat lebih hidup dan engaging
- Bubble auto-dismiss sesuai waktu baca
- Animations smooth (60fps)
- UI feels polished dan professional

**Timeline**: 4 hours

---

## 📊 Success Metrics (v0.2)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Ollama Response Time** | <5s | Latency log |
| **Fallback Success Rate** | 100% | Error handling test |
| **Confidence Decay Accuracy** | ±10% expected | User feedback |
| **Tauri Startup Time** | <3s | Performance profiling |
| **UI Frame Rate** | 60fps | DevTools performance |
| **Build Size** | <100MB | .exe file size |
| **Memory Usage** | <150MB | Task Manager |

---

## 🧪 Testing Strategy

### Unit Tests:
- `test_ollama_client.py` - Mock Ollama responses
- `test_confidence_decay.py` - Decay algorithm validation
- `test_smart_timer.js` - Bubble duration calculation

### Integration Tests:
- Ollama ON/OFF switching
- Confidence decay after 5 dismiss cycles
- Tauri ↔ Python IPC stability

### Manual Tests:
- User experience walkthrough (10-minute session)
- Visual polish review (screenshot comparison)
- Performance profiling (memory, CPU, GPU)

---

## 🔒 Non-Goals (Out of Scope v0.2)

❌ **Voice Output (TTS)** - Planned for v0.3  
❌ **Action Execution** - Planned for v0.3  
❌ **Settings Panel** - Planned for v0.3  
❌ **System Tray Icon** - Planned for v0.3  
❌ **Auto-start on Boot** - Planned for v0.3  
❌ **Multi-language Support** - Planned for v0.4  
❌ **Cloud Sync** - Planned for v1.0  

---

## 🚧 Known Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ollama tidak terinstall di user machine | HIGH | Graceful fallback + Dummy mode |
| Tauri build gagal di Windows | HIGH | Test build early, document dependencies |
| Transparent window flicker | MEDIUM | Use proper compositing, test on multiple GPUs |
| IPC latency tinggi | MEDIUM | Optimize message batching |
| Mascot loading lambat | LOW | Use SVG + preload assets |

---

## 📅 Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 (Planning) | 0.5 hours | None |
| Phase 2 (AI Brain) | 4 hours | Phase 1 |
| Phase 3 (Decision Engine) | 2 hours | Phase 2 |
| Phase 4 (Tauri) | 5 hours | Phase 1, 2, 3 |
| Phase 5 (UI/UX) | 4 hours | Phase 4 |
| **Total** | **15.5 hours** (~2 working days) | |

---

## 🎁 Deliverables (v0.2)

### Code:
- ✅ Enhanced `ai_brain.py` dengan OllamaClient
- ✅ Enhanced `decision_engine.py` dengan ConfidenceDecayV2
- ✅ Tauri configuration & build scripts
- ✅ Mascot SVG/PNG assets
- ✅ Smart bubble timer logic

### Documentation:
- ✅ RENCANA_v0.2.md (this file)
- ✅ Updated PROGRESS.md
- ✅ Tauri setup guide
- ✅ Ollama installation instructions

### Artifacts:
- ✅ Windows .exe build (ORBIT-Luna-v0.2.0-setup.exe)
- ✅ Updated README.md with v0.2 features
- ✅ Git tag: `v0.2.0`

---

## 🔮 Future Vision (v0.3 Preview)

v0.3 akan fokus pada **actionable intelligence**:
- Action execution (bukan cuma suggestion)
- System tray + settings panel
- Voice output (TTS dengan Bahasa Indonesia)
- Plugin architecture untuk extensibility
- Auto-start on boot

---

**Status**: 📝 Planning Complete, Ready for Execution  
**Next Step**: PHASE 2 (AI Brain Upgrade)  
**Owner**: Luna (OrbitAgent Senior Engineer Mode)  
**Approved**: ✅ Ready to Proceed

**Let's build ORBIT v0.2! 🚀**
