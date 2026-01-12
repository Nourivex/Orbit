import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import './LunaIcon.css'

function LunaIcon({ state, onClick }) {
  const [position, setPosition] = useState({ x: window.innerWidth - 84, y: window.innerHeight - 84 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })

  useEffect(() => {
    // Initialize position to bottom-right
    setPosition({ x: window.innerWidth - 84, y: window.innerHeight - 84 })
  }, [])

  const getEmoji = () => {
    switch (state) {
      case 'suggesting':
        return '🌟'
      case 'observing':
        return '👀'
      case 'executing':
        return '⚙️'
      default:
        return '🤖'
    }
  }

  const handleMouseDown = (e) => {
    e.preventDefault()
    setIsDragging(true)
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    })
  }

  const handleMouseMove = (e) => {
    if (isDragging) {
      const newX = e.clientX - dragOffset.x
      const newY = e.clientY - dragOffset.y
      setPosition({ x: newX, y: newY })
    }
  }

  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false)

      // Auto-snap to nearest edge
      const screenWidth = window.innerWidth
      const screenHeight = window.innerHeight
      const iconSize = 64
      const margin = 20

      const centerX = position.x + iconSize / 2
      const centerY = position.y + iconSize / 2

      let finalX = position.x
      let finalY = position.y

      // Snap to left or right edge
      if (centerX < screenWidth / 2) {
        // Snap to left
        finalX = margin
      } else {
        // Snap to right
        finalX = screenWidth - iconSize - margin
      }

      // Keep Y within bounds
      finalY = Math.max(margin, Math.min(screenHeight - iconSize - margin, position.y))

      setPosition({ x: finalX, y: finalY })
    }
  }

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, position, dragOffset])

  const handleClick = (e) => {
    // Only trigger onClick if not dragging
    if (!isDragging && onClick) {
      onClick(e)
    }
  }

  return (
    <div
      className={`luna-icon luna-icon-${state}`}
      onMouseDown={handleMouseDown}
      onClick={handleClick}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        cursor: isDragging ? 'grabbing' : 'grab'
      }}
      title="Luna - Drag to move"
    >
      <div className="icon-container">
        <span className="icon-emoji">{getEmoji()}</span>
      </div>
      {state === 'observing' && (
        <div className="pulse-ring"></div>
      )}
    </div>
  )
}

LunaIcon.propTypes = {
  state: PropTypes.string.isRequired,
  onClick: PropTypes.func
}

export default LunaIcon
