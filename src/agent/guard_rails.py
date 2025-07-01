"""Production guard rails for the agent to ensure safe and reliable operation."""

import re
import time
import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
import json

from .config import get_config


class GuardRailsError(Exception):
    """Exception raised when guard rails are violated."""
    pass


class RateLimitExceeded(GuardRailsError):
    """Exception raised when rate limits are exceeded."""
    pass


class ContentSafetyViolation(GuardRailsError):
    """Exception raised when content safety checks fail."""
    pass


class CostLimitExceeded(GuardRailsError):
    """Exception raised when cost limits are exceeded."""
    pass


class GuardRails:
    """Production guard rails implementation."""
    
    def __init__(self):
        """Initialize guard rails with configuration."""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting tracking
        self.request_counts = defaultdict(lambda: defaultdict(int))
        self.request_timestamps = defaultdict(list)
        self.cooldown_until = defaultdict(datetime)
        
        # Usage tracking
        self.token_usage = defaultdict(lambda: defaultdict(int))
        self.db_query_counts = defaultdict(int)
        self.tool_call_counts = defaultdict(int)
        
        # Error tracking
        self.error_counts = defaultdict(int)
        self.response_times = []
        self.circuit_breaker_state = defaultdict(bool)
        
        # Content safety patterns
        self.blocked_patterns = self._compile_blocked_patterns()
        
        # Spam detection
        self.message_hashes = defaultdict(list)
        
    def _compile_blocked_patterns(self) -> List[re.Pattern]:
        """Compile blocked content patterns."""
        patterns = []
        if self.config.config.get('guard_rails', {}).get('content_safety', {}).get('blocked_patterns'):
            for pattern in self.config.config['guard_rails']['content_safety']['blocked_patterns']:
                patterns.append(re.compile(pattern, re.IGNORECASE))
        return patterns
    
    def _get_user_key(self, user_id: str) -> str:
        """Get a consistent user key for tracking."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def _clean_old_timestamps(self, user_key: str, window_minutes: int):
        """Clean old timestamps outside the tracking window."""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        self.request_timestamps[user_key] = [
            ts for ts in self.request_timestamps[user_key] if ts > cutoff
        ]
    
    def check_rate_limits(self, user_id: str) -> bool:
        """Check if user has exceeded rate limits."""
        if not self.config.config.get('guard_rails', {}).get('rate_limiting', {}).get('enabled', False):
            return True
        
        user_key = self._get_user_key(user_id)
        now = datetime.now()
        
        # Check cooldown period
        if user_key in self.cooldown_until and now < self.cooldown_until[user_key]:
            raise RateLimitExceeded(f"User in cooldown until {self.cooldown_until[user_key]}")
        
        rate_config = self.config.config['guard_rails']['rate_limiting']
        
        # Clean old timestamps
        self._clean_old_timestamps(user_key, 60)  # Keep last hour
        
        # Check per-minute limit
        minute_ago = now - timedelta(minutes=1)
        recent_requests = [ts for ts in self.request_timestamps[user_key] if ts > minute_ago]
        
        if len(recent_requests) >= rate_config.get('requests_per_minute', 30):
            cooldown = timedelta(seconds=rate_config.get('cooldown_period_seconds', 60))
            self.cooldown_until[user_key] = now + cooldown
            raise RateLimitExceeded("Per-minute rate limit exceeded")
        
        # Check per-hour limit
        hour_ago = now - timedelta(hours=1)
        hour_requests = [ts for ts in self.request_timestamps[user_key] if ts > hour_ago]
        
        if len(hour_requests) >= rate_config.get('requests_per_hour', 200):
            raise RateLimitExceeded("Per-hour rate limit exceeded")
        
        # Check per-day limit
        day_ago = now - timedelta(days=1)
        day_requests = [ts for ts in self.request_timestamps[user_key] if ts > day_ago]
        
        if len(day_requests) >= rate_config.get('requests_per_day', 1000):
            raise RateLimitExceeded("Per-day rate limit exceeded")
        
        # Record this request
        self.request_timestamps[user_key].append(now)
        return True
    
    def validate_input_content(self, message: str, user_id: str) -> str:
        """Validate and sanitize input content."""
        if not self.config.config.get('guard_rails', {}).get('content_safety', {}).get('enabled', False):
            return message
        
        content_config = self.config.config['guard_rails']['content_safety']
        
        # Check message length
        min_length = content_config.get('min_message_length', 1)
        max_length = content_config.get('max_message_length', 500)
        
        if len(message) < min_length:
            raise ContentSafetyViolation(f"Message too short (minimum {min_length} characters)")
        
        if len(message) > max_length:
            raise ContentSafetyViolation(f"Message too long (maximum {max_length} characters)")
        
        # Check for blocked patterns
        if content_config.get('injection_protection', True):
            for pattern in self.blocked_patterns:
                if pattern.search(message):
                    raise ContentSafetyViolation("Message contains blocked content")
        
        # Spam detection
        if content_config.get('spam_detection', True):
            user_key = self._get_user_key(user_id)
            message_hash = hashlib.md5(message.lower().encode()).hexdigest()
            
            # Check for repeated messages
            recent_hashes = self.message_hashes[user_key]
            if recent_hashes.count(message_hash) >= 3:
                raise ContentSafetyViolation("Repeated message detected (spam)")
            
            # Add to history (keep last 10)
            recent_hashes.append(message_hash)
            if len(recent_hashes) > 10:
                recent_hashes.pop(0)
        
        # Input validation
        if self.config.config.get('guard_rails', {}).get('input_validation', {}).get('enabled', False):
            input_config = self.config.config['guard_rails']['input_validation']
            
            # Sanitize HTML if enabled
            if input_config.get('sanitize_html', True):
                # Simple HTML tag removal
                message = re.sub(r'<[^>]+>', '', message)
            
            # Normalize whitespace
            if input_config.get('normalize_whitespace', True):
                message = ' '.join(message.split())
        
        return message
    
    def check_cost_limits(self, user_id: str, tokens_used: int = 0, db_queries: int = 0, tool_calls: int = 0) -> bool:
        """Check if user has exceeded cost limits."""
        if not self.config.config.get('guard_rails', {}).get('cost_controls', {}).get('enabled', False):
            return True
        
        user_key = self._get_user_key(user_id)
        cost_config = self.config.config['guard_rails']['cost_controls']
        
        # Check per-request limits
        if tokens_used > cost_config.get('max_tokens_per_request', 4000):
            raise CostLimitExceeded("Per-request token limit exceeded")
        
        if db_queries > cost_config.get('max_database_queries_per_request', 10):
            raise CostLimitExceeded("Per-request database query limit exceeded")
        
        if tool_calls > cost_config.get('max_tool_calls_per_request', 5):
            raise CostLimitExceeded("Per-request tool call limit exceeded")
        
        # Check hourly token usage
        hour_key = datetime.now().strftime('%Y-%m-%d-%H')
        current_hour_tokens = self.token_usage[user_key][hour_key]
        
        if current_hour_tokens + tokens_used > cost_config.get('max_tokens_per_user_hour', 20000):
            raise CostLimitExceeded("Hourly token limit exceeded")
        
        # Update usage tracking
        self.token_usage[user_key][hour_key] += tokens_used
        self.db_query_counts[user_key] += db_queries
        self.tool_call_counts[user_key] += tool_calls
        
        return True
    
    def validate_response(self, response: str) -> str:
        """Validate and sanitize response content with comprehensive communication standards."""
        if not self.config.config.get('guard_rails', {}).get('response_validation', {}).get('enabled', False):
            return response
        
        response_config = self.config.config['guard_rails']['response_validation']
        
        # Check response length
        max_length = self.config.get_max_response_length()
        if response_config.get('check_response_length', True) and len(response) > max_length:
            response = response[:max_length] + "... [Response truncated for safety]"
        
        # Remove potentially sensitive information patterns
        if response_config.get('remove_sensitive_info', True):
            # Remove potential API keys, tokens, etc.
            response = re.sub(r'[a-zA-Z0-9]{32,}', '[REDACTED]', response)
            # Remove email addresses
            response = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', response)
            # Remove phone numbers
            response = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', response)
        
        # Apply communication standards if enabled
        if self.config.config.get('guard_rails', {}).get('communication_standards', {}).get('enabled', False):
            response = self._apply_communication_standards(response)
        
        return response
    
    def _apply_communication_standards(self, response: str) -> str:
        """Apply communication standards and content moderation."""
        comm_config = self.config.config['guard_rails']['communication_standards']
        
        # Check for prohibited content
        prohibited_content = comm_config.get('prohibited_content', [])
        
        # Check for specific problematic patterns
        financial_advice_patterns = ['invest', 'stock', 'financial planning', 'portfolio', 'investment']
        medical_advice_patterns = ['cure', 'treatment', 'medication', 'diagnose', 'supplement dosage']
        
        if any(pattern in response.lower() for pattern in financial_advice_patterns):
            self.logger.warning("Financial advice detected")
            response = self._apply_content_filter(response, "financial advice")
        elif any(pattern in response.lower() for pattern in medical_advice_patterns):
            self.logger.warning("Medical advice detected") 
            response = self._apply_content_filter(response, "medical advice")
        else:
            # Check standard prohibited content list
            for prohibited in prohibited_content:
                if prohibited.lower() in response.lower():
                    self.logger.warning(f"Prohibited content detected: {prohibited}")
                    response = self._apply_content_filter(response, prohibited)
                    break
        
        # Validate professional standards
        if comm_config.get('professional_standards', {}).get('maintain_grocery_focus', True):
            response = self._ensure_grocery_focus(response)
        
        # Add required disclaimers
        response = self._add_required_disclaimers(response, comm_config.get('disclaimers', {}))
        
        # Ensure brand voice compliance
        if comm_config.get('brand_voice', {}).get('maintain_friendly_tone', True):
            response = self._ensure_friendly_tone(response)
        
        return response
    
    def _apply_content_filter(self, response: str, prohibited_term: str) -> str:
        """Filter out prohibited content."""
        # Check for financial advice patterns
        if any(financial_term in response.lower() for financial_term in ['invest', 'stock', 'financial', 'portfolio']):
            return "For financial advice, please consult with a qualified financial advisor. I'm here to help with your grocery shopping and meal planning needs."
        
        # Check for medical advice patterns
        if any(medical_term in response.lower() for medical_term in ['cure', 'treatment', 'medication', 'diagnose', 'supplement']):
            return "For specific medical concerns, please consult with your healthcare provider. I can help you find nutritious food options instead."
        
        # Replace prohibited content with appropriate alternatives
        content_replacements = {
            "personal medical advice": "For specific medical concerns, please consult with your healthcare provider.",
            "medical advice": "For specific medical concerns, please consult with your healthcare provider. I can help you find nutritious food options instead.",
            "investment recommendations": "For financial advice, please consult with a qualified financial advisor.",
            "financial advice": "For financial advice, please consult with a qualified financial advisor. I'm here to help with your grocery shopping and meal planning needs.",
            "political opinions": "I focus on helping with grocery shopping and meal planning.",
            "religious advice": "I'm here to help with your grocery and meal planning needs.",
            "competitor criticism": "I'm happy to help you find the best products across different stores.",
            "unverified health claims": "For health-related questions, please consult healthcare professionals.",
            "alcohol/tobacco promotion": "I focus on helping with grocery and food items.",
            "inappropriate language": "Let me help you with your grocery shopping needs.",
            "off-topic discussions": "I'm here to help with grocery shopping, meal planning, and product recommendations."
        }
        
        for term, replacement in content_replacements.items():
            if term.lower() in prohibited_term.lower():
                return replacement
        
        return "I'm here to help with your grocery shopping and meal planning needs. How can I assist you with finding products or planning meals?"
    
    def _ensure_grocery_focus(self, response: str) -> str:
        """Ensure response maintains focus on grocery/food topics."""
        grocery_keywords = ['product', 'store', 'price', 'grocery', 'food', 'meal', 'recipe', 'ingredient', 'shopping', 'budget', 'milk', 'bread', 'vegetables', 'fruit']
        off_topic_keywords = ['weather', 'politics', 'invest', 'stock', 'medication', 'government', 'religion']
        
        response_lower = response.lower()
        
        # Check if response contains off-topic content
        has_off_topic = any(keyword in response_lower for keyword in off_topic_keywords)
        
        # Check if response contains grocery-related keywords
        has_grocery_focus = any(keyword in response_lower for keyword in grocery_keywords)
        
        # If off-topic or lacks grocery focus, redirect
        if has_off_topic or (not has_grocery_focus and len(response) > 50):
            if has_off_topic:
                # Completely replace off-topic responses
                return "I'm here to help with your grocery shopping and meal planning needs. What products are you looking for today?"
            else:
                # Add grocery context to neutral responses
                response = f"Regarding your grocery needs: {response}"
        
        return response
    
    def _add_required_disclaimers(self, response: str, disclaimers: Dict[str, str]) -> str:
        """Add required disclaimers based on response content."""
        response_lower = response.lower()
        
        # Add price disclaimer if prices are mentioned
        if any(price_indicator in response_lower for price_indicator in ['€', '$', 'price', 'cost', 'expensive', 'cheap']):
            if disclaimers.get('price_accuracy'):
                response += f"\n\n*{disclaimers['price_accuracy']}*"
        
        # Add dietary disclaimer if dietary advice is given
        if any(diet_term in response_lower for diet_term in ['healthy', 'diet', 'nutrition', 'vitamin', 'calories', 'organic']):
            if disclaimers.get('dietary_advice'):
                response += f"\n\n*{disclaimers['dietary_advice']}*"
        
        # Add availability disclaimer if specific products are mentioned
        if any(product_term in response_lower for product_term in ['available', 'stock', 'find', 'product']):
            if disclaimers.get('availability'):
                response += f"\n\n*{disclaimers['availability']}*"
        
        return response
    
    def _ensure_friendly_tone(self, response: str) -> str:
        """Ensure response maintains a friendly, helpful tone."""
        friendly_indicators = ['happy', 'glad', 'help', 'great', '!', '😊', 'pleased', 'delighted', 'wonderful']
        dry_indicators = ['the following', 'as requested', 'here are', 'available at']
        
        response_lower = response.lower()
        
        # Check if response is long enough and seems dry
        is_substantial_response = len(response) > 40  # Lowered threshold
        has_friendly_tone = any(friendly in response_lower for friendly in friendly_indicators)
        seems_dry = any(dry in response_lower for dry in dry_indicators)
        
        if is_substantial_response and not has_friendly_tone and seems_dry:
            # Add friendly greeting if it's a product recommendation
            if any(word in response_lower for word in ['product', 'find', 'available', 'store']):
                # Add friendly intro
                response = f"I'd be happy to help! {response}"
                
            # Add friendly ending
            if response.endswith('.'):
                response = response[:-1] + "! 😊"
            elif not response.endswith(('!', '?')):
                response += " 😊"
        
        return response
    
    def validate_communication_compliance(self, response: str, user_query: str) -> Dict[str, Any]:
        """Comprehensive communication compliance check."""
        if not self.config.config.get('guard_rails', {}).get('communication_standards', {}).get('enabled', False):
            return {"compliant": True, "issues": []}
        
        comm_config = self.config.config['guard_rails']['communication_standards']
        issues = []
        
        # Check brand voice compliance
        brand_voice = comm_config.get('brand_voice', {})
        if brand_voice.get('be_concise_and_clear', True) and len(response) > 3000:
            issues.append("Response too lengthy, lacks conciseness")
        
        # Check content guidelines
        content_guidelines = comm_config.get('content_guidelines', {})
        
        # Check for medical advice
        if content_guidelines.get('no_medical_advice', True):
            medical_terms = ['diagnose', 'cure', 'treatment', 'medication', 'supplement dosage']
            if any(term in response.lower() for term in medical_terms):
                issues.append("Response may contain medical advice")
        
        # Check for financial advice
        if content_guidelines.get('no_financial_advice', True):
            financial_terms = ['invest', 'stock', 'portfolio', 'financial planning']
            if any(term in response.lower() for term in financial_terms):
                issues.append("Response may contain financial advice")
        
        # Check factual accuracy for prices
        if content_guidelines.get('cite_sources_for_prices', True):
            if any(price_term in response.lower() for price_term in ['€', '$', 'price', 'cost']):
                if not any(store in response.lower() for store in ['albert heijn', 'jumbo', 'dirk', 'ah']):
                    issues.append("Price mentioned without citing store source")
        
        # Check quality controls
        quality_controls = comm_config.get('quality_controls', {})
        
        # Check relevance (more sophisticated check)
        if quality_controls.get('check_response_relevance', True):
            # Use semantic relevance - check if response contains grocery/food related terms
            grocery_terms = ['product', 'store', 'price', 'grocery', 'food', 'meal', 'milk', 'bread', 'albert', 'jumbo', 'dirk']
            query_keywords = set(user_query.lower().split())
            response_keywords = set(response.lower().split())
            
            # Check both direct keyword overlap and grocery context
            keyword_overlap = len(query_keywords.intersection(response_keywords)) / max(len(query_keywords), 1)
            has_grocery_context = any(term in response.lower() for term in grocery_terms)
            
            # Consider relevant if either good keyword overlap OR grocery context exists
            if keyword_overlap < 0.2 and not has_grocery_context:
                issues.append("Response may not be relevant to user query")
        
        # Check for actionable advice
        if quality_controls.get('require_actionable_advice', True):
            actionable_indicators = ['can', 'should', 'try', 'recommend', 'suggest', 'find', 'search', 'look for']
            if not any(indicator in response.lower() for indicator in actionable_indicators):
                issues.append("Response lacks actionable advice")
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "confidence_score": max(0, 1 - (len(issues) * 0.2))  # Reduce score for each issue
        }
    
    def record_error(self, user_id: str, error: Exception):
        """Record an error for monitoring."""
        user_key = self._get_user_key(user_id)
        self.error_counts[user_key] += 1
        
        # Log error (anonymized)
        self.logger.error(f"Error for user {user_key}: {type(error).__name__}")
        
        # Check error rate thresholds
        monitoring_config = self.config.config.get('guard_rails', {}).get('monitoring', {})
        if monitoring_config.get('enabled', False):
            error_threshold = monitoring_config.get('alert_thresholds', {}).get('error_rate_percent', 5.0)
            
            # Simplified error rate check (would need more sophisticated tracking in production)
            if self.error_counts[user_key] > 10:  # Alert after 10 errors
                self.logger.warning(f"High error rate detected for user {user_key}")
    
    def record_response_time(self, response_time_ms: float):
        """Record response time for monitoring."""
        self.response_times.append(response_time_ms)
        
        # Keep only recent measurements
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-500:]
        
        # Check response time thresholds
        monitoring_config = self.config.config.get('guard_rails', {}).get('monitoring', {})
        if monitoring_config.get('enabled', False):
            threshold = monitoring_config.get('alert_thresholds', {}).get('avg_response_time_ms', 10000)
            
            if response_time_ms > threshold:
                self.logger.warning(f"Slow response detected: {response_time_ms}ms")
    
    def should_use_circuit_breaker(self, service_name: str) -> bool:
        """Check if circuit breaker should prevent service calls."""
        if not self.config.config.get('guard_rails', {}).get('error_handling', {}).get('circuit_breaker', False):
            return False
        
        return self.circuit_breaker_state.get(service_name, False)
    
    def get_fallback_response(self, error_type: str) -> str:
        """Get a fallback response for errors."""
        if not self.config.config.get('guard_rails', {}).get('error_handling', {}).get('fallback_responses', False):
            raise
        
        fallback_responses = {
            'rate_limit': "I'm currently experiencing high demand. Please try again in a few minutes.",
            'content_safety': "I can't process that request. Please rephrase your message.",
            'cost_limit': "I've reached my usage limit for now. Please try again later.",
            'database_error': "I'm having trouble accessing product information right now. Please try again shortly.",
            'general_error': "I encountered an issue. Please try rephrasing your request or try again later."
        }
        
        return fallback_responses.get(error_type, fallback_responses['general_error'])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current guard rails statistics."""
        return {
            'total_users_tracked': len(self.request_counts),
            'total_requests': sum(sum(counts.values()) for counts in self.request_counts.values()),
            'total_errors': sum(self.error_counts.values()),
            'avg_response_time_ms': sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            'circuit_breakers_active': sum(self.circuit_breaker_state.values())
        }


# Global guard rails instance
_guard_rails = None


def get_guard_rails() -> GuardRails:
    """Get the global guard rails instance."""
    global _guard_rails
    if _guard_rails is None:
        _guard_rails = GuardRails()
    return _guard_rails


def guard_rails_decorator(func):
    """Decorator to apply guard rails to functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        guard_rails = get_guard_rails()
        start_time = time.time()
        
        try:
            # Extract user_id from kwargs or config
            user_id = kwargs.get('user_id') or 'anonymous'
            
            # Apply pre-execution checks
            guard_rails.check_rate_limits(user_id)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Record successful execution
            response_time = (time.time() - start_time) * 1000
            guard_rails.record_response_time(response_time)
            
            return result
            
        except (RateLimitExceeded, ContentSafetyViolation, CostLimitExceeded) as e:
            guard_rails.record_error(user_id, e)
            raise
        except Exception as e:
            guard_rails.record_error(user_id, e)
            
            # Check if we should use fallback response
            if guard_rails.config.config.get('guard_rails', {}).get('error_handling', {}).get('graceful_degradation', False):
                return guard_rails.get_fallback_response('general_error')
            
            raise
    
    return wrapper 