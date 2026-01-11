# RENCANA ORBIT MVP v0.1

## 🎯 Tujuan MVP
Membangun ORBIT (Observant Robotic Behavioral Intelligence Tool) sebagai desktop agent lokal yang dapat:
- Mengamati konteks aktivitas sistem secara pasif
- Memberikan saran berbasis konteks tanpa mengganggu
- Menampilkan UI floating widget dengan bubble chat
- Menghormati preferensi pengguna (dismiss & cooldown)

## 📋 Kriteria Sukses MVP
✅ Bisa mengamati active app + idle time  
✅ Bisa menghasilkan 1 jenis intent (suggest_help)  
✅ Bisa memutuskan muncul atau diam  
✅ Bisa menampilkan 1 bubble chat di widget  
✅ Bisa di-dismiss dan menghormati dismiss  

## ❌ Non-Goals MVP v0.1

Hal-hal berikut secara sengaja **TIDAK** termasuk dalam MVP:
- Voice input/output (TTS/STT)
- Automation execution kompleks
- Multi-monitor UI support
- Cloud sync atau login
- Plugin system
- 3D / animated avatar

**Fokus MVP**: Validasi behavior ORBIT, bukan fitur lanjutan.

## 🧭 Prinsip Desain ORBIT

- **Behavior > Visual** — Keputusan dan timing lebih penting dari animasi
- **Decision non-LLM > LLM** — Rule-based sebagai fondasi, AI sebagai enhancement
- **Non-intrusive by default** — User tidak terganggu, mudah di-ignore
- **Local-first & privacy-first** — Semua data tetap di device pengguna
- **Silent reasoning, explicit results** — Proses internal tidak ditampilkan

## 🔐 Privacy & Safety Principles

- ORBIT berjalan **100% lokal** (local-first)
- **Tidak ada data** yang dikirim ke cloud secara default
- Context data disimpan terbatas (ring buffer / capped history)
- User dapat **menonaktifkan monitoring** kapan saja
- ORBIT **tidak merekam input sensitif** (password, form secure)

---

## 🏗️ Rencana Implementasi Bertahap

### **PHASE 1 — Context & Event System (Layer 0)** ⏱️ 3-4 hari

#### Tujuan
Membangun fondasi monitoring sistem yang pasif dan efisien.

#### Komponen Utama
1. **Active Window Monitor**
   - Deteksi aplikasi aktif (process name & window title)
   - Polling interval: 2-5 detik
   - Platform: Windows (win32gui/psutil)

2. **Idle Time Detector**
   - Hitung waktu idle user
   - Threshold: 60s, 180s, 300s
   - Reset saat aktivitas keyboard/mouse

3. **File System Watcher**
   - Monitor perubahan file di workspace aktif
   - Events: create, modify, delete
   - Library: watchdog

4. **Error Log Collector**
   - Parse error logs dari aplikasi umum (VSCode, browser console)
   - Pattern matching untuk error signature
   - Store recent errors (max 10)

5. **Context Cache**
   - SQLite database untuk menyimpan history
   - Schema: `context_events (timestamp, app, event_type, data)`

#### Output Layer 0
```json
{
  "active_app": "Code.exe",
  "window_title": "main.py - VSCode",
  "idle_time": 45,
  "recent_file_changes": 2,
  "recent_errors": 1,
  "timestamp": "2026-01-11T10:30:00Z"
}
```

#### Task Breakdown
- [ ] Setup Python project structure
- [ ] Implementasi active window monitor
- [ ] Implementasi idle detector
- [ ] Implementasi file watcher (basic)
- [ ] Setup SQLite schema
- [ ] Testing context collection

---

### **PHASE 2 — Decision Engine (Layer 2)** ⏱️ 2 hari

#### Tujuan
Membangun rule-based system untuk memvalidasi apakah intent layak ditampilkan.

#### Komponen Utama
1. **Intent Validator**
   - Check confidence threshold >= 0.7
   - Priority scoring system
   - Intent types: suggest_help, remind, info

2. **Cooldown Manager**
   - Per-intent cooldown: 3-5 menit
   - Global cooldown: 1 menit
   - User dismiss cooldown: 10 menit

3. **Spam Filter**
   - Max popup per hour: 5
   - Same intent dalam 15 menit: ignore
   - Silent mode support

4. **Confidence Decay**
   - Confidence intent menurun jika:
     - Intent yang sama di-dismiss berulang
     - Context berubah signifikan
     - Waktu berlalu tanpa konfirmasi
   - Tujuan: mengurangi spam dan meningkatkan relevansi

#### Decision Rules
```python
IF confidence < 0.7: IGNORE
IF last_popup < 180s: IGNORE
IF user_dismissed_recently: IGNORE
IF same_intent < 900s: IGNORE
ELSE: APPROVE
```

#### Output Layer 2
```json
{
  "approved": true,
  "intent": "suggest_help",
  "reason": "confidence threshold met, cooldown passed",
  "next_allowed_time": "2026-01-11T10:35:00Z"
}
```

#### Task Breakdown
- [ ] Implementasi intent validator
- [ ] Implementasi cooldown manager
- [ ] Implementasi spam filter
- [ ] Rule engine dengan scoring
- [ ] Testing approval logic

---

### **PHASE 3 — Behavior FSM (Layer 3)** ⏱️ 2 hari

#### Tujuan
Mengelola state dan transisi perilaku ORBIT secara terstruktur.

#### State Diagram
```
   ┌──────┐
   │ idle │ ◄───────────┐
   └──┬───┘             │
      │ context change  │
      ▼                 │
┌────────────┐          │
│ observing  │          │
└────┬───────┘          │
     │ intent approved  │
     ▼                  │
┌────────────┐   user dismiss/timeout
│ suggesting │──────────┤
└────┬───────┘          │
     │ user action      │
     ▼                  │
┌────────────┐          │
│ executing  │──────────┘
└────────────┘
     │
     ▼
┌────────────┐
│ suppressed │ (cooldown)
└────────────┘
```

#### State Definitions
- **idle**: Tidak ada aktivitas, menunggu signal
- **observing**: Mengamati context, belum ada intent
- **suggesting**: Menampilkan bubble chat dengan saran
- **executing**: Menjalankan action yang dipilih user
- **suppressed**: Cooldown period setelah dismiss
- **cooldown_global**: Deep focus mode — ORBIT tidak menampilkan UI apapun kecuali kondisi kritis

#### Event Triggers
- `context_changed` → idle → observing
- `intent_approved` → observing → suggesting
- `user_dismiss` → suggesting → suppressed
- `user_action` → suggesting → executing
- `timeout` → suggesting → idle

#### Output ke UI (Layer 4)
```json
{
  "state": "suggesting",
  "emotion": "neutral",
  "bubble": {
    "text": "Kamu idle 5 menit, mau aku rangkum progress hari ini?",
    "actions": ["Ya", "Nanti", "Dismiss"]
  }
}
```

#### Task Breakdown
- [ ] Definisikan enum states
- [ ] Implementasi FSM class
- [ ] Mapping event → transitions
- [ ] State persistence
- [ ] Testing state transitions

---

### **PHASE 4 — AI Brain (Layer 1)** ⏱️ 2-3 hari

#### Tujuan
Integrasikan local LLM untuk menghasilkan insight dan intent proposal.

#### Komponen Utama
1. **LLM Integration (Ollama)**
   - Model: llama3.2 atau phi-3
   - Local inference only
   - Timeout: 5 detik max

2. **Prompt Engineering**
   - System prompt untuk ORBIT personality (Luna)
   - Context window: 2048 tokens
   - Output format: JSON structured intent

3. **Intent Generator**
   - Input: context snapshot (Layer 0)
   - Output: intent proposal + confidence
   - Types: suggest_help, remind, info

#### Prompt Template
```
Kamu adalah Luna, AI assistant untuk ORBIT.
Context saat ini:
- Active app: {app}
- Idle time: {idle}
- Recent errors: {errors}

Analisis apakah user butuh bantuan.
Output JSON:
{
  "intent": "suggest_help" | "remind" | "info" | "none",
  "confidence": 0.0-1.0,
  "message": "string",
  "reasoning": "string"
}
```

#### Output Layer 1
```json
{
  "intent": "suggest_help",
  "confidence": 0.82,
  "message": "Error ini mirip dengan kasus kemarin di file main.py",
  "reasoning": "User idle 5 menit setelah error, kemungkinan stuck"
}
```

⚠️ **Catatan**: Field `reasoning` hanya untuk logging/debug internal. **Tidak pernah ditampilkan ke UI**.

#### Task Breakdown
- [ ] Setup Ollama integration
- [ ] Test model inference speed
- [ ] Develop system prompt
- [ ] Implementasi intent generator
- [ ] Fallback mechanism jika LLM timeout
- [ ] Testing dengan berbagai context

---

### **PHASE 5 — Floating Widget UI (Layer 4)** ⏱️ 2-3 hari

#### Tujuan
Membangun antarmuka non-intrusive yang ramah dan mudah di-ignore.

#### Komponen Utama
1. **Tauri Desktop App**
   - Frameless window
   - Always on top
   - Transparent background
   - Click-through saat idle

2. **Widget Design**
   - Robot icon (80x80px)
   - Bubble chat muncul saat suggesting
   - Fade in/out animation
   - Position: bottom-right corner

3. **UI States**
   - Hidden (state: idle, suppressed)
   - Visible idle (robot icon only)
   - Suggesting (robot + bubble)

4. **IPC Communication**
   - Backend Python → Frontend Tauri
   - JSON message protocol
   - Event stream untuk state updates

#### Design Mockup
```
┌─────────────────────────┐
│                         │
│                         │
│                         │
│               ┌─────────┤
│               │  Bubble │
│               │ "Mau    │
│               │ bantuan?"│
│               └────┬────┘
│                 ▼  │
│               [Robot]    │
└─────────────────────────┘
```

#### Task Breakdown
- [ ] Setup Tauri project
- [ ] Desain robot icon/mascot
- [ ] Implementasi floating window
- [ ] Bubble chat component
- [ ] Button actions (Ya, Nanti, Dismiss)
- [ ] IPC integration dengan backend
- [ ] CSS animations
- [ ] Testing responsiveness

---

### **PHASE 6 — Integration & Polishing** ⏱️ 2 hari

#### Tujuan
Menghubungkan semua layer dan memastikan sistem bekerja end-to-end.

#### Task Breakdown
- [ ] Wire Layer 0 → Layer 1 → Layer 2 → Layer 3 → Layer 4
- [ ] End-to-end testing skenario MVP
- [ ] Performance optimization
- [ ] Error handling & logging
- [ ] Config file untuk user preferences
- [ ] Toggle mode (active/silent/disabled)
- [ ] Startup script (autostart on boot optional)
- [ ] Documentation (README, user guide)

#### Skenario Testing MVP
1. **Scenario: User Idle Detection**
   - User idle 5 menit → ORBIT muncul → "Mau aku rangkum?"
   
2. **Scenario: Error Detection**
   - Error terdeteksi → ORBIT menganalisis → "Mau aku bantu?"

3. **Scenario: User Dismiss**
   - User klik Dismiss → ORBIT masuk cooldown 10 menit

4. **Scenario: Cooldown Respect**
   - Dalam cooldown → Intent baru diabaikan

---

## 🛠️ Tech Stack

### Backend (Python)
- **Core**: Python 3.11+
- **Process monitoring**: psutil, win32gui
- **File watching**: watchdog
- **Database**: SQLite3
- **LLM**: Ollama (llama3.2/phi-3)
- **HTTP client**: httpx

### Frontend (Tauri)
- **Framework**: Tauri v2
- **UI Framework**: React (Vite)
- **Styling**: Tailwind CSS (Wajib 3.4.*)
- **Icons**: Lucide React (utama), React Icons (opsional)
- **State** Handling: Local state (FSM-driven, non-global)
- **IPC**: Tauri commands (typed JSON)
- **Build**: Rust + Node.js

### DevOps
- **Version control**: Git
- **Testing**: pytest (backend), Vitest (frontend)
- **Logging**: Python logging module
- **Config**: TOML/YAML

---

## 📦 Project Structure

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
│   ├── main.py
│   └── requirements.txt
├── frontend/
│     ├── src/
│     │   ├── main.tsx
│     │   ├── app.tsx
│     │   ├── components/
│     │   │   ├── OrbitWidget.tsx
│     │   │   ├── RobotIcon.tsx
│     │   │   ├── Bubble.tsx
│     │   │   └── ActionButtons.tsx
│     │   ├── hooks/
│     │   │   └── useOrbitState.ts
│     │   ├── styles/
│     │   │   └── index.css   # Tailwind
│     │   ├── types/
│     │   │   └── orbit.ts
│     │   └── ipc/
│     │       └── orbit.ts
│     ├── src-tauri/
│     │   ├── src/
│     │   │   └── main.rs
│     │   └── Cargo.toml
│     ├── tailwind.config.js
│     ├── postcss.config.js
│     ├── package.json
│     └── vite.config.ts
├── docs/
│   ├── RENCANA.md              # ← file ini
│   ├── PROGRESS.md
│   └── ARCHITECTURE.md
├── tests/
├── config/
│   └── orbit_config.toml
└── README.md
```

---

## 🚀 Langkah Eksekusi

### Week 1
- **Day 1-2**: Phase 1 (Context System Layer 0)
- **Day 3**: Phase 2 (Decision Engine Layer 2)
- **Day 4**: Phase 3 (Behavior FSM Layer 3)

### Week 2
- **Day 5-6**: Phase 4 (AI Brain Layer 1)
- **Day 7-8**: Phase 5 (Floating Widget UI Layer 4)

### Week 3
- **Day 9-10**: Phase 6 (Integration & Testing)
- **Day 11**: Polishing, documentation, MVP release

---

## ⚠️ Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| LLM inference terlalu lambat | UX buruk | Timeout 5s, fallback rule-based |
| Spam detection terlalu ketat | Jarang muncul | A/B testing threshold |
| UI terlalu mengganggu | User disable | Cooldown agresif, easy dismiss |
| Battery drain | Tidak sustainable | Polling interval optimization |

---

## 📊 Metrik Sukses

- [ ] Context collection latency < 100ms
- [ ] LLM inference time < 5s (P95)
- [ ] UI render time < 500ms
- [ ] False positive rate < 20%
- [ ] User dismiss rate < 50%
- [ ] CPU usage idle < 2%
- [ ] Memory footprint < 150MB

---

## 🎯 Next Steps After MVP

- Voice output (TTS optional)
- Multi-language support
- Custom automation scripts
- Plugin system
- Cloud sync (optional, privacy-first)
- Mobile companion app

---

**Status**: 🟡 Rencana siap, belum diimplementasikan  
**Target MVP Release**: 3 minggu dari kick-off  
**Owner**: Luna (OrbitAgent)  
**Tanggal Dibuat**: 11 Januari 2026
