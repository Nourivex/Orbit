"""
ORBIT Main Orchestrator v2 - With IPC Support
Coordinates all layers and communicates with frontend UI
"""

import time
import sys
import signal
import json
import asyncio
import threading
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.core.context_hub import ContextHub
from backend.core.ai_brain_v2 import AIBrainV2, AIMode
from backend.core.decision_engine import DecisionEngine
from backend.core.behavior_fsm import BehaviorController, State
from backend.utils.logger import setup_logger
from backend.ipc_server import get_ipc_server

logger = setup_logger(__name__)


class ORBITOrchestrator:
    """Main orchestrator yang menjalankan semua layer ORBIT"""
    
    def __init__(self, config_path: str = "config/orbit_config.json"):
        self.running = False
        self.config = self._load_config(config_path)
        
        # Initialize all layers
        logger.info("🔧 Initializing ORBIT layers...")
        self.context_hub = ContextHub()
        
        ai_mode_str = self.config.get("ai_mode", "auto")
        if ai_mode_str == "ollama":
            ai_mode = AIMode.OLLAMA
        elif ai_mode_str == "dummy":
            ai_mode = AIMode.DUMMY
        else:
            ai_mode = AIMode.AUTO
        
        self.ai_brain = AIBrainV2(mode=ai_mode)
        
        self.decision_engine = DecisionEngine()
        self.behavior_controller = BehaviorController()
        
        # IPC Server
        self.ipc_server = get_ipc_server()
        self.ipc_loop = None
        self.ipc_thread = None
        
        # Stats
        self.stats = {
            "iterations": 0,
            "intents_generated": 0,
            "intents_approved": 0,
            "intents_rejected": 0,
            "errors": 0
        }
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _load_config(self, path: str) -> dict:
        """Load configuration dari JSON file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"⚠️ Config not found: {path}, using defaults")
            return {
                "ai_mode": "dummy",
                "polling_interval": 10,
                "log_level": "INFO"
            }
    
    def _signal_handler(self, signum, frame):
        """Handle CTRL+C gracefully"""
        logger.info(f"\n⚠️ Received signal {signum}")
        self.stop()
    
    def _start_ipc_server(self):
        """Start IPC WebSocket server in background thread"""
        def run_ipc():
            self.ipc_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.ipc_loop)
            self.ipc_loop.run_until_complete(self.ipc_server.start())
            self.ipc_loop.run_forever()
        
        self.ipc_thread = threading.Thread(target=run_ipc, daemon=True)
        self.ipc_thread.start()
        logger.info("✅ IPC Server started on ws://localhost:8765")
    
    def start(self):
        """Start ORBIT orchestrator"""
        logger.info("=" * 60)
        logger.info("🚀 Starting ORBIT Agent - Luna v0.1")
        logger.info("=" * 60)
        
        self.running = True
        
        # Start IPC server
        self._start_ipc_server()
        
        # Start context monitoring
        self.context_hub.start(save_to_db=True)
        logger.info("✅ Context monitoring started")
        
        # Run main loop
        self._main_loop()
    
    def _main_loop(self):
        """Main orchestration loop"""
        logger.info("🔄 Entering main orchestration loop")
        
        poll_interval = self.config.get("polling_interval", 10)
        
        while self.running:
            try:
                self.stats["iterations"] += 1
                
                # === LAYER 0: Get Context ===
                context = self.context_hub.get_context_snapshot()
                
                # === LAYER 1: Generate Intent ===
                intent = self.ai_brain.generate_intent(context)
                if intent:
                    self.stats["intents_generated"] += 1
                    logger.debug(f"💡 Intent generated: {intent.type}")
                
                # === LAYER 2: Evaluate Decision ===
                decision = self.decision_engine.evaluate(intent, context)
                
                if decision.approved:
                    self.stats["intents_approved"] += 1
                    logger.info(f"✅ Intent approved: {intent.type}")
                else:
                    self.stats["intents_rejected"] += 1
                    logger.debug(f"❌ Intent rejected: {decision.reason}")
                
                # === LAYER 3: FSM Processing ===
                ui_output = self.behavior_controller.process_decision(decision)
                
                if ui_output:
                    logger.info(f"🎨 FSM State: {ui_output.state}")
                    
                    # === LAYER 4: Send to UI ===
                    if self.ipc_loop and self.ipc_server.running:
                        # Convert UIOutput dataclass to dict
                        ui_dict = {
                            'state': ui_output.state,
                            'emotion': ui_output.emotion,
                            'visible': ui_output.visible,
                            'bubble': ui_output.bubble,
                            'actions': ui_output.actions
                        }
                        asyncio.run_coroutine_threadsafe(
                            self.ipc_server.send_ui_update(ui_dict),
                            self.ipc_loop
                        )
                
                # Sleep before next iteration
                time.sleep(poll_interval)
                
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                time.sleep(5)  # Wait before retry
    
    def stop(self):
        """Stop ORBIT gracefully"""
        logger.info("🛑 Stopping ORBIT...")
        self.running = False
        
        # Stop IPC
        if self.ipc_loop:
            asyncio.run_coroutine_threadsafe(
                self.ipc_server.stop(),
                self.ipc_loop
            )
            self.ipc_loop.call_soon_threadsafe(self.ipc_loop.stop)
        
        # Stop monitoring
        self.context_hub.stop()
        
        # Print stats
        logger.info("=" * 60)
        logger.info("📊 ORBIT Session Statistics:")
        logger.info(f"   Iterations: {self.stats['iterations']}")
        logger.info(f"   Intents Generated: {self.stats['intents_generated']}")
        logger.info(f"   Intents Approved: {self.stats['intents_approved']}")
        logger.info(f"   Intents Rejected: {self.stats['intents_rejected']}")
        logger.info(f"   Errors: {self.stats['errors']}")
        logger.info("=" * 60)
        logger.info("👋 ORBIT stopped. Goodbye!")
        sys.exit(0)


def main():
    """Entry point"""
    orchestrator = ORBITOrchestrator()
    orchestrator.start()


if __name__ == "__main__":
    main()
