/**
 * IPC Bridge for communicating with Python backend
 * Uses WebSocket for real-time bidirectional communication
 */

class IPCBridge {
  constructor() {
    this.ws = null
    this.listeners = new Map()
    this.connected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 2000
  }

  connect(url = 'ws://localhost:8012') {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(url)

        this.ws.onopen = () => {
          console.log('✅ IPC Bridge connected to backend')
          this.connected = true
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            this._handleMessage(message)
          } catch (error) {
            console.error('❌ Failed to parse IPC message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('❌ IPC WebSocket error:', error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('🔌 IPC connection closed')
          this.connected = false
          this._attemptReconnect(url)
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  _attemptReconnect(url) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`🔄 Reconnecting... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      setTimeout(() => {
        this.connect(url).catch(err => {
          console.error('❌ Reconnection failed:', err)
        })
      }, this.reconnectDelay)
    } else {
      console.error('❌ Max reconnection attempts reached')
    }
  }

  _handleMessage(message) {
    const { type, data } = message

    // Trigger all listeners for this message type
    if (this.listeners.has(type)) {
      const callbacks = this.listeners.get(type)
      callbacks.forEach(callback => callback(data))
    }

    // Trigger wildcard listeners
    if (this.listeners.has('*')) {
      const callbacks = this.listeners.get('*')
      callbacks.forEach(callback => callback(message))
    }
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, [])
    }
    this.listeners.get(eventType).push(callback)
  }

  off(eventType, callback) {
    if (this.listeners.has(eventType)) {
      const callbacks = this.listeners.get(eventType)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  send(type, data = {}) {
    if (!this.connected || !this.ws) {
      console.warn('⚠️ IPC not connected, message not sent:', { type, data })
      return false
    }

    try {
      const message = JSON.stringify({ type, data })
      this.ws.send(message)
      return true
    } catch (error) {
      console.error('❌ Failed to send IPC message:', error)
      return false
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
      this.connected = false
    }
  }
}

// Singleton instance
export const ipcBridge = new IPCBridge()

export default ipcBridge
