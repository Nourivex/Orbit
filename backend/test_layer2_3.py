"""
Test Suite for Layer 2 & 3 - Decision Engine and Behavior FSM
"""

import time
import pytest
from datetime import datetime

from core.decision_engine import (
    DecisionEngine, Intent, IntentType, 
    CooldownManager, SpamFilter, ConfidenceDecay
)
from core.behavior_fsm import BehaviorFSM, BehaviorController, State, Event


# ==================== DECISION ENGINE TESTS ====================

class TestCooldownManager:
    """Test cooldown management"""
    
    def test_cooldown_initialization(self):
        """Test cooldown manager initializes correctly"""
        manager = CooldownManager(
            per_intent_cooldown=180,
            global_cooldown=60,
            dismiss_cooldown=600
        )
        assert manager.per_intent_cooldown == 180
        assert manager.global_cooldown == 60
        assert manager.dismiss_cooldown == 600
    
    def test_can_show_intent_fresh(self):
        """Test intent can be shown when no history"""
        manager = CooldownManager()
        can_show, reason = manager.can_show_intent(IntentType.SUGGEST_HELP)
        assert can_show is True
        assert "passed" in reason.lower()
    
    def test_global_cooldown_blocks(self):
        """Test global cooldown blocks all intents"""
        manager = CooldownManager(global_cooldown=10)
        
        # Show first intent
        manager.record_popup(IntentType.SUGGEST_HELP)
        
        # Try to show different intent immediately
        can_show, reason = manager.can_show_intent(IntentType.INFO)
        assert can_show is False
        assert "global cooldown" in reason.lower()
    
    def test_per_intent_cooldown(self):
        """Test per-intent cooldown"""
        manager = CooldownManager(per_intent_cooldown=5, global_cooldown=1)
        
        # Show intent
        manager.record_popup(IntentType.SUGGEST_HELP)
        time.sleep(2)  # Wait for global cooldown
        
        # Same intent should be blocked
        can_show, _ = manager.can_show_intent(IntentType.SUGGEST_HELP)
        assert can_show is False
        
        # Different intent should be allowed
        can_show, _ = manager.can_show_intent(IntentType.INFO)
        assert can_show is True
    
    def test_dismiss_cooldown_priority(self):
        """Test dismiss cooldown has highest priority"""
        manager = CooldownManager(dismiss_cooldown=10)
        
        manager.record_dismiss()
        
        # Even fresh intent should be blocked
        can_show, reason = manager.can_show_intent(IntentType.SUGGEST_HELP)
        assert can_show is False
        assert "dismissed recently" in reason.lower()


class TestSpamFilter:
    """Test spam filtering"""
    
    def test_spam_filter_initialization(self):
        """Test spam filter initializes correctly"""
        filter = SpamFilter(max_popups_per_hour=5, same_intent_window=900)
        assert filter.max_popups_per_hour == 5
        assert filter.same_intent_window == 900
    
    def test_max_popups_per_hour(self):
        """Test max popups per hour limit"""
        filter = SpamFilter(max_popups_per_hour=3)
        
        # Record 3 popups
        for _ in range(3):
            filter.record_popup(IntentType.SUGGEST_HELP)
        
        # 4th should be spam
        is_spam, reason = filter.is_spam(IntentType.INFO)
        assert is_spam is True
        assert "max popups" in reason.lower()
    
    def test_same_intent_window(self):
        """Test same intent within window is spam"""
        filter = SpamFilter(same_intent_window=5)
        
        filter.record_popup(IntentType.SUGGEST_HELP)
        
        # Same intent immediately should be spam
        is_spam, _ = filter.is_spam(IntentType.SUGGEST_HELP)
        assert is_spam is True
        
        # Different intent should be ok
        is_spam, _ = filter.is_spam(IntentType.INFO)
        assert is_spam is False


class TestConfidenceDecay:
    """Test confidence decay mechanism"""
    
    def test_confidence_decay_initialization(self):
        """Test decay initializes correctly"""
        decay = ConfidenceDecay()
        assert len(decay._dismiss_count) == 0
    
    def test_dismiss_decay(self):
        """Test confidence decays with dismissals"""
        decay = ConfidenceDecay()
        
        intent = Intent(
            type=IntentType.SUGGEST_HELP,
            confidence=0.9,
            message="Test"
        )
        
        context = {"active_app": "Test.exe"}
        
        # First time - no decay
        confidence = decay.apply_decay(intent, context, 0)
        assert confidence == 0.9
        
        # Record dismiss
        decay.record_dismiss(IntentType.SUGGEST_HELP)
        
        # Second time - should decay
        confidence = decay.apply_decay(intent, context, 0)
        assert confidence < 0.9
    
    def test_time_decay(self):
        """Test confidence decays over time"""
        decay = ConfidenceDecay()
        
        intent = Intent(
            type=IntentType.SUGGEST_HELP,
            confidence=0.9,
            message="Test"
        )
        
        context = {"active_app": "Test.exe"}
        
        # Fresh intent
        confidence1 = decay.apply_decay(intent, context, 0)
        
        # After 5 minutes
        confidence2 = decay.apply_decay(intent, context, 300)
        
        assert confidence2 < confidence1


class TestDecisionEngine:
    """Test complete decision engine"""
    
    def test_decision_engine_initialization(self):
        """Test decision engine initializes correctly"""
        engine = DecisionEngine()
        assert engine.cooldown_manager is not None
        assert engine.spam_filter is not None
        assert engine.confidence_decay is not None
    
    def test_approve_valid_intent(self):
        """Test approving valid intent"""
        engine = DecisionEngine()
        
        intent = Intent(
            type=IntentType.SUGGEST_HELP,
            confidence=0.85,
            message="Need help?"
        )
        
        context = {"active_app": "Test.exe", "idle_time": 200}
        
        result = engine.evaluate(intent, context)
        
        assert result.approved is True
        assert "passed" in result.reason.lower()
    
    def test_reject_low_confidence(self):
        """Test rejecting low confidence intent"""
        engine = DecisionEngine()
        
        intent = Intent(
            type=IntentType.SUGGEST_HELP,
            confidence=0.5,  # Below threshold
            message="Maybe help?"
        )
        
        context = {"active_app": "Test.exe"}
        
        result = engine.evaluate(intent, context)
        
        assert result.approved is False
        assert "confidence too low" in result.reason.lower()
    
    def test_reject_during_cooldown(self):
        """Test rejecting intent during cooldown"""
        engine = DecisionEngine()
        
        intent = Intent(
            type=IntentType.SUGGEST_HELP,
            confidence=0.85,
            message="Help?"
        )
        
        context = {"active_app": "Test.exe"}
        
        # Approve first
        result1 = engine.evaluate(intent, context)
        assert result1.approved is True
        
        # Try again immediately
        result2 = engine.evaluate(intent, context)
        assert result2.approved is False
        assert "cooldown" in result2.reason.lower()
    
    def test_handle_user_dismiss(self):
        """Test handling user dismiss"""
        engine = DecisionEngine()
        
        # Simulate approve and dismiss
        intent = Intent(
            type=IntentType.SUGGEST_HELP,
            confidence=0.85,
            message="Help?"
        )
        
        context = {"active_app": "Test.exe"}
        
        result = engine.evaluate(intent, context)
        assert result.approved is True
        
        # User dismisses
        engine.handle_user_dismiss()
        engine.handle_intent_dismissed(IntentType.SUGGEST_HELP)
        
        # Next intent should be blocked by dismiss cooldown
        time.sleep(1)
        result2 = engine.evaluate(intent, context)
        assert result2.approved is False


# ==================== BEHAVIOR FSM TESTS ====================

class TestBehaviorFSM:
    """Test behavior finite state machine"""
    
    def test_fsm_initialization(self):
        """Test FSM initializes in IDLE state"""
        fsm = BehaviorFSM()
        assert fsm.current_state == State.IDLE
    
    def test_valid_transition(self):
        """Test valid state transition"""
        fsm = BehaviorFSM()
        
        # IDLE -> OBSERVING
        success = fsm.trigger_event(Event.CONTEXT_CHANGED)
        assert success is True
        assert fsm.current_state == State.OBSERVING
    
    def test_invalid_transition(self):
        """Test invalid state transition"""
        fsm = BehaviorFSM()
        
        # IDLE -> SUGGESTING (invalid)
        success = fsm.trigger_event(Event.INTENT_APPROVED)
        assert success is False
        assert fsm.current_state == State.IDLE  # Should remain
    
    def test_full_flow_happy_path(self):
        """Test full happy path flow"""
        fsm = BehaviorFSM()
        
        # IDLE -> OBSERVING
        assert fsm.trigger_event(Event.CONTEXT_CHANGED) is True
        assert fsm.current_state == State.OBSERVING
        
        # OBSERVING -> SUGGESTING
        intent = Intent(IntentType.SUGGEST_HELP, 0.9, "Help?")
        assert fsm.trigger_event(Event.INTENT_APPROVED, {'intent': intent}) is True
        assert fsm.current_state == State.SUGGESTING
        
        # SUGGESTING -> EXECUTING
        assert fsm.trigger_event(Event.USER_ACTION, {'action': 'Yes'}) is True
        assert fsm.current_state == State.EXECUTING
        
        # EXECUTING -> IDLE
        assert fsm.trigger_event(Event.TIMEOUT) is True
        assert fsm.current_state == State.IDLE
    
    def test_dismiss_flow(self):
        """Test user dismiss flow"""
        fsm = BehaviorFSM()
        
        # Get to SUGGESTING
        fsm.trigger_event(Event.CONTEXT_CHANGED)
        intent = Intent(IntentType.SUGGEST_HELP, 0.9, "Help?")
        fsm.trigger_event(Event.INTENT_APPROVED, {'intent': intent})
        
        assert fsm.current_state == State.SUGGESTING
        
        # User dismisses
        fsm.trigger_event(Event.USER_DISMISS)
        assert fsm.current_state == State.SUPPRESSED
    
    def test_focus_mode(self):
        """Test focus mode (cooldown_global)"""
        fsm = BehaviorFSM()
        
        # Enter focus mode from IDLE
        fsm.trigger_event(Event.ENTER_FOCUS_MODE)
        assert fsm.current_state == State.COOLDOWN_GLOBAL
        
        # Exit focus mode
        fsm.trigger_event(Event.EXIT_FOCUS_MODE)
        assert fsm.current_state == State.IDLE
    
    def test_timeout_mechanism(self):
        """Test state timeout"""
        fsm = BehaviorFSM()
        fsm.STATE_TIMEOUTS[State.OBSERVING] = 1  # 1 second timeout
        
        # Enter OBSERVING
        fsm.trigger_event(Event.CONTEXT_CHANGED)
        assert fsm.current_state == State.OBSERVING
        
        # Wait for timeout
        time.sleep(1.5)
        
        # Check timeout
        timed_out = fsm.check_timeout()
        assert timed_out is True
        assert fsm.current_state == State.IDLE
    
    def test_ui_output_generation(self):
        """Test UI output for different states"""
        fsm = BehaviorFSM()
        
        # IDLE - not visible
        output = fsm.get_ui_output()
        assert output.state == "idle"
        assert output.visible is False
        
        # SUGGESTING - visible with bubble
        fsm.trigger_event(Event.CONTEXT_CHANGED)
        intent = Intent(IntentType.SUGGEST_HELP, 0.9, "Need help?")
        fsm.trigger_event(Event.INTENT_APPROVED, {'intent': intent})
        
        output = fsm.get_ui_output()
        assert output.state == "suggesting"
        assert output.visible is True
        assert output.bubble is not None
        assert "Need help?" in output.bubble['text']
    
    def test_state_history_tracking(self):
        """Test state transition history"""
        fsm = BehaviorFSM()
        
        # Make some transitions
        fsm.trigger_event(Event.CONTEXT_CHANGED)
        fsm.trigger_event(Event.TIMEOUT)
        
        history = fsm.get_history()
        assert len(history) == 2
        assert history[0]['from'] == 'idle'
        assert history[0]['to'] == 'observing'


class TestBehaviorController:
    """Test behavior controller"""
    
    def test_controller_initialization(self):
        """Test controller initializes correctly"""
        controller = BehaviorController()
        assert controller.fsm is not None
        assert controller.fsm.current_state == State.IDLE
    
    def test_handle_context_change(self):
        """Test handling context change"""
        controller = BehaviorController()
        
        # Interesting context (idle > 180s)
        context = {
            'active_app': 'Code.exe',
            'idle_time': 200,
            'recent_file_changes': 0,
            'error_count': 0
        }
        
        controller.handle_context_change(context)
        assert controller.fsm.current_state == State.OBSERVING
    
    def test_handle_intent_approved(self):
        """Test handling approved intent"""
        controller = BehaviorController()
        
        # Get to OBSERVING state
        controller.fsm.trigger_event(Event.CONTEXT_CHANGED)
        
        intent = Intent(IntentType.SUGGEST_HELP, 0.9, "Help?")
        controller.handle_intent_approved(intent)
        
        assert controller.fsm.current_state == State.SUGGESTING
    
    def test_handle_user_actions(self):
        """Test handling various user actions"""
        controller = BehaviorController()
        
        # Get to SUGGESTING
        controller.fsm.trigger_event(Event.CONTEXT_CHANGED)
        intent = Intent(IntentType.SUGGEST_HELP, 0.9, "Help?")
        controller.fsm.trigger_event(Event.INTENT_APPROVED, {'intent': intent})
        
        # Test "Ya" action
        controller.handle_user_action("Ya")
        assert controller.fsm.current_state == State.EXECUTING
        
        # Reset and test dismiss
        controller.fsm.reset()
        controller.fsm.trigger_event(Event.CONTEXT_CHANGED)
        controller.fsm.trigger_event(Event.INTENT_APPROVED, {'intent': intent})
        
        controller.handle_user_action("Dismiss")
        assert controller.fsm.current_state == State.SUPPRESSED
    
    def test_focus_mode_toggle(self):
        """Test entering and exiting focus mode"""
        controller = BehaviorController()
        
        controller.enter_focus_mode()
        assert controller.fsm.current_state == State.COOLDOWN_GLOBAL
        
        controller.exit_focus_mode()
        assert controller.fsm.current_state == State.IDLE
    
    def test_tick_function(self):
        """Test periodic tick function"""
        controller = BehaviorController()
        controller.fsm.STATE_TIMEOUTS[State.OBSERVING] = 1
        
        # Get to OBSERVING
        controller.fsm.trigger_event(Event.CONTEXT_CHANGED)
        
        # Wait and tick
        time.sleep(1.5)
        controller.tick()
        
        # Should have timed out
        assert controller.fsm.current_state == State.IDLE


# ==================== RUN TESTS ====================

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("ORBIT Layer 2 & 3 Test Suite")
    print("="*60)
    
    # Run pytest
    result = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "test_"
    ])
    
    return result == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
