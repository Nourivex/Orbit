import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import './App.css'
import LunaBubble from './components/LunaBubble'
import LunaIcon from './components/LunaIcon'
import ipcBridge from './ipc/bridge'
import { useTauri } from './hooks/useTauri'

function App() {
  const [state, setState] = useState('idle')
  const [bubble, setBubble] = useState(null)
  const [visible, setVisible] = useState(false)
  const [testMode, setTestMode] = useState(false)
  
  const { isTauri, isVisible: windowVisible, sendNotification, checkVisibility } = useTauri()

  useEffect(() => {
    console.log('[ORBIT] Running in Tauri:', isTauri)
    
    // Connect to backend IPC
    ipcBridge.connect('ws://localhost:8765')
      .then(() => {
        console.log('✅ Connected to ORBIT backend')
      })
      .catch((err) => {
        console.error('❌ Failed to connect to backend:', err)
      })

    // Listen for UI updates from backend
    ipcBridge.on('ui_update', async (data) => {
      console.log('%c📥 UI Update from Backend', 'background: #4CAF50; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold')
      console.group('Update Details')
      console.log('🎭 State:', data.state || 'idle')
      console.log('😊 Emotion:', data.emotion || 'neutral')
      console.log('👁️ Visible:', data.visible !== false)
      
      if (data.bubble) {
        console.log('%c💬 Bubble Chat Active', 'color: #2196F3; font-weight: bold')
        console.log('  📝 Message:', data.bubble.text)
        console.log('  🎯 Actions:', data.bubble.actions || [])
        if (data.bubble.intent_id) {
          console.log('  🆔 Intent ID:', data.bubble.intent_id)
        }
      } else {
        console.log('💬 Bubble: None')
      }
      console.groupEnd()
      
      setState(data.state || 'idle')
      
      if (data.bubble) {
        // Check if window is minimized to tray
        const isWindowVisible = isTauri ? await checkVisibility() : true
        
        if (isTauri && !isWindowVisible) {
          // Send Windows notification instead of bubble
          console.log('[Tauri] Window minimized, sending notification')
          sendNotification('ORBIT Luna', data.bubble.text)
        } else {
          // Show bubble normally
          setBubble({
            text: data.bubble.text,
            actions: data.bubble.actions || []
          })
          setVisible(true)
        }
        setTestMode(false) // Real update, disable test
      } else {
        setVisible(false)
      }
    })

    return () => {
      ipcBridge.disconnect()
    }
  }, [isTauri, sendNotification, checkVisibility])

  const handleIconClick = () => {
    console.log('🖱️ Luna icon clicked - showing test bubble')
    setTestMode(true)
    setState('suggesting')
    setBubble({
      text: 'Ini test bubble! Klik avatar untuk toggle.',
      actions: ['Oke', 'Dismiss']
    })
    setVisible(!visible)
  }

  const handleAction = (action) => {
    console.log('👤 User action:', action)
    
    // Send action to backend only if not test mode
    if (!testMode) {
      ipcBridge.send('user_action', {
        action: action,
        intent_id: bubble?.intent_id || null
      })
    }
    
    if (action === 'Dismiss' || action === 'Oke') {
      setVisible(false)
      setState('idle')
      setTestMode(false)
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
      <LunaIcon state={state} onClick={handleIconClick} />
      {visible && bubble && (
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
