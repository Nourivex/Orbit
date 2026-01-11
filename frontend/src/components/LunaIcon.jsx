import PropTypes from 'prop-types'
import './LunaIcon.css'

function LunaIcon({ state }) {
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
    <div className={`luna-icon luna-icon-${state}`}>
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
}

export default LunaIcon
