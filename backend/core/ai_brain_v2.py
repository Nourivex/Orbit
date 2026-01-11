"""
AI Brain v2 - Layer 1 Enhanced
Hybrid Ollama + Dummy with graceful fallback and variatif responses
"""

import random
import time
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

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
    Pool of variatif dummy responses
    Ensures no repetition and realistic suggestions
    """
    
    def __init__(self):
        self.suggest_help_messages = [
            "Sudah 5 menit idle nih, butuh bantuan?",
            "Lagi nyangkut? Aku bisa bantu cari solusi",
            "Kayaknya lagi mikir keras ya, mau diskusi?",
            "Mau aku rangkum progress hari ini?",
            "Lagi stuck? Yuk brainstorming bareng",
            "Butuh second opinion untuk kode ini?",
            "Mau aku bantu debug masalah ini?",
            "Kelihatannya lagi ribet, aku bisa support",
            "Udah lama idle, perlu assistance?",
            "Mau aku cari referensi buat masalah ini?",
            "Lagi nyari solusi? Aku bisa bantu explore",
            "Kayaknya ada yang ganjal, mau ku cek?",
            "Butuh fresh perspective? Aku ready",
            "Stuck di bagian mana? Cerita yuk",
            "Mau ku carikan docs atau contoh kode?",
        ]
        
        self.last_message = None
        self.last_suggest_time = 0
        self.usage_count = {}  # Track message usage
    
    def get_message(self, intent_type: IntentType) -> str:
        """
        Get variatif message based on intent type
        
        Args:
            intent_type: Type of intent
            
        Returns:
            Random message (no repetition)
        """
        if intent_type == IntentType.SUGGEST_HELP:
            # Enforce 15-minute minimum between suggestions
            now = time.time()
            if now - self.last_suggest_time < 900:  # 15 minutes
                logger.debug("Dummy mode cooldown active (15min rule)")
                return None
            
            # Filter out last message and least-used messages
            available = [m for m in self.suggest_help_messages if m != self.last_message]
            
            # Pick least-used message
            available.sort(key=lambda m: self.usage_count.get(m, 0))
            msg = available[0] if available else self.suggest_help_messages[0]
            
            # Update tracking
            self.last_message = msg
            self.last_suggest_time = now
            self.usage_count[msg] = self.usage_count.get(msg, 0) + 1
            
            return msg
        
        return ""
    
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
        """Generate intent using dummy pool"""
        self.stats['dummy_calls'] += 1
        
        idle_time = context.get('idle_time', 0)
        active_app = context.get('active_app', '').lower()
        
        # Rule: Long idle in coding app
        if idle_time >= 300 and ('code' in active_app or 'studio' in active_app):
            message = self.dummy_pool.get_message(IntentType.SUGGEST_HELP)
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
    
    brain = AIBrainV2(mode=AIMode.AUTO)
    
    print(f"\nMode: {brain.mode.value}")
    if brain.ollama_client:
        print(f"Ollama available: {brain.ollama_client.available}")
    
    # Test context
    context = {
        "active_app": "Code.exe",
        "window_title": "main.py",
        "idle_time": 350,
        "recent_file_changes": 2
    }
    
    print("\nGenerating intents...")
    for i in range(3):
        print(f"\n--- Attempt {i+1} ---")
        intent = brain.generate_intent(context)
        print(f"Intent: {intent.type.value}")
        print(f"Confidence: {intent.confidence:.2f}")
        print(f"Message: {intent.message}")
        time.sleep(1)
    
    print("\n" + "-"*60)
    print("Statistics:")
    for k, v in brain.get_stats().items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    test_ai_brain_v2()
