import { useState, useEffect } from 'react'
import './App.css'
import LunaBubble from './components/LunaBubble'
import LunaIcon from './components/LunaIcon'
import ipcBridge from './ipc/bridge'

function App() {
  const [state, setState] = useState('idle')
  const [bubble, setBubble] = useState(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Connect to backend IPC
    ipcBridge.connect('ws://localhost:8765')
      .then(() => {
        console.log('✅ Connected to ORBIT backend')
      })
      .catch((err) => {
        console.error('❌ Failed to connect to backend:', err)
      })

    // Listen for UI updates from backend
    ipcBridge.on('ui_update', (data) => {
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
    })

    return () => {
      ipcBridge.disconnect()
    }
  }, [])

  const handleAction = (action) => {
    console.log('👤 User action:', action)
    
    // Send action to backend
    ipcBridge.send('user_action', {
      action: action,
      intent_id: bubble?.intent_id || null
    })
    
    if (action === 'Dismiss') {
      setVisible(false)
      setState('suppressed')
    } else if (action === 'Ya') {
      setState('executing')
      setBubble({
        text: 'Sedang diproses...',
        actions: []
      })
    } else if (action === 'Nanti') {
      setVisible(false)
      setState('idle')
    }
  }

  return (
    <div className="orbit-widget">
      <LunaIcon state={state} />
      {visible && bubble && state === 'suggesting' && (
        <LunaBubble
          text={bubble.text}
          actions={bubble.actions}
          onAction={handleAction}
        />
      )}
    </div>
  )
}

export default App
