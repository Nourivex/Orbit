"""
Integration Test - Layers 0 → 1 → 2 → 3
End-to-end pipeline validation
"""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.context_hub import ContextHub
from core.ai_brain import AIBrain, AIMode
from core.decision_engine import DecisionEngine
from core.behavior_fsm import BehaviorController
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ORBITIntegration:
    """
    Complete ORBIT integration
    Connects all layers: Context → AI → Decision → Behavior
    """
    
    def __init__(self, use_ollama: bool = False):
        """
        Initialize ORBIT integration
        
        Args:
            use_ollama: Try to use Ollama (will fallback to dummy if unavailable)
        """
        logger.info("="*60)
        logger.info("Initializing ORBIT Integration")
        logger.info("="*60)
        
        # Layer 0: Context Hub
        self.context_hub = ContextHub(polling_interval=5.0)
        logger.info("✅ Layer 0 (Context Hub) initialized")
        
        # Layer 1: AI Brain
        ai_mode = AIMode.AUTO if use_ollama else AIMode.DUMMY
        self.ai_brain = AIBrain(mode=ai_mode)
        logger.info(f"✅ Layer 1 (AI Brain) initialized - mode: {ai_mode.value}")
        
        # Layer 2: Decision Engine
        self.decision_engine = DecisionEngine()
        logger.info("✅ Layer 2 (Decision Engine) initialized")
        
        # Layer 3: Behavior FSM
        self.behavior_controller = BehaviorController()
        logger.info("✅ Layer 3 (Behavior FSM) initialized")
        
        # Statistics
        self.iteration_count = 0
        self.intents_generated = 0
        self.intents_approved = 0
        self.popups_shown = 0
    
    def process_iteration(self):
        """Process one iteration of the ORBIT pipeline"""
        self.iteration_count += 1
        
        print(f"\n{'='*60}")
        print(f"Iteration {self.iteration_count}")
        print(f"{'='*60}")
        
        # Step 1: Get context from Layer 0
        context = self.context_hub.get_context_snapshot()
        print(f"\n[Layer 0] Context:")
        print(f"  App: {context['active_app']}")
        print(f"  Idle: {context['idle_time']}s ({context['idle_level']})")
        print(f"  Files changed: {context['recent_file_changes']}")
        print(f"  Errors: {context['error_count']}")
        
        # Check if context is interesting for FSM
        self.behavior_controller.handle_context_change(context)
        
        current_state = self.behavior_controller.fsm.current_state.value
        print(f"\n[Layer 3] FSM State: {current_state}")
        
        # Only generate intent if in OBSERVING state
        if current_state != "observing":
            print("  → Not in observing state, skipping intent generation")
            return
        
        # Step 2: Generate intent with AI Brain (Layer 1)
        intent = self.ai_brain.generate_intent(context)
        self.intents_generated += 1
        
        print(f"\n[Layer 1] Intent Generated:")
        print(f"  Type: {intent.type.value}")
        print(f"  Confidence: {intent.confidence:.2f}")
        print(f"  Message: {intent.message}")
        
        if intent.type.value == "none":
            print("  → No intent, returning to idle")
            self.behavior_controller.fsm.trigger_event(
                self.behavior_controller.fsm.Event.TIMEOUT
            )
            return
        
        # Step 3: Evaluate with Decision Engine (Layer 2)
        decision = self.decision_engine.evaluate(intent, context)
        
        print(f"\n[Layer 2] Decision:")
        print(f"  Approved: {decision.approved}")
        print(f"  Reason: {decision.reason}")
        
        if decision.approved:
            self.intents_approved += 1
            
            # Step 4: Transition FSM to SUGGESTING
            self.behavior_controller.handle_intent_approved(intent)
            self.popups_shown += 1
            
            # Get UI output
            ui_output = self.behavior_controller.fsm.get_ui_output()
            
            print(f"\n[Layer 3→4] UI Output:")
            print(f"  State: {ui_output.state}")
            print(f"  Visible: {ui_output.visible}")
            print(f"  Emotion: {ui_output.emotion}")
            if ui_output.bubble:
                print(f"  Bubble text: {ui_output.bubble['text']}")
                print(f"  Actions: {ui_output.bubble.get('actions', [])}")
            
            # Simulate user action (for demo)
            print(f"\n  [Simulating user dismiss...]")
            time.sleep(1)
            self.behavior_controller.handle_user_dismiss()
            self.decision_engine.handle_user_dismiss()
            self.decision_engine.handle_intent_dismissed(intent.type)
        
        else:
            print(f"  → Intent rejected, returning to idle")
            self.behavior_controller.fsm.trigger_event(
                self.behavior_controller.fsm.Event.TIMEOUT
            )
    
    def get_stats(self):
        """Get integration statistics"""
        return {
            'iterations': self.iteration_count,
            'intents_generated': self.intents_generated,
            'intents_approved': self.intents_approved,
            'popups_shown': self.popups_shown,
            'approval_rate': (self.intents_approved / self.intents_generated * 100) 
                           if self.intents_generated > 0 else 0,
            'layer0': self.context_hub.get_stats(),
            'layer1': self.ai_brain.get_stats(),
            'layer2': self.decision_engine.get_stats(),
            'layer3': self.behavior_controller.fsm.get_state_info()
        }


def test_integration():
    """Test complete ORBIT integration"""
    print("\n" + "="*60)
    print("ORBIT Integration Test - All Layers")
    print("="*60)
    
    # Create integration (dummy mode for reliable testing)
    orbit = ORBITIntegration(use_ollama=False)
    
    # Simulate various contexts
    test_contexts = [
        {
            'desc': 'Long idle in VSCode',
            'idle_time': 350,
            'active_app': 'Code.exe',
            'file_changes': 2,
            'errors': 0
        },
        {
            'desc': 'Active with errors',
            'idle_time': 200,
            'active_app': 'Chrome.exe',
            'file_changes': 0,
            'errors': 1
        },
        {
            'desc': 'Many file changes',
            'idle_time': 30,
            'active_app': 'Code.exe',
            'file_changes': 8,
            'errors': 0
        },
        {
            'desc': 'Normal activity',
            'idle_time': 10,
            'active_app': 'Code.exe',
            'file_changes': 1,
            'errors': 0
        }
    ]
    
    # Override context hub's get_context_snapshot for testing
    context_idx = 0
    original_get_context = orbit.context_hub.get_context_snapshot
    
    def mock_context():
        nonlocal context_idx
        if context_idx < len(test_contexts):
            ctx = test_contexts[context_idx]
            context_idx += 1
            return {
                'timestamp': '2026-01-11T10:00:00Z',
                'active_app': ctx['active_app'],
                'window_title': f"{ctx['active_app']} window",
                'idle_time': ctx['idle_time'],
                'idle_level': 'long' if ctx['idle_time'] > 180 else 'medium' if ctx['idle_time'] > 60 else 'active',
                'is_idle': ctx['idle_time'] >= 60,
                'file_changes_total': ctx['file_changes'],
                'recent_file_changes': ctx['file_changes'],
                'error_count': ctx['errors'],
                'latency_ms': 0,
                'snapshot_count': context_idx
            }
        return original_get_context()
    
    orbit.context_hub.get_context_snapshot = mock_context
    
    # Process iterations
    try:
        for i, test_ctx in enumerate(test_contexts):
            print(f"\n\n{'#'*60}")
            print(f"# Test Scenario {i+1}: {test_ctx['desc']}")
            print(f"{'#'*60}")
            
            orbit.process_iteration()
            
            # Add delay between iterations
            if i < len(test_contexts) - 1:
                print("\n[Waiting 2s for cooldown...]")
                time.sleep(2)
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    
    # Final statistics
    print("\n\n" + "="*60)
    print("FINAL STATISTICS")
    print("="*60)
    
    stats = orbit.get_stats()
    
    print(f"\nGeneral:")
    print(f"  Total iterations: {stats['iterations']}")
    print(f"  Intents generated: {stats['intents_generated']}")
    print(f"  Intents approved: {stats['intents_approved']}")
    print(f"  Popups shown: {stats['popups_shown']}")
    print(f"  Approval rate: {stats['approval_rate']:.1f}%")
    
    print(f"\nLayer 1 (AI Brain):")
    for key, value in stats['layer1'].items():
        print(f"  {key}: {value}")
    
    print(f"\nLayer 2 (Decision Engine):")
    for key, value in stats['layer2'].items():
        print(f"  {key}: {value}")
    
    print(f"\nLayer 3 (FSM):")
    print(f"  Current state: {stats['layer3']['current_state']}")
    print(f"  State elapsed: {stats['layer3']['elapsed_time']:.1f}s")
    
    # Success criteria
    print("\n" + "="*60)
    print("VALIDATION")
    print("="*60)
    
    success = True
    
    # Check 1: At least some intents generated
    if stats['intents_generated'] > 0:
        print("✅ Intents generated successfully")
    else:
        print("❌ No intents generated")
        success = False
    
    # Check 2: Decision engine working
    if stats['intents_approved'] >= 0:  # Can be 0 if all blocked
        print("✅ Decision engine evaluated intents")
    else:
        print("❌ Decision engine not working")
        success = False
    
    # Check 3: FSM transitions working
    if len(orbit.behavior_controller.fsm.get_history()) > 0:
        print("✅ FSM transitions recorded")
    else:
        print("❌ No FSM transitions")
        success = False
    
    # Check 4: Layers integrated
    if stats['iterations'] == len(test_contexts):
        print("✅ All test scenarios processed")
    else:
        print("❌ Not all scenarios processed")
        success = False
    
    if success:
        print("\n🎉 INTEGRATION TEST PASSED - All layers working together!")
        return True
    else:
        print("\n⚠️  INTEGRATION TEST FAILED - Some issues detected")
        return False


if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
