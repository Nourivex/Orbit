import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import './LunaIcon.css'

function LunaIcon({ state, onClick }) {
  // Remove absolute positioning - now controlled by flexbox parent
  const [isDragging, setIsDragging] = useState(false)

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

  const handleClick = (e) => {
    if (!isDragging && onClick) {
      onClick(e)
    }
  }

  return (
    <div
      className={`luna-icon luna-icon-${state}`}
      onClick={handleClick}
      style={{
        cursor: 'pointer'
      }}
      title="Luna - Click to interact"
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
