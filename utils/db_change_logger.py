"""
Database Change Logger for Knowledge Base Operations
Logs all database modifications to the console with timestamps and details
"""

import datetime
from typing import Optional, Dict, Any

class DatabaseChangeLogger:
    """Centralized logging for all database changes"""
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get formatted timestamp for logging"""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def _format_log_message(operation: str, entity_type: str, entity_id: Optional[str], details: Dict[str, Any]) -> str:
        """Format a consistent log message"""
        timestamp = DatabaseChangeLogger._get_timestamp()
        entity_info = f" ID:{entity_id}" if entity_id else ""
        details_str = ", ".join([f"{k}={v}" for k, v in details.items() if v is not None])
        details_part = f" ({details_str})" if details_str else ""
        
        return f"[{timestamp}] 📊 DB_CHANGE: {operation} {entity_type.upper()}{entity_info}{details_part}"
    
    @staticmethod
    def log_knowledge_base_insert(kb_id: str, name: str, description: Optional[str] = None):
        """Log knowledge base creation"""
        details = {"name": name}
        if description:
            details["description"] = description[:50] + "..." if len(description) > 50 else description
        
        message = DatabaseChangeLogger._format_log_message("CREATE", "Knowledge Base", kb_id, details)
        print(message)
    
    @staticmethod
    def log_knowledge_base_update(kb_id: str, name: Optional[str] = None, description: Optional[str] = None):
        """Log knowledge base update"""
        details = {}
        if name:
            details["name"] = name
        if description:
            details["description"] = description[:50] + "..." if len(description) > 50 else description
        
        message = DatabaseChangeLogger._format_log_message("UPDATE", "Knowledge Base", kb_id, details)
        print(message)
    
    @staticmethod
    def log_article_insert(article_id: str, title: str, kb_id: str, parent_id: Optional[str] = None):
        """Log article creation"""
        details = {"title": title, "kb_id": kb_id}
        if parent_id:
            details["parent_id"] = parent_id
        
        message = DatabaseChangeLogger._format_log_message("CREATE", "Article", article_id, details)
        print(message)
    
    @staticmethod
    def log_article_update(article_id: str, title: Optional[str] = None, content: Optional[str] = None, parent_id: Optional[str] = None):
        """Log article update"""
        details = {}
        if title:
            details["title"] = title
        if content:
            details["content_length"] = len(content)
        if parent_id:
            details["parent_id"] = parent_id
        
        message = DatabaseChangeLogger._format_log_message("UPDATE", "Article", article_id, details)
        print(message)
    
    @staticmethod
    def log_tag_insert(tag_id: str, name: str, description: Optional[str] = None):
        """Log tag creation"""
        details = {"name": name}
        if description:
            details["description"] = description[:30] + "..." if len(description) > 30 else description
        
        message = DatabaseChangeLogger._format_log_message("CREATE", "Tag", tag_id, details)
        print(message)
    
    @staticmethod
    def log_tag_update(tag_id: str, name: Optional[str] = None, description: Optional[str] = None):
        """Log tag update"""
        details = {}
        if name:
            details["name"] = name
        if description:
            details["description"] = description[:30] + "..." if len(description) > 30 else description
        
        message = DatabaseChangeLogger._format_log_message("UPDATE", "Tag", tag_id, details)
        print(message)
    
    @staticmethod
    def log_tag_delete(tag_id: str, name: Optional[str] = None):
        """Log tag deletion"""
        details = {"name": name} if name else {}
        message = DatabaseChangeLogger._format_log_message("DELETE", "Tag", tag_id, details)
        print(message)
    
    @staticmethod
    def log_tag_article_association(article_id: str, tag_id: str, operation: str = "ADD"):
        """Log tag-article association changes"""
        details = {"tag_id": tag_id, "article_id": article_id}
        message = DatabaseChangeLogger._format_log_message(f"{operation}_TAG_ASSOCIATION", "Article", article_id, details)
        print(message)
    
    @staticmethod
    def log_error(operation: str, entity_type: str, error_message: str, entity_id: Optional[str] = None):
        """Log database operation errors"""
        timestamp = DatabaseChangeLogger._get_timestamp()
        entity_info = f" ID:{entity_id}" if entity_id else ""
        message = f"[{timestamp}] ❌ DB_ERROR: {operation} {entity_type.upper()}{entity_info} - {error_message}"
        print(message)
