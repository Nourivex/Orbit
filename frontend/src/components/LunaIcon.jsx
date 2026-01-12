import PropTypes from 'prop-types'
import './LunaIcon.css'

function LunaIcon({ state, onClick }) {
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

  return (
    <div 
      className={`luna-icon luna-icon-${state}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
      title={onClick ? "Click untuk test bubble" : "Luna"}
      data-tauri-drag-region
    >
      <div className="icon-container" data-tauri-drag-region>
        <span className="icon-emoji" data-tauri-drag-region>{getEmoji()}</span>
      </div>
      {state === 'observing' && (
        <div className="pulse-ring" data-tauri-drag-region></div>
      )}
    </div>
  )
}

LunaIcon.propTypes = {
  state: PropTypes.string.isRequired,
  onClick: PropTypes.func
}

export default LunaIcon
