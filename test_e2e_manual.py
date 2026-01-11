#!/usr/bin/env python3
"""
Manual End-to-End Test untuk ORBIT
Tests full pipeline: Context → AI → Decision → FSM → UI
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

import time
import logging
from backend.core.context_hub import ContextHub
from backend.core.ai_brain import AIBrain, AIMode
from backend.core.decision_engine import DecisionEngine
from backend.core.behavior_fsm import BehaviorController

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_full_pipeline():
    """Test complete ORBIT pipeline"""
    logger.info("=" * 60)
    logger.info("🧪 ORBIT End-to-End Test")
    logger.info("=" * 60)
    
    # Initialize all layers
    logger.info("🔧 Initializing layers...")
    context_hub = ContextHub()
    ai_brain = AIBrain(mode=AIMode.DUMMY)
    decision_engine = DecisionEngine()
    behavior_controller = BehaviorController()
    
    # Test Case 1: Normal flow dengan approval
    logger.info("\n📋 Test Case 1: Normal flow (intent approved)")
    logger.info("-" * 60)
    
    context = context_hub.get_context_snapshot()
    logger.info(f"✅ Layer 0 - Context: {context.get('active_app', 'N/A')}, idle={context.get('idle_time', 0)}s")
    
    intent = ai_brain.generate_intent(context)
    if intent:
        logger.info(f"✅ Layer 1 - Intent: {intent.type} (confidence={intent.confidence})")
    else:
        logger.warning("⚠️ Layer 1 - No intent generated")
    
    decision = decision_engine.evaluate(intent, context)
    logger.info(f"✅ Layer 2 - Decision: approved={decision.approved}, reason={decision.reason}")
    
    ui_output = behavior_controller.process_decision(decision)
    if ui_output:
        logger.info(f"✅ Layer 3 - FSM State: {ui_output['state']}")
        logger.info(f"   Bubble: {ui_output.get('bubble', {}).get('text', 'N/A')}")
    else:
        logger.info("ℹ️ Layer 3 - No UI output (idle)")
    
    # Test Case 2: Dismiss + Cooldown
    logger.info("\n📋 Test Case 2: User dismisses → Cooldown")
    logger.info("-" * 60)
    
    if intent and intent.type != "none":
        behavior_controller.handle_user_dismiss()
        logger.info("✅ User dismissed intent")
        
        # Try to generate again immediately
        decision2 = decision_engine.evaluate(intent, context)
        logger.info(f"✅ Layer 2 - Second attempt: approved={decision2.approved}")
        
        if not decision2.approved:
            logger.info(f"   Reason: {decision2.reason}")
            logger.info("✅ Cooldown working correctly!")
    else:
        logger.info("ℹ️ Skipping (no valid intent generated in Test Case 1)")
    
    # Test Case 3: Check FSM state
    logger.info("\n📋 Test Case 3: FSM State Management")
    logger.info("-" * 60)
    
    current_state = behavior_controller.get_current_state()
    logger.info(f"✅ Current FSM State: {current_state}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ End-to-End Test Complete!")
    logger.info("=" * 60)
    logger.info("\nNext Steps:")
    logger.info("1. Start backend: python main_v2.py")
    logger.info("2. Start frontend: cd frontend && npm run dev")
    logger.info("3. Open http://localhost:5173 in browser")
    logger.info("4. Observe Luna widget behavior")


if __name__ == "__main__":
    test_full_pipeline()
