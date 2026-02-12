"""
Input Validation & Sanitization Service
Protects against malicious input and ensures data quality
"""

import re
from typing import Tuple, Optional
from services.logger import setup_logger
from services.config import config

logger = setup_logger('input_validator', 'input_validator.log')


class InputValidator:
    """
    Validates and sanitizes user input to prevent security issues.
    
    Features:
    - Length validation
    - Suspicious pattern detection (XSS, SQL injection, etc.)
    - Input sanitization
    - Content filtering
    """
    
    # Suspicious patterns that might indicate attacks
    SUSPICIOUS_PATTERNS = [
        r'<script[\s\S]*?>[\s\S]*?</script>',  # Script tags
        r'javascript:',                         # JavaScript protocol
        r'on\w+\s*=',                          # Event handlers (onclick, onerror, etc.)
        r'(union|select|insert|update|delete|drop)\s+',  # SQL keywords
        r'\.\./',                               # Path traversal
        r'eval\s*\(',                          # Code injection
        r'<iframe',                            # Iframe injection
        r'data:text/html',                     # Data URI XSS
        r'vbscript:',                          # VBScript protocol
        r'expression\s*\(',                    # CSS expression
    ]
    
    # Compile patterns for performance
    COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS]
    
    def __init__(
        self,
        max_length: int = None,
        min_length: int = None,
        allow_special_chars: bool = True
    ):
        """
        Initialize validator.
        
        Args:
            max_length: Maximum input length (uses config default if None)
            min_length: Minimum input length (uses config default if None)
            allow_special_chars: Whether to allow special characters
        """
        self.max_length = max_length or config.app.MAX_INPUT_LENGTH
        self.min_length = min_length or config.app.MIN_INPUT_LENGTH
        self.allow_special_chars = allow_special_chars
    
    def validate(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate input text.
        
        Args:
            text: User input to validate
        
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid
        
        Example:
            >>> validator = InputValidator()
            >>> is_valid, error = validator.validate("Hello world")
            >>> if not is_valid:
            >>>     print(f"Error: {error}")
        """
        
        # Check if empty
        if not text or not text.strip():
            logger.warning("Validation failed: Empty input")
            return False, "Please enter a question."
        
        # Check minimum length
        if len(text.strip()) < self.min_length:
            logger.warning(f"Validation failed: Too short ({len(text)} < {self.min_length})")
            return False, f"Query too short (minimum {self.min_length} characters)."
        
        # Check maximum length
        if len(text) > self.max_length:
            logger.warning(f"Validation failed: Too long ({len(text)} > {self.max_length})")
            return False, f"Query too long (maximum {self.max_length} characters)."
        
        # Check for suspicious patterns
        text_lower = text.lower()
        for i, pattern in enumerate(self.COMPILED_PATTERNS):
            if pattern.search(text_lower):
                logger.error(f"Suspicious input detected (pattern {i}): {text[:100]}...")
                return False, "Invalid input detected. Please rephrase your question."
        
        # Check for excessive special characters (spam indicator)
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if special_char_ratio > 0.5:  # More than 50% special chars
            logger.warning(f"High special char ratio: {special_char_ratio:.2%}")
            return False, "Too many special characters. Please use normal text."
        
        # Check for excessive repetition (spam indicator)
        if self._has_excessive_repetition(text):
            logger.warning(f"Excessive repetition detected: {text[:50]}...")
            return False, "Please avoid excessive repetition."
        
        logger.debug(f"Validation passed for input: {text[:50]}...")
        return True, None
    
    def sanitize(self, text: str) -> str:
        """
        Clean and sanitize user input.
        
        This is applied BEFORE validation and removes obviously problematic content.
        
        Args:
            text: Raw user input
        
        Returns:
            Sanitized text
        
        Example:
            >>> validator = InputValidator()
            >>> clean = validator.sanitize("  Hello   world!  ")
            >>> print(clean)  # "Hello world!"
        """
        if not text:
            return ""
        
        # Remove control characters (except newlines, tabs)
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Normalize whitespace (collapse multiple spaces)
        text = ' '.join(text.split())
        
        # Limit length (hard cutoff for safety)
        if len(text) > self.max_length:
            text = text[:self.max_length]
            logger.warning(f"Input truncated to {self.max_length} chars")
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        logger.debug(f"Sanitized input: {len(text)} chars")
        return text
    
    def validate_and_sanitize(self, text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Convenience method that both sanitizes and validates.
        
        Args:
            text: Raw user input
        
        Returns:
            Tuple of (is_valid, sanitized_text, error_message)
        
        Example:
            >>> validator = InputValidator()
            >>> is_valid, clean_text, error = validator.validate_and_sanitize("  Hello!  ")
            >>> if is_valid:
            >>>     process(clean_text)
            >>> else:
            >>>     print(f"Error: {error}")
        """
        # First sanitize
        sanitized = self.sanitize(text)
        
        # Then validate
        is_valid, error = self.validate(sanitized)
        
        return is_valid, sanitized, error
    
    def _has_excessive_repetition(self, text: str) -> bool:
        """
        Check if text has excessive character or word repetition.
        
        Args:
            text: Text to check
        
        Returns:
            True if excessive repetition detected
        """
        # Check for repeated characters (e.g., "aaaaaaa")
        if re.search(r'(.)\1{7,}', text):  # Same char 8+ times
            return True
        
        # Check for repeated words (e.g., "hello hello hello hello")
        words = text.lower().split()
        if len(words) >= 4:
            # Count consecutive identical words
            max_consecutive = 1
            current_consecutive = 1
            
            for i in range(1, len(words)):
                if words[i] == words[i-1]:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 1
            
            if max_consecutive >= 4:  # Same word 4+ times in a row
                return True
        
        return False


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

# Global validator instance
_default_validator = InputValidator()


def validate_input(text: str) -> Tuple[bool, Optional[str]]:
    """Convenience function for quick validation"""
    return _default_validator.validate(text)


def sanitize_input(text: str) -> str:
    """Convenience function for quick sanitization"""
    return _default_validator.sanitize(text)


def validate_and_sanitize(text: str) -> Tuple[bool, str, Optional[str]]:
    """Convenience function for validation + sanitization"""
    return _default_validator.validate_and_sanitize(text)