import PropTypes from 'prop-types'
import './LunaBubble.css'

function LunaBubble({ text, actions, onAction }) {
  return (
    <div className="luna-bubble">
      <div className="bubble-content">
        <p className="bubble-text">{text}</p>
        {actions && actions.length > 0 && (
          <div className="bubble-actions">
            {actions.map((action) => (
              <button
                key={action}
                className={`bubble-action ${action.toLowerCase()}`}
                onClick={() => onAction(action)}
              >
                {action}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="bubble-tail"></div>
    </div>
  )
}

LunaBubble.propTypes = {
  text: PropTypes.string.isRequired,
  actions: PropTypes.arrayOf(PropTypes.string),
  onAction: PropTypes.func.isRequired,
}

export default LunaBubble
