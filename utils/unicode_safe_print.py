"""
Unicode-safe printing utilities for Windows console compatibility
"""
import sys

def safe_print(message: str) -> None:
    """
    Print message with Unicode emoji replacement for Windows console compatibility
    """
    # Define emoji to ASCII replacements for Windows console
    replacements = {
        '🚀': '[START]',
        '✅': '[OK]',
        '❌': '[FAIL]',
        '🔧': '[TOOL]',
        '📝': '[PARAMS]',
        '📊': '[STATS]',
        '🔍': '[SEARCH]',
        '📚': '[KB]',
        '📋': '[LIST]',
        '🎯': '[TARGET]',
        '🤖': '[AGENT]',
        '🏷️': '[TAG]',
        '🦊': '[GITLAB]',
        '⚠️': '[WARN]',
        '💬': '[CHAT]',
        '🌐': '[MULTI]',
        '🚪': '[GATE]',
        '⚡': '[AUTO]',
        '🔄': '[SYNC]',
        '📄': '[DOC]',
        '📁': '[FOLDER]',
        '🆔': '[ID]',
        '🔗': '[LINK]',
        '👁️': '[VIEW]',
        '🎯': '[AIM]',
        '🏗️': '[BUILD]',
        '🏁': '[MILESTONE]',
        '⏰': '[TIME]',
        '📅': '[DATE]'
    }
    
    # Replace Unicode emojis if on Windows
    if sys.platform.startswith('win'):
        safe_message = message
        for emoji, replacement in replacements.items():
            safe_message = safe_message.replace(emoji, replacement)
        print(safe_message)
    else:
        # On Unix systems, print normally (they handle Unicode better)
        print(message)

def safe_format(template: str, *args, **kwargs) -> str:
    """
    Format string and make it Unicode-safe for console output
    """
    formatted = template.format(*args, **kwargs)
    
    if sys.platform.startswith('win'):
        # Define emoji to ASCII replacements for Windows console
        replacements = {
            '🚀': '[START]',
            '✅': '[OK]',
            '❌': '[FAIL]',
            '🔧': '[TOOL]',
            '📝': '[PARAMS]',
            '📊': '[STATS]',
            '🔍': '[SEARCH]',
            '📚': '[KB]',
            '📋': '[LIST]',
            '🎯': '[TARGET]',
            '🤖': '[AGENT]',
            '🏷️': '[TAG]',
            '🦊': '[GITLAB]',
            '⚠️': '[WARN]',
            '💬': '[CHAT]',
            '🌐': '[MULTI]',
            '🚪': '[GATE]',
            '⚡': '[AUTO]',
            '🔄': '[SYNC]',
            '📄': '[DOC]',
            '📁': '[FOLDER]',
            '🆔': '[ID]',
            '🔗': '[LINK]',
            '👁️': '[VIEW]',
            '🎯': '[AIM]',
            '🏗️': '[BUILD]',
            '🏁': '[MILESTONE]',
            '⏰': '[TIME]',
            '📅': '[DATE]'
        }
        
        # Replace Unicode emojis with ASCII equivalents
        for emoji, replacement in replacements.items():
            formatted = formatted.replace(emoji, replacement)
    
    return formatted
