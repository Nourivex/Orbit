"""
AI Brain v2 - Layer 1 Enhanced
Hybrid Ollama + Dummy with graceful fallback and variatif responses
"""

import random
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    
from core.decision_engine import Intent, IntentType
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AIMode(Enum):
    """AI operation modes"""
    OLLAMA = "ollama"
    DUMMY = "dummy"
    AUTO = "auto"


class DummyModePool:
    """
    Pool of variatif dummy responses (loaded from JSON)
    Ensures no repetition and context-aware suggestions
    """
    
    def __init__(self, responses_path: str = "data/dummy_responses.json"):
        self.responses = self._load_responses(responses_path)
        self.last_message = None
        self.last_suggest_time = 0
        self.usage_count = {}  # Track message usage
    
    def _load_responses(self, path: str) -> Dict:
        """Load dummy responses from JSON file"""
        try:
            # Try multiple paths
            paths_to_try = [
                Path(__file__).parent.parent / path,  # backend/data/...
                Path(__file__).parent.parent.parent / "backend" / path,  # root -> backend/data/...
                Path(path)  # absolute
            ]
            
            for json_path in paths_to_try:
                if json_path.exists():
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    logger.info(f"✅ Loaded {len(data.get('suggest_help', []))} dummy responses from {json_path}")
                    return data
            
            logger.warning(f"⚠️ Could not find dummy responses file: {path}")
            return self._get_fallback_responses()
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load dummy responses: {e}")
            return self._get_fallback_responses()
    
    def _get_fallback_responses(self) -> Dict:
        """Fallback responses if JSON loading fails"""
        return {
            "suggest_help": [
                "Butuh bantuan?",
                "Mau aku bantu?",
                "Lagi stuck nih?",
                "Ada yang bisa ku bantu?",
                "Mau diskusi masalahnya?"
            ]
        }
    
    def get_message(self, intent_type: IntentType, context: Dict[str, Any] = None) -> str:
        """
        Get variatif message based on intent type and context
        
        Args:
            intent_type: Type of intent
            context: Optional context for smarter selection
            
        Returns:
            Random message (no repetition)
        """
        if intent_type == IntentType.SUGGEST_HELP:
            # Enforce 15-minute minimum between suggestions (reduced to 30s for testing)
            now = time.time()
            if now - self.last_suggest_time < 30:  # 30 seconds for v0.2 testing
                logger.debug(f"Dummy mode cooldown active ({int(now - self.last_suggest_time)}s since last)")
                return None
            
            # Choose message pool based on context
            messages = self._select_pool(context)
            
            # Filter out last message and pick least-used
            available = [m for m in messages if m != self.last_message]
            
            if not available:
                available = messages  # Reset if all used
            
            # Pick least-used message (gacha-style with weight)
            available.sort(key=lambda m: self.usage_count.get(m, 0))
            
            # Weighted random (favor least-used)
            weights = [1 / (self.usage_count.get(m, 0) + 1) for m in available]
            msg = random.choices(available, weights=weights, k=1)[0]
            
            # Update tracking
            self.last_message = msg
            self.last_suggest_time = now
            self.usage_count[msg] = self.usage_count.get(msg, 0) + 1
            
            logger.info(f"💭 Dummy gacha: '{msg}' (used {self.usage_count[msg]}x)")
            return msg
        
        return ""
    
    def _select_pool(self, context: Dict[str, Any]) -> list:
        """Select appropriate message pool based on context"""
        if not context:
            return self.responses.get("suggest_help", [])
        
        idle_time = context.get('idle_time', 0)
        error_count = context.get('error_count', 0)
        hour = datetime.now().hour
        
        # Context-aware selection
        if error_count > 0 and 'contexts' in self.responses:
            ctx_messages = self.responses['contexts'].get('error_detected', [])
            if ctx_messages:
                return ctx_messages
        
        if idle_time >= 600 and 'contexts' in self.responses:  # 10 minutes
            ctx_messages = self.responses['contexts'].get('long_idle', [])
            if ctx_messages:
                return ctx_messages
        
        # Time-based mood
        if 'moods' in self.responses:
            if 5 <= hour < 12:
                mood_messages = self.responses['moods'].get('morning', [])
            elif 12 <= hour < 17:
                mood_messages = self.responses['moods'].get('afternoon', [])
            elif 17 <= hour < 22:
                mood_messages = self.responses['moods'].get('evening', [])
            else:
                mood_messages = self.responses['moods'].get('night', [])
            
            if mood_messages:
                # Mix mood + suggest_help (50/50)
                return mood_messages + self.responses.get("suggest_help", [])
        
        return self.responses.get("suggest_help", [])
    
    def get_confidence(self, context: Dict[str, Any]) -> float:
        """
        Calculate realistic confidence score
        
        Args:
            context: Context snapshot
            
        Returns:
            Confidence score (0.70-0.90)
        """
        idle_time = context.get('idle_time', 0)
        error_count = context.get('error_count', 0)
        
        # Base confidence
        confidence = 0.70
        
        # Boost for longer idle
        if idle_time >= 300:
            confidence += 0.10
        elif idle_time >= 180:
            confidence += 0.05
        
        # Boost for errors
        if error_count > 0:
            confidence += 0.05
        
        # Add slight randomness (more realistic)
        confidence += random.uniform(-0.03, 0.03)
        
        return min(0.90, max(0.70, confidence))


class OllamaClient:
    """
    Ollama LLM client with health check and retry logic
    """
    
    def __init__(self, model: str = "llama3.2", timeout: float = 5.0):
        self.model = model
        self.timeout = timeout
        self.available = False
        self.check_health()
    
    def check_health(self) -> bool:
        """
        Check Ollama service health
        
        Returns:
            True if Ollama is available
        """
        if not OLLAMA_AVAILABLE:
            logger.warning("⚠️ ollama library not installed")
            self.available = False
            return False
        
        try:
            # Try to list models (ollama.list() returns ListResponse object)
            response = ollama.list()
            
            # Extract models list from response (ListResponse.models attribute)
            models_list = response.models if hasattr(response, 'models') else []
            
            if not models_list:
                logger.warning("⚠️ No Ollama models found")
                self.available = False
                return False
            
            # Extract model names (Model objects have .model attribute)
            model_names = [m.model for m in models_list if hasattr(m, 'model')]
            
            if not model_names:
                logger.warning("⚠️ Could not parse model names")
                self.available = False
                return False
            
            # Check if our model exists (try exact and :latest suffix)
            if self.model not in model_names and f"{self.model}:latest" not in model_names:
                logger.warning(f"⚠️ Model '{self.model}' not found. Available: {model_names[:5]}")
                
                # Try llama3.1:8b as realistic fallback
                if "llama3.1:8b" in model_names:
                    self.model = "llama3.1:8b"
                    logger.info(f"✅ Using fallback model: {self.model}")
                elif "gemma3:4b" in model_names:
                    self.model = "gemma3:4b"
                    logger.info(f"✅ Using fallback model: {self.model}")
                else:
                    # Use first available model
                    self.model = model_names[0]
                    logger.info(f"✅ Using available model: {self.model}")
            
            self.available = True
            logger.info(f"✅ Ollama health check passed (model: {self.model})")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Ollama health check failed: {e}")
            self.available = False
            return False
    
    def generate_intent(self, context: Dict[str, Any]) -> Optional[Intent]:
        """
        Generate intent using Ollama LLM
        
        Args:
            context: Context snapshot
            
        Returns:
            Intent or None if failed
        """
        if not self.available:
            return None
        
        prompt = self._build_prompt(context)
        
        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                system=self._get_system_prompt(),
                format='json',
                options={
                    'temperature': 0.7,
                    'timeout': self.timeout
                }
            )
            
            output = response.get('response', '{}')
            
            # Parse JSON
            import json
            try:
                intent_data = json.loads(output)
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON output")
                return None
            
            # Parse intent type (LOCKED to suggest_help or none)
            intent_type = IntentType.NONE
            intent_str = intent_data.get("intent", "none").lower()
            
            if "suggest_help" in intent_str or "help" in intent_str:
                intent_type = IntentType.SUGGEST_HELP
            # remind & info LOCKED OUT for v0.2
            
            confidence = float(intent_data.get("confidence", 0.5))
            message = intent_data.get("message", "")
            reasoning = intent_data.get("reasoning", "")
            
            # ⚠️ reasoning is internal only (never to UI/DB)
            logger.debug(f"LLM reasoning (internal): {reasoning}")
            
            return Intent(
                type=intent_type,
                confidence=confidence,
                message=message,
                reasoning=""  # Strip reasoning before returning
            )
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """Get Luna system prompt"""
        return """Kamu adalah Luna, AI assistant untuk ORBIT.
Kepribadian: Ramah, informatif, dan pendukung.
Gaya bahasa: Santai namun profesional dalam Bahasa Indonesia.
Suara: Tenang dan meyakinkan.

Tugasmu: Mengamati konteks user dan memberikan saran HANYA jika benar-benar dibutuhkan.
Jangan mengganggu atau spam. Bersikap humble dan tidak memaksa."""
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build context-aware prompt"""
        return f"""Analisis konteks user berikut:

Context:
- Active window: {context.get('active_app', 'Unknown')}
- Idle time: {context.get('idle_time', 0)} seconds
- Recent file changes: {context.get('recent_file_changes', 0)}
- Time of day: {datetime.now().strftime('%H:%M')}

Based on this context, decide on ONE action:
1. "suggest_help" - User might need assistance
2. "none" - No action needed (user is focused)

⚠️ ALLOWED INTENTS (v0.2): suggest_help, none ONLY

Respond in JSON:
{{
  "intent": "suggest_help",
  "confidence": 0.85,
  "reasoning": "User idle 5min in coding app, might be stuck",
  "message": "Kamu lagi stuck? Mau aku bantu debug atau cari solusi?"
}}

⚠️ Field `reasoning` is strictly internal and never surfaced to UI or persisted.
Keep message in Bahasa Indonesia, casual tone, max 80 chars."""


class AIBrainV2:
    """
    AI Brain v2 - Hybrid Ollama + Dummy with graceful fallback
    """
    
    def __init__(
        self,
        mode: AIMode = AIMode.AUTO,
        model: str = "llama3.2",
        timeout: float = 5.0
    ):
        self.mode = mode
        self.ollama_client = None
        self.dummy_pool = DummyModePool()
        
        # Statistics
        self.stats = {
            'ollama_calls': 0,
            'dummy_calls': 0,
            'failures': 0,
            'total_intents': 0
        }
        
        logger.info(f"AIBrainV2 initialized (mode: {mode.value}, model: {model})")
        
        # Initialize Ollama if needed
        if mode in (AIMode.OLLAMA, AIMode.AUTO):
            self.ollama_client = OllamaClient(model=model, timeout=timeout)
            
            if not self.ollama_client.available and mode == AIMode.OLLAMA:
                logger.error("❌ OLLAMA mode requested but service unavailable!")
            elif not self.ollama_client.available and mode == AIMode.AUTO:
                logger.info("🔄 AUTO mode: Ollama unavailable, using Dummy")
    
    def generate_intent(self, context: Dict[str, Any]) -> Intent:
        """
        Generate intent with hybrid approach
        
        Args:
            context: Context snapshot
            
        Returns:
            Intent proposal
        """
        self.stats['total_intents'] += 1
        
        # Try Ollama first if available
        if self.ollama_client and self.ollama_client.available:
            intent = self.ollama_client.generate_intent(context)
            
            if intent:
                self.stats['ollama_calls'] += 1
                logger.info(f"🧠 Intent via Ollama: {intent.type.value} (conf: {intent.confidence:.2f})")
                return intent
            else:
                self.stats['failures'] += 1
                logger.warning("⚠️ Ollama failed, falling back to Dummy")
                
                # Retry health check
                if self.mode == AIMode.AUTO:
                    self.ollama_client.check_health()
        
        # Fallback to Dummy
        return self._generate_with_dummy(context)
    
    def _generate_with_dummy(self, context: Dict[str, Any]) -> Intent:
        """Generate intent using dummy pool with gacha system"""
        self.stats['dummy_calls'] += 1
        
        idle_time = context.get('idle_time', 0)
        active_app = context.get('active_app', '').lower()
        
        # Rule: Idle in coding app (lowered to 60s for v0.2 testing, will be 300s in production)
        if idle_time >= 60 and ('code' in active_app or 'studio' in active_app or 'python' in active_app):
            message = self.dummy_pool.get_message(IntentType.SUGGEST_HELP, context)
            if message:
                confidence = self.dummy_pool.get_confidence(context)
                logger.info(f"💭 Intent via Dummy: suggest_help (conf: {confidence:.2f})")
                return Intent(
                    type=IntentType.SUGGEST_HELP,
                    confidence=confidence,
                    message=message,
                    reasoning=""  # Internal only
                )
        
        # Default: no intent
        logger.debug("💭 Dummy: no interesting context")
        return Intent(
            type=IntentType.NONE,
            confidence=0.0,
            message="",
            reasoning=""
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return {
            **self.stats,
            'mode': self.mode.value,
            'ollama_available': self.ollama_client.available if self.ollama_client else False
        }


# Export for compatibility
AIBrain = AIBrainV2


def test_ai_brain_v2():
    """Test AI Brain v2"""
    print("\n" + "="*60)
    print("AI Brain V2 Test")
    print("="*60)
    
    # Test DUMMY mode explicitly
    brain = AIBrainV2(mode=AIMode.DUMMY)
    
    print(f"\nMode: {brain.mode.value}")
    if brain.ollama_client:
        print(f"Ollama available: {brain.ollama_client.available}")
    
    # Test context
    context = {
        "active_app": "Code.exe",
        "window_title": "main.py",
        "idle_time": 350,
        "recent_file_changes": 2,
        "error_count": 1
    }
    
    print("\nGenerating intents with DUMMY mode (gacha system)...")
    for i in range(5):
        print(f"\n--- Attempt {i+1} ---")
        intent = brain.generate_intent(context)
        print(f"Intent: {intent.type.value}")
        print(f"Confidence: {intent.confidence:.2f}")
        print(f"Message: {intent.message}")
        
        # Wait to bypass cooldown for first attempt
        if i == 0:
            time.sleep(901)  # 15 min + 1 sec
    
    print("\n" + "-"*60)
    print("Statistics:")
    for k, v in brain.get_stats().items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    test_ai_brain_v2()
