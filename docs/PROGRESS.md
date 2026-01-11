# PROGRESS LOG — ORBIT MVP v0.1

## 📅 11 Januari 2026

### ✅ Keputusan Teknis
1. **Arsitektur Final**: Layer 0-4 dengan pemisahan tegas antara reasoning (AI), decision (rule-based), dan behavior (FSM)
2. **MVP Scope**: Fokus pada single intent type (suggest_help) untuk validasi end-to-end flow
3. **Tech Stack**:
   - Backend: Python 3.11+ (psutil, watchdog, Ollama)
   - Frontend: Tauri v2 (HTML/CSS/JS)
   - Database: SQLite untuk context cache
4. **LLM Strategy**: Ollama local dengan timeout 5s, fallback ke rule-based jika lambat
5. **UI Design**: Non-intrusive floating widget, bottom-right corner, easy dismiss

### 📝 Rencana Dibuat
- `docs/RENCANA.md` berisi roadmap lengkap Phase 1-6
- Target timeline: 3 minggu untuk MVP v0.1
- Kriteria sukses MVP didefinisikan dengan jelas

### 🔍 Keputusan Penting
- **Decision Engine threshold**: confidence >= 0.7 untuk approve intent
- **Cooldown policy**:
  - Per-intent: 3-5 menit
  - Global: 1 menit
  - User dismiss: 10 menit
- **FSM States**: idle, observing, suggesting, executing, suppressed
- **Max popup per hour**: 5 (anti-spam)

### 🚧 Pending Decisions
- Robot icon design (SVG vs PNG)
- Exact LLM model choice (llama3.2 vs phi-3) → depends on performance testing
- Autostart on boot (optional, akan diputuskan setelah MVP)

### 📦 Project Setup
- Struktur folder backend/frontend/docs didefinisikan
- Git repository initialized
- Agent mode instructions finalized

### 🔄 Refinement Applied
- Added **Non-Goals MVP** untuk mencegah scope creep
- Added **Privacy & Safety Principles** untuk trust
- Added **Prinsip Desain ORBIT** sebagai kompas jangka panjang
- Enhanced Decision Engine dengan **Confidence Decay**
- Added `cooldown_global` state untuk deep focus mode
- Clarified `reasoning` field sebagai internal-only

---

## 🎯 Next Immediate Steps
1. Initialize Python project (requirements.txt, virtual env)
2. Setup Tauri project skeleton
3. Begin Phase 1: Context Hub implementation
4. Test psutil + win32gui untuk window monitoring

---

**Status**: 🟢 Planning complete, ready for implementation  
**Phase**: Pre-implementation  
**Owner**: Luna (OrbitAgent)
