"""
Decision Engine - Layer 2
Rule-based system for validating and approving intents
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from utils.logger import setup_logger

logger = setup_logger(__name__)


class IntentType(Enum):
    """Types of intents ORBIT can generate"""
    SUGGEST_HELP = "suggest_help"
    REMIND = "remind"
    INFO = "info"
    NONE = "none"


@dataclass
class Intent:
    """Intent proposal from AI Brain or rule-based system"""
    type: IntentType
    confidence: float
    message: str
    reasoning: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionResult:
    """Result of decision engine evaluation"""
    approved: bool
    intent: Optional[Intent]
    reason: str
    next_allowed_time: Optional[str] = None


class CooldownManager:
    """Manages cooldown periods for intents and user actions"""
    
    def __init__(
        self,
        per_intent_cooldown: int = 10,       # 10s for v0.2 testing (180s production)
        global_cooldown: int = 5,            # 5s for v0.2 testing (60s production)
        dismiss_cooldown: int = 600          # 10 minutes
    ):
        """
        Initialize cooldown manager
        
        Args:
            per_intent_cooldown: Cooldown per intent type (seconds)
            global_cooldown: Global cooldown between any popups (seconds)
            dismiss_cooldown: Cooldown after user dismiss (seconds)
        """
        self.per_intent_cooldown = per_intent_cooldown
        self.global_cooldown = global_cooldown
        self.dismiss_cooldown = dismiss_cooldown
        
        # Tracking
        self._last_intent_time: Dict[IntentType, float] = {}
        self._last_popup_time: Optional[float] = None
        self._last_dismiss_time: Optional[float] = None
        
        logger.info(f"CooldownManager initialized (per-intent: {per_intent_cooldown}s, "
                   f"global: {global_cooldown}s, dismiss: {dismiss_cooldown}s)")
        logger.info("⚠️ Using v0.2 TESTING thresholds (will restore production values after validation)")
    
    def can_show_intent(self, intent_type: IntentType) -> tuple[bool, str]:
        """
        Check if intent can be shown based on cooldowns
        
        Args:
            intent_type: Type of intent to check
            
        Returns:
            Tuple of (can_show, reason)
        """
        now = time.time()
        
        # Check dismiss cooldown (highest priority)
        if self._last_dismiss_time:
            elapsed = now - self._last_dismiss_time
            if elapsed < self.dismiss_cooldown:
                remaining = self.dismiss_cooldown - elapsed
                return False, f"User dismissed recently (wait {int(remaining)}s)"
        
        # Check global cooldown
        if self._last_popup_time:
            elapsed = now - self._last_popup_time
            if elapsed < self.global_cooldown:
                remaining = self.global_cooldown - elapsed
                return False, f"Global cooldown active (wait {int(remaining)}s)"
        
        # Check per-intent cooldown
        if intent_type in self._last_intent_time:
            elapsed = now - self._last_intent_time[intent_type]
            if elapsed < self.per_intent_cooldown:
                remaining = self.per_intent_cooldown - elapsed
                return False, f"Intent cooldown active (wait {int(remaining)}s)"
        
        return True, "Cooldown passed"
    
    def record_popup(self, intent_type: IntentType):
        """Record that a popup was shown"""
        now = time.time()
        self._last_popup_time = now
        self._last_intent_time[intent_type] = now
        logger.debug(f"Recorded popup: {intent_type.value}")
    
    def record_dismiss(self):
        """Record that user dismissed a popup"""
        self._last_dismiss_time = time.time()
        logger.info("User dismissed popup - dismiss cooldown activated")
    
    def get_next_allowed_time(self, intent_type: IntentType) -> Optional[str]:
        """Get next time this intent can be shown"""
        now = time.time()
        next_times = []
        
        # Check all cooldowns and get the furthest time
        if self._last_dismiss_time:
            next_times.append(self._last_dismiss_time + self.dismiss_cooldown)
        
        if self._last_popup_time:
            next_times.append(self._last_popup_time + self.global_cooldown)
        
        if intent_type in self._last_intent_time:
            next_times.append(self._last_intent_time[intent_type] + self.per_intent_cooldown)
        
        if not next_times:
            return None
        
        next_time = max(next_times)
        if next_time <= now:
            return None
        
        return datetime.fromtimestamp(next_time).isoformat()
    
    def reset(self):
        """Reset all cooldowns (for testing)"""
        self._last_intent_time.clear()
        self._last_popup_time = None
        self._last_dismiss_time = None
        logger.info("All cooldowns reset")


class SpamFilter:
    """Filters out spammy or repetitive intents"""
    
    def __init__(
        self,
        max_popups_per_hour: int = 100,      # 100 for v0.2 testing (5 production)
        same_intent_window: int = 15         # 15s for v0.2 testing (900s production)
    ):
        """
        Initialize spam filter
        
        Args:
            max_popups_per_hour: Maximum popups allowed per hour
            same_intent_window: Seconds to consider same intent as spam
        """
        self.max_popups_per_hour = max_popups_per_hour
        self.same_intent_window = same_intent_window
        
        # Tracking
        self._popup_history: List[float] = []
        self._intent_history: Dict[IntentType, List[float]] = {}
        
        logger.info(f"SpamFilter initialized (max/hour: {max_popups_per_hour}, "
                   f"same window: {same_intent_window}s)")
        logger.info("⚠️ Using v0.2 TESTING thresholds (will restore production values after validation)")
    
    def is_spam(self, intent_type: IntentType) -> tuple[bool, str]:
        """
        Check if intent would be considered spam
        
        Args:
            intent_type: Type of intent to check
            
        Returns:
            Tuple of (is_spam, reason)
        """
        now = time.time()
        
        # Clean old history
        self._cleanup_old_history(now)
        
        # Check popups per hour
        if len(self._popup_history) >= self.max_popups_per_hour:
            return True, f"Max popups/hour reached ({self.max_popups_per_hour})"
        
        # Check same intent repetition
        if intent_type in self._intent_history:
            recent = [t for t in self._intent_history[intent_type] 
                     if now - t < self.same_intent_window]
            if len(recent) > 0:
                return True, f"Same intent shown recently (<{self.same_intent_window}s)"
        
        return False, "Not spam"
    
    def record_popup(self, intent_type: IntentType):
        """Record that a popup was shown"""
        now = time.time()
        self._popup_history.append(now)
        
        if intent_type not in self._intent_history:
            self._intent_history[intent_type] = []
        self._intent_history[intent_type].append(now)
        
        logger.debug(f"Recorded in spam filter: {intent_type.value}")
    
    def _cleanup_old_history(self, now: float):
        """Remove history older than 1 hour"""
        cutoff = now - 3600  # 1 hour
        
        # Clean popup history
        self._popup_history = [t for t in self._popup_history if t > cutoff]
        
        # Clean intent history
        for intent_type in list(self._intent_history.keys()):
            self._intent_history[intent_type] = [
                t for t in self._intent_history[intent_type] if t > cutoff
            ]
            if not self._intent_history[intent_type]:
                del self._intent_history[intent_type]
    
    def reset(self):
        """Reset spam filter (for testing)"""
        self._popup_history.clear()
        self._intent_history.clear()
        logger.info("Spam filter reset")


class ConfidenceDecay:
    """Manages confidence decay for intents"""
    
    def __init__(self):
        """Initialize confidence decay tracker"""
        self._dismiss_count: Dict[IntentType, int] = {}
        self._last_context: Optional[Dict[str, Any]] = None
        
        logger.info("ConfidenceDecay initialized")
    
    def apply_decay(
        self,
        intent: Intent,
        context: Dict[str, Any],
        time_since_generation: float
    ) -> float:
        """
        Apply confidence decay based on various factors
        
        Args:
            intent: Intent to decay
            context: Current context
            time_since_generation: Seconds since intent was generated
            
        Returns:
            Decayed confidence value
        """
        confidence = intent.confidence
        
        # Decay 1: Repeated dismissals
        dismiss_count = self._dismiss_count.get(intent.type, 0)
        if dismiss_count > 0:
            decay = 0.1 * dismiss_count  # 10% per dismiss
            confidence -= decay
            logger.debug(f"Dismiss decay: -{decay:.2f} ({dismiss_count} dismisses)")
        
        # Decay 2: Context change
        if self._last_context:
            if self._context_changed_significantly(context):
                confidence -= 0.15  # 15% decay for context change
                logger.debug("Context change decay: -0.15")
        
        # Decay 3: Time passed
        if time_since_generation > 60:  # After 1 minute
            time_decay = min(0.2, (time_since_generation / 300) * 0.2)  # Max 20% over 5 min
            confidence -= time_decay
            logger.debug(f"Time decay: -{time_decay:.2f}")
        
        # Update context
        self._last_context = context.copy()
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))
    
    def record_dismiss(self, intent_type: IntentType):
        """Record that an intent was dismissed"""
        self._dismiss_count[intent_type] = self._dismiss_count.get(intent_type, 0) + 1
        logger.info(f"Recorded dismiss for {intent_type.value} "
                   f"(total: {self._dismiss_count[intent_type]})")
    
    def _context_changed_significantly(self, new_context: Dict[str, Any]) -> bool:
        """Check if context changed significantly"""
        if not self._last_context:
            return False
        
        # Check app change
        if self._last_context.get('active_app') != new_context.get('active_app'):
            return True
        
        # Check idle state change
        if (self._last_context.get('is_idle') != new_context.get('is_idle')):
            return True
        
        return False
    
    def reset(self):
        """Reset decay tracker (for testing)"""
        self._dismiss_count.clear()
        self._last_context = None
        logger.info("Confidence decay reset")


class DecisionEngine:
    """
    Layer 2 - Decision Engine
    Validates and approves intents based on rules and policies
    """
    
    CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self):
        """Initialize decision engine with all components"""
        self.cooldown_manager = CooldownManager()
        self.spam_filter = SpamFilter()
        self.confidence_decay = ConfidenceDecay()
        
        logger.info("DecisionEngine initialized")
    
    def evaluate(
        self,
        intent: Intent,
        context: Dict[str, Any],
        time_since_generation: float = 0.0
    ) -> DecisionResult:
        """
        Evaluate if intent should be approved
        
        Args:
            intent: Intent to evaluate
            context: Current system context
            time_since_generation: Seconds since intent was generated
            
        Returns:
            DecisionResult with approval status and reasoning
        """
        # Apply confidence decay
        decayed_confidence = self.confidence_decay.apply_decay(
            intent, context, time_since_generation
        )
        
        # Check 1: Confidence threshold
        if decayed_confidence < self.CONFIDENCE_THRESHOLD:
            return DecisionResult(
                approved=False,
                intent=intent,
                reason=f"Confidence too low: {decayed_confidence:.2f} < {self.CONFIDENCE_THRESHOLD}"
            )
        
        # Check 2: Cooldown
        can_show, cooldown_reason = self.cooldown_manager.can_show_intent(intent.type)
        if not can_show:
            next_time = self.cooldown_manager.get_next_allowed_time(intent.type)
            return DecisionResult(
                approved=False,
                intent=intent,
                reason=f"Cooldown: {cooldown_reason}",
                next_allowed_time=next_time
            )
        
        # Check 3: Spam filter
        is_spam, spam_reason = self.spam_filter.is_spam(intent.type)
        if is_spam:
            return DecisionResult(
                approved=False,
                intent=intent,
                reason=f"Spam filter: {spam_reason}"
            )
        
        # APPROVED
        logger.info(f"Intent APPROVED: {intent.type.value} (confidence: {decayed_confidence:.2f})")
        
        # Record for tracking
        self.cooldown_manager.record_popup(intent.type)
        self.spam_filter.record_popup(intent.type)
        
        return DecisionResult(
            approved=True,
            intent=intent,
            reason="All checks passed",
            next_allowed_time=self.cooldown_manager.get_next_allowed_time(intent.type)
        )
    
    def handle_user_dismiss(self):
        """Handle user dismissing a popup"""
        self.cooldown_manager.record_dismiss()
        logger.info("User dismiss handled")
    
    def handle_intent_dismissed(self, intent_type: IntentType):
        """Handle specific intent being dismissed"""
        self.confidence_decay.record_dismiss(intent_type)
        logger.info(f"Intent {intent_type.value} dismissed - decay recorded")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get decision engine statistics"""
        return {
            'cooldown_active': self.cooldown_manager._last_popup_time is not None,
            'popups_last_hour': len(self.spam_filter._popup_history),
            'dismiss_counts': dict(self.confidence_decay._dismiss_count)
        }
    
    def reset(self):
        """Reset all state (for testing)"""
        self.cooldown_manager.reset()
        self.spam_filter.reset()
        self.confidence_decay.reset()
        logger.info("DecisionEngine reset")
