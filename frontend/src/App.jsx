import { useState, useEffect } from 'react'
import './App.css'
import LunaBubble from './components/LunaBubble'
import LunaIcon from './components/LunaIcon'
import ipcBridge from './ipc/bridge'
import { useTauri } from './hooks/useTauri'
import { getCurrentWindow } from '@tauri-apps/api/window'
// Pastikan path Settings benar, atau buat component dummy jika belum ada
// import Settings from './pages/Settings' 

function App() {
  // 1. STATE AWAL HARUS NULL (Jangan 'main')
  const [windowLabel, setWindowLabel] = useState(null) 
  
  const [state, setState] = useState('idle')
  const [bubble, setBubble] = useState(null)
  const [visible, setVisible] = useState(false)
  
  // Ambil helper dari hook
  const { isTauri, sendNotification } = useTauri()

  // 2. DETEKSI IDENTITAS WINDOW (CRITICAL)
  useEffect(() => {
    const identifyWindow = async () => {
      if (isTauri) {
        try {
          const win = await getCurrentWindow()
          console.log('🪟 Window Identified:', win.label)
          setWindowLabel(win.label)
        } catch (err) {
          console.error('❌ Failed to identify window:', err)
          // Hanya fallback ke main jika benar-benar error fatal
          setWindowLabel('main') 
        }
      } else {
        // Mode browser (dev tanpa tauri) -> Anggap main
        setWindowLabel('main')
      }
    }
    identifyWindow()
  }, [isTauri])

  // 3. EFEK SAMPING (IPC) - HANYA UNTUK MAIN WINDOW
  useEffect(() => {
    // Jaga-jaga: Jika label belum tau atau BUKAN main, stop.
    if (windowLabel !== 'main') return 

    console.log('✅ Main Window Logic Activated')
    
    const handleUiUpdate = (data) => {
        console.log('📥 UI Update:', data)
        setState(data.state || 'idle')
        
        if (data.bubble) {
             setBubble({ 
               text: data.bubble.text, 
               actions: data.bubble.actions || [] 
             })
             setVisible(true)
        } else {
             setVisible(false)
        }
    }

    // Connect listener
    ipcBridge.on('ui_update', handleUiUpdate)

    return () => {
      ipcBridge.disconnect()
    }
  }, [windowLabel]) // Re-run hanya jika windowLabel confirm 'main'

  // --- RENDER GATEKEEPER ---

  // A. Sedang Loading / Identitas belum tau? JANGAN RENDER APAPUN.
  if (windowLabel === null) {
    return null // Layar kosong, tidak ada logic yang jalan
  }

  // B. Apakah ini Window Settings?
  if (windowLabel === 'settings') {
    return (
      <div className="settings-container" style={{ padding: '20px', background: 'white', height: '100vh', overflow: 'auto' }}>
        <h2>Pengaturan ORBIT</h2>
        <p>Panel konfigurasi (v0.2)</p>
      </div>
    )
  }

  // C. Apakah ini Window Main? (Widget)
  if (windowLabel === 'main') {
    return (
      <div className="orbit-widget">
         {/* Render Bubble jika ada */}
         {visible && bubble && (
          <LunaBubble
            text={bubble.text}
            actions={bubble.actions}
            onAction={(action) => ipcBridge.send('user_action', { action })}
          />
        )}
        
        {/* Render Avatar */}
        <LunaIcon 
          state={state} 
          onClick={() => {
              // Manual trigger test
              ipcBridge.send('manual_trigger', { type: 'poke' })
          }} 
        />
      </div>
    )
  }

  // D. Fallback (Unknown Window)
  return null
}

export default App
