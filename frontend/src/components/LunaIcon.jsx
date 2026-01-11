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
