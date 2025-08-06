"""Test the database change logging system"""

import sys
sys.path.append('.')

from utils.db_change_logger import DatabaseChangeLogger

# Test all logging methods
print("Testing Database Change Logger:")
print("=" * 60)

# Test KB logging
DatabaseChangeLogger.log_knowledge_base_insert("1", "Personal Finance Guide", "A comprehensive financial guide")
DatabaseChangeLogger.log_knowledge_base_update("1", "Updated Finance Guide", "An updated comprehensive guide")

# Test Article logging  
DatabaseChangeLogger.log_article_insert("15", "Budgeting Basics", "1", None)
DatabaseChangeLogger.log_article_update("15", "Advanced Budgeting", "This is updated content for budgeting", "1")

# Test Tag logging
DatabaseChangeLogger.log_tag_insert("5", "budgeting", "Articles about budgeting")
DatabaseChangeLogger.log_tag_update("5", "budget-management", "Updated description")
DatabaseChangeLogger.log_tag_delete("5", "budget-management")

# Test Tag-Article associations
DatabaseChangeLogger.log_tag_article_association("15", "5", "ADD")
DatabaseChangeLogger.log_tag_article_association("15", "5", "REMOVE")

# Test Error logging
DatabaseChangeLogger.log_error("CREATE", "Article", "Connection timeout", "15")

print("=" * 60)
print("✅ Database logging test completed!")
