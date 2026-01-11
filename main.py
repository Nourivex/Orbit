"""
ORBIT Main Orchestrator
Coordinates all layers and runs the complete system
"""

import time
import sys
import signal
import json
from pathlib import Path
from threading import Thread, Event
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.core.context_hub import ContextHub
from backend.core.ai_brain import AIBrain, AIMode
from backend.core.decision_engine import DecisionEngine
from backend.core.behavior_fsm import BehaviorController, State
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class ORBITOrchestrator:
    """
    Main orchestrator for ORBIT
    Runs all layers in coordinated loop
    """
    
    def __init__(
        self,
        ai_mode: AIMode = AIMode.AUTO,
        polling_interval: float = 5.0,
        config_path: Optional[str] = None
    ):
        """
        Initialize ORBIT orchestrator
        
        Args:
            ai_mode: AI operation mode (auto, ollama, dummy)
            polling_interval: Seconds between context checks
            config_path: Path to configuration file
        """
        logger.info("="*60)
        logger.info("🚀 Starting ORBIT (Observant Robotic Behavioral Intelligence Tool)")
        logger.info("="*60)
        
        self.polling_interval = polling_interval
        self.config = self._load_config(config_path) if config_path else {}
        
        # Initialize all layers
        logger.info("\n📦 Initializing layers...")
        
        # Layer 0: Context Hub
        self.context_hub = ContextHub(
            polling_interval=polling_interval,
            watch_path=self.config.get('watch_path')
        )
        logger.info("  ✅ Layer 0 (Context Hub)")
        
        # Layer 1: AI Brain
        self.ai_brain = AIBrain(
            mode=ai_mode,
            model=self.config.get('ai_model', 'llama3.2')
        )
        logger.info(f"  ✅ Layer 1 (AI Brain) - mode: {ai_mode.value}")
        
        # Layer 2: Decision Engine
        self.decision_engine = DecisionEngine()
        logger.info("  ✅ Layer 2 (Decision Engine)")
        
        # Layer 3: Behavior FSM
        self.behavior_controller = BehaviorController()
        logger.info("  ✅ Layer 3 (Behavior FSM)")
        
        # Control
        self._running = Event()
        self._paused = Event()
        self._main_thread: Optional[Thread] = None
        
        # Statistics
        self.stats = {
            'start_time': time.time(),
            'iterations': 0,
            'contexts_processed': 0,
            'intents_generated': 0,
            'intents_approved': 0,
            'popups_shown': 0,
            'user_dismisses': 0
        }
        
        logger.info("\n✨ ORBIT initialized successfully\n")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                if config_path.endswith('.json'):
                    return json.load(f)
                # Add TOML support if needed
            return {}
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
            return {}
    
    def start(self):
        """Start ORBIT orchestrator"""
        if self._running.is_set():
            logger.warning("ORBIT already running")
            return
        
        logger.info("▶️  Starting ORBIT main loop...")
        
        # Start context monitoring
        self.context_hub.start(save_to_db=True)
        
        # Start main loop thread
        self._running.set()
        self._main_thread = Thread(target=self._main_loop, daemon=False)
        self._main_thread.start()
        
        logger.info("✅ ORBIT is now running\n")
    
    def stop(self):
        """Stop ORBIT orchestrator"""
        logger.info("\n🛑 Stopping ORBIT...")
        
        self._running.clear()
        
        # Stop context hub
        self.context_hub.stop()
        
        # Wait for main thread
        if self._main_thread:
            self._main_thread.join(timeout=5)
        
        # Print final stats
        self._print_stats()
        
        logger.info("✅ ORBIT stopped\n")
    
    def pause(self):
        """Pause ORBIT (stop generating intents)"""
        self._paused.set()
        logger.info("⏸️  ORBIT paused")
    
    def resume(self):
        """Resume ORBIT"""
        self._paused.clear()
        logger.info("▶️  ORBIT resumed")
    
    def _main_loop(self):
        """Main orchestration loop"""
        logger.info("🔄 Main loop started\n")
        
        while self._running.is_set():
            try:
                # Check if paused
                if self._paused.is_set():
                    time.sleep(1)
                    continue
                
                self.stats['iterations'] += 1
                
                # Get current context (Layer 0)
                context = self.context_hub.get_context_snapshot()
                self.stats['contexts_processed'] += 1
                
                # Handle context change in FSM
                self.behavior_controller.handle_context_change(context)
                
                # Tick FSM (check timeouts)
                self.behavior_controller.tick()
                
                current_state = self.behavior_controller.fsm.current_state
                
                # Only generate intent if in OBSERVING state
                if current_state == State.OBSERVING:
                    # Generate intent (Layer 1)
                    intent = self.ai_brain.generate_intent(context)
                    self.stats['intents_generated'] += 1
                    
                    if intent.type.value != "none":
                        # Evaluate with decision engine (Layer 2)
                        decision = self.decision_engine.evaluate(intent, context)
                        
                        if decision.approved:
                            self.stats['intents_approved'] += 1
                            
                            # Transition to SUGGESTING
                            self.behavior_controller.handle_intent_approved(intent)
                            self.stats['popups_shown'] += 1
                            
                            # Get UI output
                            ui_output = self.behavior_controller.fsm.get_ui_output()
                            
                            # Log popup
                            logger.info(f"💬 POPUP: {ui_output.bubble.get('text', '')}")
                            
                            # TODO: Send to UI via IPC
                            # For now, auto-dismiss after 10 seconds for demo
                            time.sleep(10)
                            self.behavior_controller.handle_user_dismiss()
                            self.decision_engine.handle_user_dismiss()
                            self.stats['user_dismisses'] += 1
                    else:
                        # No intent, return to idle
                        self.behavior_controller.fsm.trigger_event(
                            self.behavior_controller.fsm.Event.TIMEOUT
                        )
                
                # Sleep until next iteration
                time.sleep(self.polling_interval)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(self.polling_interval)
        
        logger.info("🔄 Main loop stopped")
    
    def _print_stats(self):
        """Print final statistics"""
        runtime = time.time() - self.stats['start_time']
        
        logger.info("\n" + "="*60)
        logger.info("📊 ORBIT Session Statistics")
        logger.info("="*60)
        logger.info(f"Runtime: {runtime:.1f}s ({runtime/60:.1f} minutes)")
        logger.info(f"Iterations: {self.stats['iterations']}")
        logger.info(f"Contexts processed: {self.stats['contexts_processed']}")
        logger.info(f"Intents generated: {self.stats['intents_generated']}")
        logger.info(f"Intents approved: {self.stats['intents_approved']}")
        logger.info(f"Popups shown: {self.stats['popups_shown']}")
        logger.info(f"User dismisses: {self.stats['user_dismisses']}")
        
        if self.stats['intents_generated'] > 0:
            approval_rate = (self.stats['intents_approved'] / self.stats['intents_generated']) * 100
            logger.info(f"Approval rate: {approval_rate:.1f}%")
        
        logger.info("="*60 + "\n")
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            'running': self._running.is_set(),
            'paused': self._paused.is_set(),
            'current_state': self.behavior_controller.fsm.current_state.value,
            'stats': self.stats.copy(),
            'layer0': self.context_hub.get_stats(),
            'layer1': self.ai_brain.get_stats(),
            'layer2': self.decision_engine.get_stats()
        }


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global orbit
    logger.info("\n\n⚠️  Received interrupt signal")
    if orbit:
        orbit.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    global orbit
    
    # Parse args (simple version)
    ai_mode = AIMode.AUTO
    if len(sys.argv) > 1:
        mode_arg = sys.argv[1].lower()
        if mode_arg == "ollama":
            ai_mode = AIMode.OLLAMA
        elif mode_arg == "dummy":
            ai_mode = AIMode.DUMMY
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start orchestrator
    orbit = ORBITOrchestrator(ai_mode=ai_mode, polling_interval=10.0)
    
    try:
        orbit.start()
        
        # Keep running
        logger.info("Press Ctrl+C to stop\n")
        while orbit._running.is_set():
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Keyboard interrupt")
        orbit.stop()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        orbit.stop()
        sys.exit(1)


if __name__ == "__main__":
    orbit = None
    main()
