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

### PHASE 2: AI Brain Upgrade (Hybrid Logic) 🧠 ✅ COMPLETE
**Status**: ✅ Delivered with critical bug fixes
**Tujuan**: Integrasi Ollama dengan graceful fallback ke Dummy mode

**Tasks:**
1. ✅ Install `ollama` Python library (`pip install ollama`)
2. ✅ Implement `OllamaClient` class di `ai_brain_v2.py`:
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
2. "none" - No action needed (user is focused)

⚠️ ALLOWED INTENTS (v0.2): suggest_help, none ONLY
(remind & info → v0.3)

Respond in JSON:
{
  "intent": "suggest_help",
  "confidence": 0.85,
  "reasoning": "User idle 5min in coding app, might be stuck",
  "message": "Kamu lagi stuck? Mau aku bantu debug atau cari solusi?"
}

⚠️ Field `reasoning` is strictly internal and never surfaced to UI or persisted.
Keep message in Bahasa Indonesia, casual tone, max 100 chars.
```

**Success Criteria:**
- ✅ Ollama responds dalam <5s or fallback ke Dummy
- ✅ No crashes jika Ollama mati
- ✅ Confidence scores realistis (0.7-0.95)
- ✅ Messages variatif dan context-aware (20+ pool)
- ✅ Gacha system dengan weighted random
- ✅ FSM bug fixed (IDLE → SUGGESTING)
- ✅ Balanced cooldown/spam filters

**Timeline**: 4 hours (actual: 3.5h + fixes)
**Commits**: 11 commits (87db38e...e3c634f)

---

### PHASE 3: Decision Engine Enhancement 🔧 ⏭️ DEFERRED
**Status**: ⏭️ Deferred to production hardening phase
**Tujuan**: Implementasi confidence decay dan user preference learning

**Rationale for Deferral**:
- ConfidenceDecay code already exists in decision_engine.py
- Not critical for MVP v0.2 user testing
- Better to gather real user data first before tuning decay
- Focus resources on Tauri (higher user value)

**Quick Enhancement (15min)**:
- Verify existing decay logic works
- Add basic stats endpoint
- Document for v0.3

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

### PHASE 4: Tauri Migration (The Body) 🖥️🟡 IN PROGRESS
**Status**: 🟡 Init complete, needs window config & testing
**Tujuan**: Convert web app → native desktop app dengan Tauri + Ghost Mode transparency

**Tasks:**

#### 1. Window Configuration (Ghost Mode)
   
   **Main Window Configuration** (`label: main`):
   - Konfigurasi untuk widget Luna yang transparan dan non-intrusive
   - Properties yang harus diset:
     ```json
     {
       "label": "main",
       "title": "ORBIT - Luna",
       "width": 400,
       "height": 500,
       "resizable": false,
       "transparent": true,          // Ghost mode: tembus pandang
       "decorations": false,         // No title bar/borders
       "alwaysOnTop": true,          // Stay above other windows
       "skipTaskbar": true,          // ❗ Tidak muncul di taskbar (akses via Tray)
       "visible": true,
       "focus": false,               // Tidak steal focus dari user
       "x": null,                    // Will be calculated dynamically
       "y": null
     }
     ```
   
   **Settings Window Configuration** (`label: settings`):
   - Window kedua untuk panel pengaturan ORBIT
   - Properties yang harus diset:
     ```json
     {
       "label": "settings",
       "title": "ORBIT Settings",
       "width": 600,
       "height": 700,
       "resizable": true,
       "transparent": false,         // Normal window
       "decorations": true,          // Has title bar (normal window)
       "alwaysOnTop": false,
       "skipTaskbar": false,         // Muncul di taskbar saat dibuka
       "visible": false,             // ❗ Default hidden (show on demand)
       "center": true
     }
     ```

#### 2. CSS Cleanup (Hapus Kotak Putih/Background)
   
   **Masalah**: Default CSS sering membuat background putih yang mengganggu transparency.
   
   **Solusi** - Refactor `frontend/src/index.css` & `App.css`:
   ```css
   /* index.css - Global reset untuk transparency */
   html, body, #root {
     margin: 0;
     padding: 0;
     background: transparent;      /* ❗ Kunci utama ghost mode */
     overflow: hidden;             /* No scrollbars */
     width: 100vw;
     height: 100vh;
   }
   
   body {
     font-family: 'Segoe UI', Tahoma, sans-serif;
     -webkit-font-smoothing: antialiased;
   }
   
   /* App.css - Container transparency */
   .App {
     background: transparent;       /* No white box */
     width: 100%;
     height: 100%;
     position: relative;
   }
   
   /* Pastikan hanya komponen Luna yang visible */
   .luna-container {
     /* Only this has background/styling */
   }
   ```

#### 3. System Tray & Context Menu
   
   **A. Rust-side System Tray** (`src-tauri/src/main.rs`):
   ```rust
   use tauri::{
     CustomMenuItem, SystemTray, SystemTrayMenu, SystemTrayEvent,
     Manager
   };
   
   fn main() {
     // Build system tray menu
     let show_hide = CustomMenuItem::new("toggle", "Show/Hide Luna");
     let settings = CustomMenuItem::new("settings", "Settings");
     let quit = CustomMenuItem::new("quit", "Quit");
     
     let tray_menu = SystemTrayMenu::new()
       .add_item(show_hide)
       .add_item(settings)
       .add_native_item(SystemTrayMenuItem::Separator)
       .add_item(quit);
     
     let system_tray = SystemTray::new().with_menu(tray_menu);
     
     tauri::Builder::default()
       .system_tray(system_tray)
       .on_system_tray_event(|app, event| match event {
         SystemTrayEvent::MenuItemClick { id, .. } => {
           match id.as_str() {
             "toggle" => {
               let window = app.get_window("main").unwrap();
               if window.is_visible().unwrap() {
                 window.hide().unwrap();
               } else {
                 window.show().unwrap();
               }
             }
             "settings" => {
               let settings_window = app.get_window("settings").unwrap();
               settings_window.show().unwrap();
               settings_window.set_focus().unwrap();
             }
             "quit" => {
               std::process::exit(0);
             }
             _ => {}
           }
         }
         _ => {}
       })
       .run(tauri::generate_context!())
       .expect("error while running tauri application");
   }
   ```
   
   **B. React Context Menu** (`LunaIcon.jsx`):
   ```jsx
   import { invoke } from '@tauri-apps/api/tauri';
   
   const LunaIcon = () => {
     const handleContextMenu = (e) => {
       e.preventDefault();
       
       // Option 1: Trigger Rust native menu
       invoke('show_context_menu');
       
       // Option 2: Show custom React menu
       // setShowMenu(true);
     };
     
     return (
       <div 
         className="luna-icon"
         onContextMenu={handleContextMenu}
       >
         {/* Luna mascot */}
       </div>
     );
   };
   ```

#### 4. Position Window to Bottom-Right
   
   Dynamically calculate window position saat startup:
   ```javascript
   // src/main.jsx or App.jsx
   import { appWindow } from '@tauri-apps/api/window';
   import { primaryMonitor } from '@tauri-apps/api/window';
   
   async function positionWindow() {
     const monitor = await primaryMonitor();
     const screenWidth = monitor.size.width;
     const screenHeight = monitor.size.height;
     
     await appWindow.setPosition({
       type: 'Physical',
       x: screenWidth - 420,   // 400px width + 20px margin
       y: screenHeight - 520   // 500px height + 20px margin
     });
   }
   
   // Call on app mount
   positionWindow();
   ```

#### 5. Backend Integration Strategy & Smart Dev Orchestration
   
   **A. MVP v0.2 Approach** (Simplified):
   - Keep Python backend as **separate process** (no sidecar bundling yet)
   - Benefits: Faster iteration, easier debugging
   - **Future (v0.3)**: Bundle Python as Tauri sidecar for single .exe distribution
   
   **B. Development Orchestration** (Kill-Switch Problem Fix):
   
   **Problem**: Saat Tauri dev window ditutup, terminal Python backend sering tertinggal nyala, menyebabkan:
   - Port conflict saat restart (address already in use)
   - Orphan processes memakan resource
   - Harus manual kill task via Task Manager
   
   **Solution**: Setup `concurrently` untuk coordinated process management
   
   **Implementation Steps**:
   
   1. **Install Dependency**:
      ```bash
      cd frontend
      npm install --save-dev concurrently
      ```
   
   2. **Port Configuration** (Standardisasi):
      
      **Frontend - Update `vite.config.js`**:
      ```javascript
      import { defineConfig } from 'vite'
      import react from '@vitejs/plugin-react'
      
      export default defineConfig({
        plugins: [react()],
        server: {
          port: 3000,           // ⚠️ Fixed port untuk konsistensi
          strictPort: true,     // Fail jika port sudah dipakai
        }
      })
      ```
      
      **Backend - Update `backend/ipc_server.py`**:
      ```python
      # IPC Server Configuration
      HOST = "localhost"
      PORT = 8012  # ⚠️ Fixed port (bukan 8765 lagi)
      
      async def main():
          server = await websockets.serve(handle_client, HOST, PORT)
          logger.info(f"IPC Server running on ws://{HOST}:{PORT}")
          await server.wait_closed()
      ```
      
      **Update Frontend IPC Bridge - `src/ipc/bridge.js`**:
      ```javascript
      const WS_URL = 'ws://localhost:8012';  // Match backend port
      ```
   
   3. **Update `package.json` Scripts**:
      ```json
      {
        "scripts": {
          "dev": "vite",
          "dev:backend": "cd ../backend && python ipc_server.py",
          "dev:orbit": "concurrently -k \"npm run dev:backend\" \"npm run tauri dev\"",
          "tauri": "tauri",
          "tauri:dev": "tauri dev",
          "build": "vite build",
          "tauri:build": "tauri build"
        }
      }
      ```
      
      **Key flags**:
      - `-k` atau `--kill-others`: Kill semua proses saat salah satu mati
      - `\"npm run dev:backend\"`: Start Python backend dulu
      - `\"npm run tauri dev\"`: Kemudian start Tauri (butuh Vite siap)
   
   4. **New Developer Workflow**:
      ```bash
      # Old way (MANUAL, RISKY):
      # Terminal 1: cd backend && python ipc_server.py
      # Terminal 2: cd frontend && npm run tauri dev
      # Problem: Harus manual kill keduanya
      
      # ✅ New way (ONE COMMAND):
      cd frontend
      npm run dev:orbit
      # Close Tauri window → Python backend otomatis mati juga!
      ```
   
   **Benefits**:
   - ✅ No more orphan Python processes
   - ✅ Port conflicts eliminated
   - ✅ Single command untuk start/stop semua
   - ✅ Konsisten dengan modern dev practices (Next.js, Remix style)

#### 6. Tauri Configuration Complete Example
   
   **Update `src-tauri/tauri.conf.json`**:
   ```json
   {
     "build": {
       "devPath": "http://localhost:3000",  // ⚠️ Match Vite port
       "distDir": "../dist"
     },
     "tauri": {
       "windows": [
         {
           "label": "main",
           "title": "ORBIT - Luna",
           "width": 400,
           "height": 150,           // ⚠️ Reduced height (widget, bukan full window)
           "resizable": false,
           "transparent": true,
           "decorations": false,
           "alwaysOnTop": true,
           "skipTaskbar": true,     // ⚠️ No taskbar clutter
           "visible": true,
           "focus": false
         },
         {
           "label": "settings",
           "title": "ORBIT Settings",
           "width": 600,
           "height": 700,
           "resizable": true,
           "transparent": false,
           "decorations": true,
           "alwaysOnTop": false,
           "skipTaskbar": false,
           "visible": false,
           "center": true
         }
       ],
       "systemTray": {
         "iconPath": "icons/tray-icon.png",
         "iconAsTemplate": true
       },
       "allowlist": {
         "all": false,
         "window": {
           "all": true,
           "setPosition": true,
           "setSize": true,
           "show": true,
           "hide": true,
           "setFocus": true
         }
       }
     }
   }
   ```

#### 7. Build & Testing
   
   ```bash
   # ✅ NEW: Orchestrated development (RECOMMENDED)
   cd frontend
   npm run dev:orbit    # Starts backend + Tauri in one command
   
   # Old: Manual development (still works, but tedious)
   # Terminal 1: cd backend && python ipc_server.py
   # Terminal 2: cd frontend && npm run tauri dev
   
   # Production build
   npm run tauri:build
   # Output: src-tauri/target/release/bundle/
   ```

**Success Criteria:**
- ✅ Main window transparent dengan Luna floating di pojok kanan bawah (400x150px)
- ✅ Always-on-top berfungsi (tidak tertutup window lain)
- ✅ Tidak ada taskbar button untuk main window (skipTaskbar: true)
- ✅ System Tray icon muncul dengan menu "Show/Hide", "Settings", "Quit"
- ✅ Klik kiri tray icon: Toggle visibility Luna widget
- ✅ Klik kanan tray icon: Buka context menu
- ✅ Right-click pada Luna menampilkan context menu
- ✅ Settings window dapat dibuka dan tertutup dengan normal
- ✅ Background 100% transparan (no white box)
- ✅ Click-through pada area kosong, interactive di Luna widget
- ✅ **DX**: `npm run dev:orbit` starts everything, close window kills all
- ✅ **DX**: Port conflicts tidak pernah terjadi (fixed ports: 3000, 8012)
- ✅ .exe build berhasil dan berjalan standalone

**Timeline**: 7 hours (updated: +1h untuk orchestration setup)

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

## ✅ Definition of Done — MVP v0.2

MVP v0.2 dianggap **COMPLETE** jika:
- ✅ ORBIT berjalan sebagai aplikasi desktop Tauri (.exe)
- ✅ AI Brain otomatis switch Ollama ↔ Dummy tanpa crash
- ✅ Suggestion (`suggest_help`) muncul tepat waktu & bisa di-dismiss
- ✅ Tidak ada UI muncul tanpa Decision Engine approval
- ✅ ORBIT dapat berjalan 30 menit tanpa memory leak
- ✅ Bubble timer auto-dismiss based on reading speed
- ✅ Intent types locked to `suggest_help` + `none` only

---

## 🛑 Kill Switch (Safety Feature)

**Motivation**: Penyelamat kalau user lagi meeting / fokus total.

**Implementation**:
- Global flag: `ORBIT_ENABLED=false` di `config/orbit_config.json`
- Jika `false`:
  - Context monitoring tetap berjalan (background)
  - AI Brain & Decision Engine **disabled**
  - UI tidak pernah muncul
- Toggle via config file (manual edit untuk v0.2, UI toggle di v0.3)

**Usage**:
```json
{
  "orbit_enabled": false,  // ← Kill switch
  "ai_mode": "ollama",
  ...
}
```

---

## 🤖 Dummy Mode UX Rules

**Tujuan**: Supaya Dummy mode tidak terasa 'bodoh' atau annoying.

**Rules (Enforced in Code)**:
1. **Frequency Limit**: Tidak boleh muncul >1x dalam 15 menit
2. **Message Quality**: Harus netral & singkat (max 80 chars)
3. **No Repetition**: Tidak boleh mengulang kalimat yang sama 2x berturut-turut
4. **Context-Aware**: Pool harus punya minimum 15 variasi message

**Implementation**:
```python
class DummyModePool:
    def __init__(self):
        self.messages = [
            "Sudah 5 menit idle nih, butuh bantuan?",
            "Lagi nyangkut? Aku bisa bantu cari solusi",
            "Break dulu yuk, udah lama fokus",
            # ... 12 more variations
        ]
        self.last_message = None
        self.last_suggest_time = 0
    
    def get_message(self) -> str:
        # Filter out last message
        available = [m for m in self.messages if m != self.last_message]
        msg = random.choice(available)
        self.last_message = msg
        return msg
```

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
❌ **Intent types**: `remind` & `info` - **LOCKED OUT**, moved to v0.3  

**Scope Lock Rationale**:  
v0.2 fokus membuat `suggest_help` terasa **tepat waktu & manusiawi**.  
Ini bukan downgrade — ini **fokus**. Quality > Quantity.  

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
