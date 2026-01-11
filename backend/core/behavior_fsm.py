"""
Behavior FSM - Layer 3
State machine for managing ORBIT behavior and personality
"""

import time
from enum import Enum
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from core.decision_engine import Intent, IntentType
from utils.logger import setup_logger

logger = setup_logger(__name__)


class State(Enum):
    """FSM states for ORBIT behavior"""
    IDLE = "idle"
    OBSERVING = "observing"
    SUGGESTING = "suggesting"
    EXECUTING = "executing"
    SUPPRESSED = "suppressed"
    COOLDOWN_GLOBAL = "cooldown_global"


class Event(Enum):
    """Events that trigger state transitions"""
    CONTEXT_CHANGED = "context_changed"
    INTENT_APPROVED = "intent_approved"
    USER_DISMISS = "user_dismiss"
    USER_ACTION = "user_action"
    TIMEOUT = "timeout"
    COOLDOWN_EXPIRED = "cooldown_expired"
    ENTER_FOCUS_MODE = "enter_focus_mode"
    EXIT_FOCUS_MODE = "exit_focus_mode"


@dataclass
class StateData:
    """Data associated with current state"""
    state: State
    entered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    intent: Optional[Intent] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIOutput:
    """Output to send to UI Layer (Layer 4)"""
    state: str
    emotion: str
    visible: bool
    bubble: Optional[Dict[str, Any]] = None
    actions: list = field(default_factory=list)


class BehaviorFSM:
    """
    Layer 3 - Behavior Finite State Machine
    Manages ORBIT's behavioral state and transitions
    """
    
    # State transition map: {state: {event: next_state}}
    TRANSITIONS = {
        State.IDLE: {
            Event.CONTEXT_CHANGED: State.OBSERVING,
            Event.INTENT_APPROVED: State.SUGGESTING,  # Allow direct IDLE → SUGGESTING
            Event.ENTER_FOCUS_MODE: State.COOLDOWN_GLOBAL
        },
        State.OBSERVING: {
            Event.INTENT_APPROVED: State.SUGGESTING,
            Event.TIMEOUT: State.IDLE,
            Event.ENTER_FOCUS_MODE: State.COOLDOWN_GLOBAL
        },
        State.SUGGESTING: {
            Event.USER_DISMISS: State.SUPPRESSED,
            Event.USER_ACTION: State.EXECUTING,
            Event.TIMEOUT: State.IDLE,
            Event.ENTER_FOCUS_MODE: State.COOLDOWN_GLOBAL
        },
        State.EXECUTING: {
            Event.TIMEOUT: State.IDLE,
            Event.USER_DISMISS: State.SUPPRESSED
        },
        State.SUPPRESSED: {
            Event.COOLDOWN_EXPIRED: State.IDLE
        },
        State.COOLDOWN_GLOBAL: {
            Event.EXIT_FOCUS_MODE: State.IDLE
        }
    }
    
    # Timeout durations for each state (seconds)
    STATE_TIMEOUTS = {
        State.OBSERVING: 30,      # 30s to decide
        State.SUGGESTING: 60,     # 60s before auto-dismiss
        State.EXECUTING: 10,      # 10s for action
        State.SUPPRESSED: 600     # 10 minutes cooldown
    }
    
    def __init__(self):
        """Initialize FSM in IDLE state"""
        self.current_state = State.IDLE
        self.state_data = StateData(state=State.IDLE)
        self.state_entered_at = time.time()
        
        # Callbacks
        self._state_change_callback: Optional[Callable] = None
        self._ui_update_callback: Optional[Callable] = None
        
        # History
        self.state_history = []
        
        logger.info("BehaviorFSM initialized in IDLE state")
    
    def trigger_event(self, event: Event, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Trigger an event and transition to new state if valid
        
        Args:
            event: Event to trigger
            data: Optional data associated with event
            
        Returns:
            True if transition occurred, False otherwise
        """
        if data is None:
            data = {}
        
        # Check if transition is valid
        if self.current_state not in self.TRANSITIONS:
            logger.warning(f"No transitions defined for state {self.current_state}")
            return False
        
        if event not in self.TRANSITIONS[self.current_state]:
            logger.debug(f"Event {event.value} not valid in state {self.current_state.value}")
            return False
        
        # Get next state
        next_state = self.TRANSITIONS[self.current_state][event]
        
        # Perform transition
        self._transition_to(next_state, event, data)
        return True
    
    def _transition_to(self, next_state: State, event: Event, data: Dict[str, Any]):
        """
        Transition to new state
        
        Args:
            next_state: State to transition to
            event: Event that triggered transition
            data: Event data
        """
        prev_state = self.current_state
        
        # Record in history
        self.state_history.append({
            'from': prev_state.value,
            'to': next_state.value,
            'event': event.value,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update state
        self.current_state = next_state
        self.state_entered_at = time.time()
        
        # Update state data
        self.state_data = StateData(
            state=next_state,
            intent=data.get('intent'),
            context=data.get('context', {}),
            metadata=data.get('metadata', {})
        )
        
        logger.info(f"State transition: {prev_state.value} -> {next_state.value} (event: {event.value})")
        
        # Callbacks
        if self._state_change_callback:
            self._state_change_callback(prev_state, next_state, event)
        
        # Update UI
        self._update_ui()
    
    def check_timeout(self) -> bool:
        """
        Check if current state has timed out
        
        Returns:
            True if timeout event was triggered
        """
        if self.current_state not in self.STATE_TIMEOUTS:
            return False
        
        elapsed = time.time() - self.state_entered_at
        timeout = self.STATE_TIMEOUTS[self.current_state]
        
        if elapsed >= timeout:
            logger.info(f"State {self.current_state.value} timed out ({elapsed:.1f}s >= {timeout}s)")
            return self.trigger_event(Event.TIMEOUT)
        
        return False
    
    def get_ui_output(self) -> UIOutput:
        """
        Get current UI output based on state
        
        Returns:
            UIOutput object for Layer 4
        """
        state = self.current_state
        
        if state == State.IDLE:
            return UIOutput(
                state="idle",
                emotion="neutral",
                visible=False
            )
        
        elif state == State.OBSERVING:
            return UIOutput(
                state="observing",
                emotion="curious",
                visible=True,
                bubble=None  # Just show icon
            )
        
        elif state == State.SUGGESTING:
            intent = self.state_data.intent
            message = intent.message if intent else "Ada yang bisa kubantu?"
            
            return UIOutput(
                state="suggesting",
                emotion="helpful",
                visible=True,
                bubble={
                    "text": message,
                    "actions": ["Ya", "Nanti", "Dismiss"]
                }
            )
        
        elif state == State.EXECUTING:
            return UIOutput(
                state="executing",
                emotion="working",
                visible=True,
                bubble={
                    "text": "Sedang diproses...",
                    "actions": []
                }
            )
        
        elif state in (State.SUPPRESSED, State.COOLDOWN_GLOBAL):
            return UIOutput(
                state="suppressed",
                emotion="quiet",
                visible=False
            )
        
        # Default
        return UIOutput(
            state="unknown",
            emotion="neutral",
            visible=False
        )
    
    def _update_ui(self):
        """Send UI update via callback"""
        if self._ui_update_callback:
            ui_output = self.get_ui_output()
            self._ui_update_callback(ui_output)
    
    def set_state_change_callback(self, callback: Callable):
        """Set callback for state changes"""
        self._state_change_callback = callback
    
    def set_ui_update_callback(self, callback: Callable):
        """Set callback for UI updates"""
        self._ui_update_callback = callback
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        Get current state information
        
        Returns:
            Dictionary with state info
        """
        elapsed = time.time() - self.state_entered_at
        timeout = self.STATE_TIMEOUTS.get(self.current_state)
        
        return {
            'current_state': self.current_state.value,
            'elapsed_time': elapsed,
            'timeout': timeout,
            'has_timeout': timeout is not None,
            'intent_type': self.state_data.intent.type.value if self.state_data.intent else None,
            'entered_at': self.state_data.entered_at
        }
    
    def get_history(self, limit: int = 10) -> list:
        """Get recent state transition history"""
        return self.state_history[-limit:]
    
    def reset(self):
        """Reset FSM to initial state (for testing)"""
        self.current_state = State.IDLE
        self.state_data = StateData(state=State.IDLE)
        self.state_entered_at = time.time()
        self.state_history.clear()
        logger.info("BehaviorFSM reset to IDLE")


class BehaviorController:
    """
    High-level controller that coordinates FSM with context and decisions
    """
    
    def __init__(self, fsm: Optional[BehaviorFSM] = None):
        """
        Initialize behavior controller
        
        Args:
            fsm: BehaviorFSM instance (creates new if None)
        """
        self.fsm = fsm or BehaviorFSM()
        logger.info("BehaviorController initialized")
    
    def handle_context_change(self, context: Dict[str, Any]):
        """
        Handle context change from Layer 0
        
        Args:
            context: Context snapshot
        """
        # Only trigger if in IDLE
        if self.fsm.current_state == State.IDLE:
            # Check if context is interesting
            if self._is_interesting_context(context):
                self.fsm.trigger_event(Event.CONTEXT_CHANGED, {'context': context})
    
    def handle_intent_approved(self, intent: Intent):
        """
        Handle intent approval from Layer 2
        
        Args:
            intent: Approved intent
        """
        # Allow transition from IDLE or OBSERVING to SUGGESTING
        if self.fsm.current_state in (State.IDLE, State.OBSERVING):
            logger.info(f"Intent approved, transitioning {self.fsm.current_state.value} → SUGGESTING")
            self.fsm.trigger_event(Event.INTENT_APPROVED, {'intent': intent})
        else:
            logger.warning(f"Cannot handle intent approval in state: {self.fsm.current_state.value}")
    
    def handle_user_dismiss(self):
        """Handle user dismissing popup"""
        if self.fsm.current_state in (State.SUGGESTING, State.EXECUTING):
            self.fsm.trigger_event(Event.USER_DISMISS)
    
    def handle_user_action(self, action: str):
        """
        Handle user action from UI
        
        Args:
            action: Action taken by user
        """
        if self.fsm.current_state == State.SUGGESTING:
            if action in ("Ya", "Yes", "OK"):
                self.fsm.trigger_event(Event.USER_ACTION, {'action': action})
            elif action in ("Nanti", "Later"):
                self.fsm.trigger_event(Event.TIMEOUT)  # Treat as timeout
            elif action == "Dismiss":
                self.fsm.trigger_event(Event.USER_DISMISS)
    
    def enter_focus_mode(self):
        """Enter deep focus mode (cooldown_global)"""
        self.fsm.trigger_event(Event.ENTER_FOCUS_MODE)
        logger.info("Entered focus mode - ORBIT silenced")
    
    def exit_focus_mode(self):
        """Exit focus mode"""
        if self.fsm.current_state == State.COOLDOWN_GLOBAL:
            self.fsm.trigger_event(Event.EXIT_FOCUS_MODE)
            logger.info("Exited focus mode")
    
    def tick(self):
        """
        Tick function to be called periodically
        Checks for timeouts and state progression
        """
        self.fsm.check_timeout()
        
        # Auto-expire suppressed state
        if self.fsm.current_state == State.SUPPRESSED:
            elapsed = time.time() - self.fsm.state_entered_at
            if elapsed >= self.fsm.STATE_TIMEOUTS[State.SUPPRESSED]:
                self.fsm.trigger_event(Event.COOLDOWN_EXPIRED)
    
    def _is_interesting_context(self, context: Dict[str, Any]) -> bool:
        """
        Determine if context is interesting enough to observe
        
        Args:
            context: Context snapshot
            
        Returns:
            True if interesting
        """
        # Idle for a while
        if context.get('idle_time', 0) >= 180:  # 3 minutes
            return True
        
        # Recent file changes
        if context.get('recent_file_changes', 0) > 3:
            return True
        
        # Errors detected
        if context.get('error_count', 0) > 0:
            return True
        
        return False
    
    def process_decision(self, decision):
        """
        Process decision result from Layer 2 and generate UI output
        
        Args:
            decision: DecisionResult from DecisionEngine
            
        Returns:
            UI output dict or None
        """
        if decision.approved and decision.intent:
            # Intent approved, transition to suggesting
            self.handle_intent_approved(decision.intent)
            return self.fsm.get_ui_output()
        elif not decision.approved:
            # Intent rejected, stay idle or go to appropriate state
            if "Cooldown" in decision.reason or "spam" in decision.reason.lower():
                # Cooldown active, suppress
                if self.fsm.current_state not in (State.SUPPRESSED, State.COOLDOWN_GLOBAL):
                    self.fsm.trigger_event(Event.TIMEOUT)  # Transition to idle
            return None
        return None
    
    def get_current_state(self) -> State:
        """Get current FSM state"""
        return self.fsm.current_state

