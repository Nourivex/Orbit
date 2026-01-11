import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import './Settings.css'
import ipcBridge from '../ipc/bridge'

function Settings() {
  const [aiMode, setAiMode] = useState('auto')
  const [orbitEnabled, setOrbitEnabled] = useState(true)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    // Load settings from backend
    loadSettings()
    
    // Listen for stats updates
    ipcBridge.on('stats_update', (data) => {
      setStats(data.stats)
    })
    
    return () => {
      ipcBridge.off('stats_update')
    }
  }, [])

  const loadSettings = () => {
    // Request current settings from backend
    ipcBridge.send('get_settings', {})
    
    ipcBridge.on('settings_response', (data) => {
      setAiMode(data.ai_mode || 'auto')
      setOrbitEnabled(data.orbit_enabled !== false)
    })
  }

  const handleModeChange = (newMode) => {
    setAiMode(newMode)
    ipcBridge.send('update_settings', {
      ai_mode: newMode
    })
    
    console.log('%c⚙️ AI Mode Changed', 'color: #FF9800; font-weight: bold')
    console.log('  New mode:', newMode)
  }

  const handleToggleOrbit = () => {
    const newState = !orbitEnabled
    setOrbitEnabled(newState)
    ipcBridge.send('update_settings', {
      orbit_enabled: newState
    })
    
    console.log('%c⚙️ ORBIT Toggle', 'color: #FF9800; font-weight: bold')
    console.log('  Enabled:', newState)
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <Link to="/" className="back-button">
          ← Back to ORBIT
        </Link>
        <h1>⚙️ ORBIT Settings</h1>
      </div>

      <div className="settings-content">
        {/* Kill Switch */}
        <section className="setting-section">
          <h2>🛑 Kill Switch</h2>
          <p className="setting-description">
            Emergency disable for ORBIT. When off, Luna will not observe or suggest anything.
          </p>
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={orbitEnabled}
              onChange={handleToggleOrbit}
            />
            <span className="slider"></span>
            <span className="toggle-label">
              {orbitEnabled ? '✅ ORBIT Active' : '❌ ORBIT Disabled'}
            </span>
          </label>
        </section>

        {/* AI Mode Selection */}
        <section className="setting-section">
          <h2>🧠 AI Brain Mode</h2>
          <p className="setting-description">
            Choose how Luna thinks and generates suggestions.
          </p>
          
          <div className="mode-options">
            <label className={`mode-option ${aiMode === 'auto' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="ai-mode"
                value="auto"
                checked={aiMode === 'auto'}
                onChange={() => handleModeChange('auto')}
              />
              <div className="mode-content">
                <h3>🔄 AUTO</h3>
                <p>Smart mode: Use Ollama LLM if available, fallback to Dummy</p>
                <span className="mode-badge recommended">Recommended</span>
              </div>
            </label>

            <label className={`mode-option ${aiMode === 'ollama' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="ai-mode"
                value="ollama"
                checked={aiMode === 'ollama'}
                onChange={() => handleModeChange('ollama')}
              />
              <div className="mode-content">
                <h3>🤖 OLLAMA</h3>
                <p>Force LLM mode (requires Ollama running)</p>
                <span className="mode-badge">Advanced</span>
              </div>
            </label>

            <label className={`mode-option ${aiMode === 'dummy' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="ai-mode"
                value="dummy"
                checked={aiMode === 'dummy'}
                onChange={() => handleModeChange('dummy')}
              />
              <div className="mode-content">
                <h3>💭 DUMMY</h3>
                <p>Rule-based mode with 15+ variatif responses</p>
                <span className="mode-badge">Lightweight</span>
              </div>
            </label>
          </div>
        </section>

        {/* Statistics */}
        {stats && (
          <section className="setting-section">
            <h2>📊 Statistics</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-label">Total Intents</span>
                <span className="stat-value">{stats.total_intents || 0}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Ollama Calls</span>
                <span className="stat-value">{stats.ollama_calls || 0}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Dummy Calls</span>
                <span className="stat-value">{stats.dummy_calls || 0}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Failures</span>
                <span className="stat-value">{stats.failures || 0}</span>
              </div>
            </div>
          </section>
        )}

        {/* About */}
        <section className="setting-section about">
          <h2>ℹ️ About Luna</h2>
          <p>
            <strong>ORBIT MVP v0.2</strong><br/>
            AI Desktop Agent by Luna<br/>
            Phase 2: AI Brain Upgrade ✅
          </p>
          <p className="version-info">
            Mode: <code>{aiMode}</code><br/>
            Status: <code>{orbitEnabled ? 'Active' : 'Disabled'}</code>
          </p>
        </section>
      </div>
    </div>
  )
}

export default Settings
