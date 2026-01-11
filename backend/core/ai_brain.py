"""
AI Brain - Layer 1
LLM-powered reasoning with fallback to dummy mode
"""

import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from core.decision_engine import Intent, IntentType
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AIMode(Enum):
    """AI operation modes"""
    OLLAMA = "ollama"        # Use Ollama LLM
    DUMMY = "dummy"          # Use rule-based dummy responses
    AUTO = "auto"            # Auto-detect and fallback


class AIBrain:
    """
    Layer 1 - AI Brain
    Generates insights and intent proposals using LLM or dummy logic
    """
    
    # Luna's personality prompt
    SYSTEM_PROMPT = """Kamu adalah Luna, AI assistant untuk ORBIT.
Kepribadian: Ramah, informatif, dan pendukung.
Gaya bahasa: Santai namun profesional.
Suara: Tenang dan meyakinkan.

Tugasmu adalah mengamati konteks user dan memberikan saran yang membantu.
Kamu tidak boleh mengganggu atau spam.
Hanya berikan saran ketika benar-benar dibutuhkan.
"""
    
    def __init__(
        self,
        mode: AIMode = AIMode.AUTO,
        ollama_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout: float = 5.0
    ):
        """
        Initialize AI Brain
        
        Args:
            mode: Operation mode (ollama, dummy, auto)
            ollama_url: Ollama server URL
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.mode = mode
        self.ollama_url = ollama_url
        self.model = model
        self.timeout = timeout
        
        self._ollama_available = None
        self._fallback_to_dummy = False
        
        # Statistics
        self._intent_count = 0
        self._ollama_calls = 0
        self._dummy_calls = 0
        self._failures = 0
        
        logger.info(f"AIBrain initialized (mode: {mode.value}, model: {model})")
        
        # Check Ollama availability
        if mode in (AIMode.OLLAMA, AIMode.AUTO):
            self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> bool:
        """
        Check if Ollama is available
        
        Returns:
            True if Ollama is reachable
        """
        try:
            response = httpx.get(
                f"{self.ollama_url}/api/tags",
                timeout=2.0
            )
            self._ollama_available = response.status_code == 200
            
            if self._ollama_available:
                logger.info("✅ Ollama server detected and available")
            else:
                logger.warning("⚠️ Ollama server responded with non-200 status")
            
            return self._ollama_available
            
        except Exception as e:
            self._ollama_available = False
            logger.warning(f"⚠️ Ollama not available: {e}")
            
            if self.mode == AIMode.AUTO:
                logger.info("🔄 Auto mode: falling back to Dummy mode")
                self._fallback_to_dummy = True
            
            return False
    
    def generate_intent(self, context: Dict[str, Any]) -> Intent:
        """
        Generate intent based on context
        
        Args:
            context: Context snapshot from Layer 0
            
        Returns:
            Intent proposal
        """
        self._intent_count += 1
        
        # Determine which mode to use
        use_ollama = False
        
        if self.mode == AIMode.OLLAMA:
            use_ollama = self._ollama_available or self._check_ollama_availability()
        elif self.mode == AIMode.AUTO:
            if not self._fallback_to_dummy:
                use_ollama = self._ollama_available or self._check_ollama_availability()
        
        # Try Ollama first if available
        if use_ollama:
            try:
                intent = self._generate_with_ollama(context)
                self._ollama_calls += 1
                logger.info(f"🧠 Intent generated via Ollama: {intent.type.value}")
                return intent
                
            except Exception as e:
                logger.error(f"Ollama generation failed: {e}")
                self._failures += 1
                
                # Fallback to dummy if in AUTO mode
                if self.mode == AIMode.AUTO:
                    logger.info("🔄 Falling back to Dummy mode")
                    self._fallback_to_dummy = True
                else:
                    # Return low-confidence intent
                    return Intent(
                        type=IntentType.NONE,
                        confidence=0.0,
                        message="",
                        reasoning="LLM failed"
                    )
        
        # Use dummy mode
        intent = self._generate_with_dummy(context)
        self._dummy_calls += 1
        logger.info(f"💭 Intent generated via Dummy: {intent.type.value}")
        return intent
    
    def _generate_with_ollama(self, context: Dict[str, Any]) -> Intent:
        """
        Generate intent using Ollama LLM
        
        Args:
            context: Context snapshot
            
        Returns:
            Intent from LLM
        """
        # Build prompt
        prompt = self._build_prompt(context)
        
        # Call Ollama API
        response = httpx.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "system": self.SYSTEM_PROMPT,
                "stream": False,
                "format": "json"
            },
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")
        
        # Parse response
        result = response.json()
        output = result.get("response", "{}")
        
        try:
            intent_data = json.loads(output)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON, using dummy fallback")
            return self._generate_with_dummy(context)
        
        # Create Intent
        intent_type = IntentType.NONE
        intent_str = intent_data.get("intent", "none").lower()
        
        if "suggest_help" in intent_str or "help" in intent_str:
            intent_type = IntentType.SUGGEST_HELP
        elif "remind" in intent_str:
            intent_type = IntentType.REMIND
        elif "info" in intent_str:
            intent_type = IntentType.INFO
        
        return Intent(
            type=intent_type,
            confidence=float(intent_data.get("confidence", 0.5)),
            message=intent_data.get("message", ""),
            reasoning=intent_data.get("reasoning", "")
        )
    
    def _generate_with_dummy(self, context: Dict[str, Any]) -> Intent:
        """
        Generate intent using rule-based dummy logic
        
        Args:
            context: Context snapshot
            
        Returns:
            Intent from dummy rules
        """
        idle_time = context.get('idle_time', 0)
        active_app = context.get('active_app', '')
        error_count = context.get('error_count', 0)
        file_changes = context.get('recent_file_changes', 0)
        
        # Rule 1: Long idle + coding app
        if idle_time >= 300 and 'code' in active_app.lower():
            return Intent(
                type=IntentType.SUGGEST_HELP,
                confidence=0.85,
                message="Kamu idle 5 menit, mau aku rangkum progress hari ini?",
                reasoning="Long idle in coding app"
            )
        
        # Rule 2: Medium idle + errors
        if idle_time >= 180 and error_count > 0:
            return Intent(
                type=IntentType.SUGGEST_HELP,
                confidence=0.80,
                message="Ada error yang belum tertangani, mau aku bantu cek?",
                reasoning="Idle with errors"
            )
        
        # Rule 3: Lots of file changes
        if file_changes >= 5:
            return Intent(
                type=IntentType.INFO,
                confidence=0.75,
                message=f"Kamu sudah mengubah {file_changes} file, jangan lupa commit ya!",
                reasoning="Many file changes"
            )
        
        # Rule 4: Short idle (reminder)
        if idle_time >= 60 and idle_time < 180:
            return Intent(
                type=IntentType.REMIND,
                confidence=0.65,
                message="Sudah 1 menit idle, mau istirahat sebentar?",
                reasoning="Short idle period"
            )
        
        # Default: no intent
        return Intent(
            type=IntentType.NONE,
            confidence=0.0,
            message="",
            reasoning="No interesting context"
        )
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build prompt for LLM
        
        Args:
            context: Context snapshot
            
        Returns:
            Prompt string
        """
        prompt = f"""Analisis konteks berikut dan tentukan apakah user butuh bantuan:

Context:
- Active app: {context.get('active_app', 'Unknown')}
- Window title: {context.get('window_title', 'Unknown')}
- Idle time: {context.get('idle_time', 0)} detik
- Idle level: {context.get('idle_level', 'active')}
- Recent file changes: {context.get('recent_file_changes', 0)}
- Error count: {context.get('error_count', 0)}

Berikan output dalam format JSON:
{{
  "intent": "suggest_help" | "remind" | "info" | "none",
  "confidence": 0.0-1.0,
  "message": "pesan singkat untuk user (bahasa Indonesia, ramah)",
  "reasoning": "alasan kenapa memberikan saran ini"
}}

Jika konteks tidak menarik atau user terlihat sibuk, return "none" dengan confidence 0.0.
Jangan mengganggu jika tidak perlu.
"""
        return prompt
    
    def get_stats(self) -> Dict[str, Any]:
        """Get AI Brain statistics"""
        return {
            'mode': self.mode.value,
            'ollama_available': self._ollama_available,
            'fallback_to_dummy': self._fallback_to_dummy,
            'total_intents': self._intent_count,
            'ollama_calls': self._ollama_calls,
            'dummy_calls': self._dummy_calls,
            'failures': self._failures
        }
    
    def set_mode(self, mode: AIMode):
        """
        Change AI mode at runtime
        
        Args:
            mode: New mode to use
        """
        old_mode = self.mode
        self.mode = mode
        
        if mode in (AIMode.OLLAMA, AIMode.AUTO):
            self._check_ollama_availability()
        
        logger.info(f"AI mode changed: {old_mode.value} -> {mode.value}")


def test_ai_brain():
    """Test AI Brain with sample context"""
    print("\n" + "="*60)
    print("AI Brain Test")
    print("="*60)
    
    # Test AUTO mode (will use dummy if Ollama unavailable)
    brain = AIBrain(mode=AIMode.AUTO)
    
    print(f"\nMode: {brain.mode.value}")
    print(f"Ollama available: {brain._ollama_available}")
    print(f"Using dummy: {brain._fallback_to_dummy}")
    
    # Test contexts
    contexts = [
        {
            "active_app": "Code.exe",
            "window_title": "main.py - VSCode",
            "idle_time": 350,
            "idle_level": "long",
            "recent_file_changes": 2,
            "error_count": 0
        },
        {
            "active_app": "Chrome.exe",
            "window_title": "YouTube",
            "idle_time": 200,
            "idle_level": "medium",
            "recent_file_changes": 0,
            "error_count": 1
        },
        {
            "active_app": "Code.exe",
            "window_title": "app.py",
            "idle_time": 30,
            "idle_level": "active",
            "recent_file_changes": 8,
            "error_count": 0
        }
    ]
    
    print("\n" + "-"*60)
    for i, context in enumerate(contexts, 1):
        print(f"\nTest {i}:")
        print(f"  Context: {context['active_app']} - idle {context['idle_time']}s")
        
        intent = brain.generate_intent(context)
        
        print(f"  Intent: {intent.type.value}")
        print(f"  Confidence: {intent.confidence:.2f}")
        print(f"  Message: {intent.message}")
        print(f"  Reasoning: {intent.reasoning}")
    
    # Stats
    print("\n" + "-"*60)
    print("Statistics:")
    stats = brain.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_ai_brain()
