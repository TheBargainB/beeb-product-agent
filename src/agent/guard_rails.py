"""
Minimal guard rails implementation for testing purposes.
"""

import time
import logging
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass


# Exception classes
class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass


class ContentSafetyViolation(Exception):
    """Raised when content safety check fails"""
    pass


class CostLimitExceeded(Exception):
    """Raised when cost limit is exceeded"""
    pass


@dataclass
class GuardRailsConfig:
    """Configuration for guard rails"""
    rate_limiting_enabled: bool = True
    content_safety_enabled: bool = True
    cost_controls_enabled: bool = True
    max_requests_per_minute: int = 30
    max_tokens_per_request: int = 4000
    max_message_length: int = 500
    graceful_degradation: bool = True
    
    @classmethod
    def from_runtime_config(cls, runtime_config: Dict[str, Any]) -> 'GuardRailsConfig':
        """Create GuardRailsConfig from runtime configuration."""
        return cls(
            rate_limiting_enabled=runtime_config.get('rate_limiting_enabled', True),
            content_safety_enabled=runtime_config.get('content_safety_enabled', True),
            cost_controls_enabled=runtime_config.get('cost_controls_enabled', True),
            max_requests_per_minute=runtime_config.get('max_requests_per_minute', 30),
            max_tokens_per_request=runtime_config.get('max_tokens_per_request', 4000),
            max_message_length=runtime_config.get('max_message_length', 500),
            graceful_degradation=runtime_config.get('graceful_degradation', True)
        )


class GuardRails:
    """Enhanced guard rails implementation with runtime configuration support"""
    
    def __init__(self, config: GuardRailsConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.user_requests = {}
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'response_times': [],
            'errors': []
        }
    
    def check_rate_limits(self, user_id: str) -> None:
        """Check rate limits for a user"""
        if not self.config.rate_limiting_enabled:
            return
        
        current_time = time.time()
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        # Remove old requests (older than 1 minute)
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id] 
            if current_time - req_time < 60
        ]
        
        if len(self.user_requests[user_id]) >= self.config.max_requests_per_minute:
            raise RateLimitExceeded(f"Rate limit exceeded for user {user_id}")
        
        self.user_requests[user_id].append(current_time)
    
    def validate_input_content(self, content: str, user_id: str) -> str:
        """Validate and sanitize input content"""
        if not self.config.content_safety_enabled:
            return content
        
        # Check message length
        if len(content) > self.config.max_message_length:
            raise ContentSafetyViolation(f"Message too long: {len(content)} > {self.config.max_message_length}")
        
        # Basic content filtering (you can enhance this)
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # JavaScript URLs
            r'data:text/html',            # Data URLs
            r'vbscript:',                 # VBScript
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.logger.warning(f"Suspicious content detected from user {user_id}: {pattern}")
                # You could raise an exception here or sanitize the content
        
        return content
    
    def check_cost_limits(self, user_id: str, tokens_used: int = 0, tool_calls: int = 0) -> None:
        """Check cost limits for a user"""
        if not self.config.cost_controls_enabled:
            return
        
        if tokens_used > self.config.max_tokens_per_request:
            raise CostLimitExceeded(f"Token limit exceeded: {tokens_used} > {self.config.max_tokens_per_request}")
        
        # You can add more sophisticated cost tracking here
        self.stats['total_requests'] += 1
    
    def validate_response(self, response: str) -> str:
        """Validate response content"""
        # Basic response validation
        if len(response) > 5000:  # Max response length
            return response[:5000] + "... [truncated]"
        return response
    
    def validate_communication_compliance(self, content: str, user_query: str) -> Dict[str, Any]:
        """Validate communication compliance"""
        return {
            'is_compliant': True,
            'confidence_score': 0.95,
            'issues': []
        }
    
    def record_response_time(self, response_time: float) -> None:
        """Record response time"""
        self.stats['response_times'].append(response_time)
        if len(self.stats['response_times']) > 1000:
            self.stats['response_times'] = self.stats['response_times'][-1000:]
    
    def record_error(self, user_id: str, error: Exception) -> None:
        """Record error"""
        self.stats['errors'].append({
            'user_id': user_id,
            'error': str(error),
            'timestamp': time.time()
        })
        if len(self.stats['errors']) > 1000:
            self.stats['errors'] = self.stats['errors'][-1000:]
    
    def get_fallback_response(self, error_type: str) -> str:
        """Get fallback response for errors"""
        if not self.config.graceful_degradation:
            return "I encountered an error and cannot process your request."
        
        fallback_responses = {
            'rate_limit': "I'm currently experiencing high traffic. Please try again in a few minutes.",
            'content_safety': "I can't process that request. Please rephrase your message.",
            'cost_limit': "I'm currently at capacity. Please try again later.",
            'general_error': "I apologize, but I'm having technical difficulties. Please try again.",
            'ratelimitexceeded': "I'm currently experiencing high traffic. Please try again in a few minutes.",
            'contentsafetyviolation': "I can't process that request. Please rephrase your message.",
            'costlimitexceeded': "I'm currently at capacity. Please try again later."
        }
        return fallback_responses.get(error_type, fallback_responses['general_error'])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get guard rails statistics"""
        return {
            'total_requests': self.stats['total_requests'],
            'blocked_requests': self.stats['blocked_requests'],
            'average_response_time': sum(self.stats['response_times']) / len(self.stats['response_times']) if self.stats['response_times'] else 0,
            'error_count': len(self.stats['errors'])
        }


# Global guard rails instance
_guard_rails_instance = None


def get_guard_rails(runtime_config: Optional[Dict[str, Any]] = None) -> GuardRails:
    """Get the global guard rails instance with optional runtime configuration"""
    global _guard_rails_instance
    if _guard_rails_instance is None or runtime_config is not None:
        if runtime_config:
            config = GuardRailsConfig.from_runtime_config(runtime_config)
        else:
            config = GuardRailsConfig()
        _guard_rails_instance = GuardRails(config)
    return _guard_rails_instance 