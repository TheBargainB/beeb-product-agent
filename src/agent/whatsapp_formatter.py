"""WhatsApp response formatter - converts markdown to WhatsApp-friendly formatting."""

import re
from typing import Dict, Any, Optional


class WhatsAppFormatter:
    """Formatter to convert markdown responses to WhatsApp-compatible format."""
    
    def __init__(self):
        self.format_rules = {
            # WhatsApp formatting rules
            'bold': {'markdown': r'\*\*(.*?)\*\*', 'whatsapp': r'*\1*'},
            'italic': {'markdown': r'\*(.*?)\*', 'whatsapp': r'_\1_'},
            'strikethrough': {'markdown': r'~~(.*?)~~', 'whatsapp': r'~\1~'},
            'code': {'markdown': r'`([^`]+)`', 'whatsapp': r'```\1```'},
            'code_block': {'markdown': r'```[\w]*\n(.*?)```', 'whatsapp': r'```\1```'},
            
            # Headers - convert to bold text with emojis
            'h1': {'markdown': r'^# (.*?)$', 'whatsapp': r'🔥 *\1*'},
            'h2': {'markdown': r'^## (.*?)$', 'whatsapp': r'📌 *\1*'},
            'h3': {'markdown': r'^### (.*?)$', 'whatsapp': r'• *\1*'},
            'h4': {'markdown': r'^#### (.*?)$', 'whatsapp': r'  ▪ *\1*'},
            
            # Lists - convert to simple bullet points
            'unordered_list': {'markdown': r'^[\s]*[-\*\+] (.*?)$', 'whatsapp': r'• \1'},
            'ordered_list': {'markdown': r'^[\s]*\d+\. (.*?)$', 'whatsapp': r'• \1'},
            
            # Links - show as plain text with URL
            'link': {'markdown': r'\[([^\]]*)\]\(([^\)]*)\)', 'whatsapp': r'\1: \2'},
            
            # Remove extra formatting
            'blockquote': {'markdown': r'^> (.*?)$', 'whatsapp': r'💭 \1'},
        }
    
    def format_for_whatsapp(self, text: str, source: str = "general") -> str:
        """
        Convert markdown text to WhatsApp-friendly format.
        
        Args:
            text: The markdown text to convert
            source: Source context (e.g., "whatsapp", "general")
            
        Returns:
            WhatsApp-formatted text
        """
        if not text:
            return text
            
        # Only format for WhatsApp source
        if source.lower() != "whatsapp":
            return text
            
        formatted_text = text
        
        # Apply formatting rules in order
        for rule_name, rule in self.format_rules.items():
            if rule_name in ['h1', 'h2', 'h3', 'h4', 'unordered_list', 'ordered_list', 'blockquote']:
                # Apply line-by-line for headers and lists
                formatted_text = re.sub(
                    rule['markdown'], 
                    rule['whatsapp'], 
                    formatted_text, 
                    flags=re.MULTILINE
                )
            else:
                # Apply globally for inline formatting
                formatted_text = re.sub(
                    rule['markdown'], 
                    rule['whatsapp'], 
                    formatted_text, 
                    flags=re.DOTALL
                )
        
        # Clean up extra whitespace and empty lines
        formatted_text = self._clean_whitespace(formatted_text)
        
        # Apply WhatsApp-specific improvements
        formatted_text = self._enhance_for_whatsapp(formatted_text)
        
        return formatted_text
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean up excessive whitespace."""
        # Remove more than 2 consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove trailing whitespace from lines
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def _enhance_for_whatsapp(self, text: str) -> str:
        """Apply WhatsApp-specific enhancements."""
        # Add spacing around sections
        text = re.sub(r'([🔥📌•])([^\n])', r'\1 \2', text)
        
        # Ensure proper spacing after bullet points
        text = re.sub(r'• ([^\n])', r'• \1', text)
        
        # Add emojis to common sections
        text = re.sub(r'\*\*INGREDIENTS\*\*:', '*🥘 INGREDIENTS*:', text, flags=re.IGNORECASE)
        text = re.sub(r'\*\*INSTRUCTIONS\*\*:', '*👨‍🍳 INSTRUCTIONS*:', text, flags=re.IGNORECASE)
        text = re.sub(r'\*\*RECIPE\*\*:', '*🍽️ RECIPE*:', text, flags=re.IGNORECASE)
        text = re.sub(r'\*\*TIPS\*\*:', '*💡 TIPS*:', text, flags=re.IGNORECASE)
        text = re.sub(r'\*\*NOTES\*\*:', '*📝 NOTES*:', text, flags=re.IGNORECASE)
        
        return text
    
    def format_recipe(self, recipe_text: str, source: str = "whatsapp") -> str:
        """Special formatting for recipe content."""
        if source.lower() != "whatsapp":
            return recipe_text
            
        formatted = self.format_for_whatsapp(recipe_text, source)
        
        # Additional recipe-specific formatting
        formatted = re.sub(r'Cook Time:', '⏱️ Cook Time:', formatted)
        formatted = re.sub(r'Prep Time:', '⏰ Prep Time:', formatted)
        formatted = re.sub(r'Servings:', '🍽️ Servings:', formatted)
        formatted = re.sub(r'Difficulty:', '📊 Difficulty:', formatted)
        
        return formatted
    
    def format_grocery_list(self, list_text: str, source: str = "whatsapp") -> str:
        """Special formatting for grocery list content."""
        if source.lower() != "whatsapp":
            return list_text
            
        formatted = self.format_for_whatsapp(list_text, source)
        
        # Additional grocery list formatting
        formatted = re.sub(r'Total Cost:', '💰 Total Cost:', formatted)
        formatted = re.sub(r'Items:', '🛒 Items:', formatted)
        formatted = re.sub(r'Store:', '🏪 Store:', formatted)
        
        return formatted
    
    def format_meal_plan(self, plan_text: str, source: str = "whatsapp") -> str:
        """Special formatting for meal plan content."""
        if source.lower() != "whatsapp":
            return plan_text
            
        formatted = self.format_for_whatsapp(plan_text, source)
        
        # Additional meal plan formatting
        formatted = re.sub(r'Breakfast:', '🌅 Breakfast:', formatted)
        formatted = re.sub(r'Lunch:', '🌞 Lunch:', formatted)
        formatted = re.sub(r'Dinner:', '🌙 Dinner:', formatted)
        formatted = re.sub(r'Snack:', '🍿 Snack:', formatted)
        
        return formatted
    
    def detect_content_type(self, text: str) -> str:
        """Detect the type of content to apply appropriate formatting."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['recipe', 'ingredients', 'instructions', 'cook', 'bake']):
            return 'recipe'
        elif any(word in text_lower for word in ['grocery', 'shopping', 'store', 'items']):
            return 'grocery_list'
        elif any(word in text_lower for word in ['meal plan', 'breakfast', 'lunch', 'dinner', 'menu']):
            return 'meal_plan'
        else:
            return 'general'
    
    def auto_format(self, text: str, source: str = "whatsapp") -> str:
        """Automatically detect content type and apply appropriate formatting."""
        if source.lower() != "whatsapp":
            return text
            
        content_type = self.detect_content_type(text)
        
        if content_type == 'recipe':
            return self.format_recipe(text, source)
        elif content_type == 'grocery_list':
            return self.format_grocery_list(text, source)
        elif content_type == 'meal_plan':
            return self.format_meal_plan(text, source)
        else:
            return self.format_for_whatsapp(text, source)


# Global formatter instance
whatsapp_formatter = WhatsAppFormatter()


def format_response_for_whatsapp(response: str, source: str = "whatsapp") -> str:
    """
    Convenience function to format any response for WhatsApp.
    
    Args:
        response: The response text to format
        source: Source context (e.g., "whatsapp", "general")
        
    Returns:
        WhatsApp-formatted response
    """
    return whatsapp_formatter.auto_format(response, source)


def format_response_for_platform(response: str, platform: str = "general") -> str:
    """
    Format response for different platforms.
    
    Args:
        response: The response text to format
        platform: Target platform ("whatsapp", "telegram", "web", "general")
        
    Returns:
        Platform-formatted response
    """
    if platform.lower() == "whatsapp":
        return whatsapp_formatter.auto_format(response, "whatsapp")
    elif platform.lower() == "telegram":
        # Telegram supports markdown, so return as-is
        return response
    elif platform.lower() == "web":
        # Web supports full markdown
        return response
    else:
        # General format - light markdown cleanup
        return response 