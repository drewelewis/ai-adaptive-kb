import os
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from models.article import Article
from models.knowledge_base import KnowledgeBase
from models.tags import Tags
from utils.db_change_logger import DatabaseChangeLogger

load_dotenv(override=True)

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', 5432)
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

class KnowledgeBaseOperations:
    def _get_connection(self):
        return psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
    def get_knowledge_bases(self) -> List[str]:
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # get all active knowledge bases
                    sql = """SELECT * FROM knowledge_base WHERE is_active = TRUE;"""
                    cur.execute(sql)
                    knowledge_bases = cur.fetchall()
                    # Return list of knowledge base names
                    return [kb['name'] for kb in knowledge_bases]
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_knowledge_bases: {e}")
            return []
    
    def get_knowledge_bases_with_ids(self) -> List[Dict[str, Any]]:
        """Get knowledge bases with their IDs and names"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # get all active knowledge bases
                    sql = """SELECT id, name, description FROM knowledge_base WHERE is_active = TRUE;"""
                    cur.execute(sql)
                    knowledge_bases = cur.fetchall()
                    # Return list of dicts with id and name
                    return [{"id": str(kb['id']), "name": kb['name'], "description": kb['description']} for kb in knowledge_bases]
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_knowledge_bases_with_ids: {e}")
            return []
    # update knowledge base by id
    def update_knowledge_base(self, knowledge_base: KnowledgeBase.UpdateModel) -> Optional[KnowledgeBase.BaseModel]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    sql = """UPDATE knowledge_base
                             SET name = %s, description = %s, author_id = %s, gitlab_project_id = %s
                             WHERE id = %s RETURNING id;"""
                    cur.execute(sql, (knowledge_base.name, knowledge_base.description, knowledge_base.author_id, knowledge_base.gitlab_project_id, knowledge_base.id))
                    id = cur.fetchone()[0]
                    conn.commit()
                    
                    # Log the database change
                    DatabaseChangeLogger.log_knowledge_base_update(
                        kb_id=str(knowledge_base.id), 
                        name=knowledge_base.name, 
                        description=knowledge_base.description
                    )
                    
                    # Fetch the complete updated record from database
                    updated_knowledge_base = self.get_knowledge_base_by_id(str(id))
                    return updated_knowledge_base
        except Exception as e:
            DatabaseChangeLogger.log_error("UPDATE", "Knowledge Base", str(e), str(knowledge_base.id))
            print(f"An error occurred with KnowledgeBaseOperations.update_knowledge_base: {e}")
            return None
        finally:
            if conn:
                conn.close()    
    
    def update_knowledge_base_gitlab_project_id(self, knowledge_base_id: int, gitlab_project_id: int) -> bool:
        """Update the GitLab project ID for an existing knowledge base"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    sql = """UPDATE knowledge_base
                             SET gitlab_project_id = %s, updated_at = CURRENT_TIMESTAMP
                             WHERE id = %s;"""
                    cur.execute(sql, (gitlab_project_id, knowledge_base_id))
                    conn.commit()
                    
                    # Log the database change
                    DatabaseChangeLogger.log_knowledge_base_update(
                        kb_id=str(knowledge_base_id), 
                        name=f"Updated GitLab project ID to {gitlab_project_id}", 
                        description="GitLab project ID linkage"
                    )
                    
                    return True
        except Exception as e:
            DatabaseChangeLogger.log_error("UPDATE", "Knowledge Base GitLab Project ID", str(e), str(knowledge_base_id))
            print(f"An error occurred with KnowledgeBaseOperations.update_knowledge_base_gitlab_project_id: {e}")
            return False
        finally:
            if conn:
                conn.close()
        
    def get_knowledge_base_by_id(self, knowledge_base_id: str) -> Optional[KnowledgeBase.BaseModel]:
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sql = "SELECT * FROM knowledge_base WHERE id = %s;"
                    cur.execute(sql, (knowledge_base_id,))
                    knowledge_base = cur.fetchone()
                    if knowledge_base:
                        return KnowledgeBase.BaseModel(**knowledge_base)
                    else:
                        return None
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_knowledge_base_by_id: {e}")
            return None
    
    def get_knowledge_base_by_gitlab_project_id(self, gitlab_project_id: int) -> Optional[KnowledgeBase.BaseModel]:
        """Get a knowledge base by its linked GitLab project ID."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sql = "SELECT * FROM knowledge_base WHERE gitlab_project_id = %s;"
                    cur.execute(sql, (gitlab_project_id,))
                    knowledge_base = cur.fetchone()
                    if knowledge_base:
                        return KnowledgeBase.BaseModel(**knowledge_base)
                    else:
                        return None
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_knowledge_base_by_gitlab_project_id: {e}")
            return None
    
    def get_article_by_id(self, knowledge_base_id: str, article_id: str) -> Optional[Article.BaseModel]:
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sql = "SELECT * FROM articles WHERE knowledge_base_id = %s and id= %s;"
                    cur.execute(sql, (knowledge_base_id,article_id,))
                    article = cur.fetchone()
                    if article:
                        return Article.BaseModel(**article)
                    else:
                        return None
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_article_by_id: {e}")
            return None   
        
    def insert_knowledge_base(self, knowledge_base: KnowledgeBase.InsertModel) -> int:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    sql = """INSERT INTO knowledge_base (name, description, author_id, gitlab_project_id)
                             VALUES (%s, %s, %s, %s) RETURNING id;"""
                    cur.execute(sql, (knowledge_base.name, knowledge_base.description, knowledge_base.author_id, knowledge_base.gitlab_project_id))
                    id = cur.fetchone()[0]
                    conn.commit()
                    
                    # Log the database change
                    DatabaseChangeLogger.log_knowledge_base_insert(
                        kb_id=str(id), 
                        name=knowledge_base.name, 
                        description=knowledge_base.description
                    )
 
                    return id
        except Exception as e:
            DatabaseChangeLogger.log_error("CREATE", "Knowledge Base", str(e))
            print(f"An error occurred with KnowledgeBaseOperations.insert_knowledge_base: {e}")
            return None

        # get article_hierarchy function is a recursive function that returns the hierarchy of articles in a knowledge base
    def get_article_hierarchy(self, knowledge_base_id: str) -> List[Article.HierarchyModel]:
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                sql = "SELECT * FROM get_article_hierarchy(%s);"
                print(f"Executing SQL: {sql} with knowledge_base_id: {knowledge_base_id}")
                cur.execute(sql, (knowledge_base_id,))
                articles = cur.fetchall()
                return articles
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_article_hierarchy: {e}")
            return []
        finally:
            if conn:
                conn.close()


    def get_root_level_articles(self, knowledge_base_id: str) -> list:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    sql = """SELECT * FROM articles 
                             WHERE parent_id IS NULL AND knowledge_base_id = %s AND is_active = TRUE;"""
                    cur.execute(sql, (knowledge_base_id,))
                    articles = cur.fetchall()
                    return articles
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_root_level_articles: {e}")
            return []

    def get_articles_by_parentids(self, knowledge_base_id: str, parent_ids: list[str]) -> list[str]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Dynamically build the correct number of placeholders
                    parent_ids = ', '.join(parent_ids)
                    sql = f"SELECT * FROM articles WHERE parent_id IN ({parent_ids}) AND  knowledge_base_id = {knowledge_base_id} AND is_active = TRUE;"
                    cur.execute(sql, (parent_ids,knowledge_base_id))

                    articles = cur.fetchall()
                    return articles
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_articles_by_parentids: {e}")
            return []
    
    def insert_article(self, knowledge_base_id: str, article: Article.InsertModel) -> Optional[Article.BaseModel]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    sql = """INSERT INTO articles (knowledge_base_id,title, content, author_id, parent_id)
                             VALUES (%s, %s, %s, %s, %s) RETURNING id;"""
                    cur.execute(sql, (knowledge_base_id, article.title, article.content, article.author_id, article.parent_id))
                    conn.commit()
                    new_article_id = cur.fetchone()
                    if new_article_id:
                        # Log the database change
                        DatabaseChangeLogger.log_article_insert(
                            article_id=str(new_article_id[0]),
                            title=article.title,
                            kb_id=knowledge_base_id,
                            parent_id=str(article.parent_id) if article.parent_id else None
                        )
                        
                        new_article = Article.BaseModel(
                            id=new_article_id[0],
                            knowledge_base_id=knowledge_base_id,
                            title=article.title,
                            content=article.content,
                            author_id=article.author_id,
                            parent_id=article.parent_id
                        )
                    if new_article:
                        return new_article
                    else:
                        return None
                
        except Exception as e:
            DatabaseChangeLogger.log_error("CREATE", "Article", str(e))
            print(f"An error occurred with KnowledgeBaseOperations.insert_article: {e}")
            return None
        finally:
            if conn:
                conn.close()  

    def update_article(self, knowledge_base_id: str, article: Article.UpdateModel) -> Article.BaseModel:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Update the article in the database
                    sql = """UPDATE articles
                             SET knowledge_base_id= %s, title = %s, content = %s, author_id = %s, parent_id = %s
                             WHERE id = %s RETURNING id;"""
                    
                    cur.execute(sql, (knowledge_base_id,article.title, article.content, article.author_id, article.parent_id, article.id))
                    article_id = cur.fetchone()[0]
                    conn.commit()

                    if article_id:
                        # Log the database change
                        DatabaseChangeLogger.log_article_update(
                            article_id=str(article.id),
                            title=article.title,
                            content=article.content,
                            parent_id=str(article.parent_id) if article.parent_id else None
                        )
                        
                        updated_article = Article.BaseModel(
                            id=article_id,
                            knowledge_base_id=knowledge_base_id,
                            title=article.title,
                            content=article.content,
                            author_id=article.author_id,
                            parent_id=article.parent_id
                        )
                    if updated_article:
                        return updated_article
                    else:
                        return None
                
        except Exception as e:
            DatabaseChangeLogger.log_error("UPDATE", "Article", str(e), str(article.id))
            print(f"An error occurred with KnowledgeBaseOperations.insert_article: {e}")
            return None  

    # =============================================
    # TAG OPERATIONS
    # =============================================
    
    def get_tags_by_knowledge_base(self, knowledge_base_id: str) -> List[Tags.BaseModel]:
        """Get all tags for a specific knowledge base"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sql = "SELECT * FROM tags WHERE knowledge_base_id = %s ORDER BY name;"
                    cur.execute(sql, (knowledge_base_id,))
                    tags = cur.fetchall()
                    return [Tags.BaseModel(**tag) for tag in tags]
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_tags_by_knowledge_base: {e}")
            return []

    def get_tag_by_id(self, tag_id: str) -> Optional[Tags.BaseModel]:
        """Get a specific tag by ID"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sql = "SELECT * FROM tags WHERE id = %s;"
                    cur.execute(sql, (tag_id,))
                    tag = cur.fetchone()
                    if tag:
                        return Tags.BaseModel(**tag)
                    else:
                        return None
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_tag_by_id: {e}")
            return None

    def get_tag_by_name(self, knowledge_base_id: str, tag_name: str) -> Optional[Tags.BaseModel]:
        """Get a tag by name within a knowledge base"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sql = "SELECT * FROM tags WHERE knowledge_base_id = %s AND name = %s;"
                    cur.execute(sql, (knowledge_base_id, tag_name.lower()))
                    tag = cur.fetchone()
                    if tag:
                        return Tags.BaseModel(**tag)
                    else:
                        return None
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_tag_by_name: {e}")
            return None

    def insert_tag(self, tag: Tags.InsertModel) -> Optional[Tags.BaseModel]:
        """Insert a new tag"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if tag already exists for this knowledge base
                    existing_tag = self.get_tag_by_name(str(tag.knowledge_base_id), tag.name)
                    if existing_tag:
                        print(f"Tag '{tag.name}' already exists in knowledge base {tag.knowledge_base_id}")
                        return existing_tag
                    
                    sql = """INSERT INTO tags (name, knowledge_base_id)
                             VALUES (%s, %s) RETURNING id;"""
                    cur.execute(sql, (tag.name, tag.knowledge_base_id))
                    tag_id = cur.fetchone()[0]
                    conn.commit()
                    
                    # Log the database change
                    DatabaseChangeLogger.log_tag_insert(
                        tag_id=str(tag_id),
                        name=tag.name
                    )
                    
                    new_tag = Tags.BaseModel(
                        id=tag_id,
                        name=tag.name,
                        knowledge_base_id=tag.knowledge_base_id
                    )
                    return new_tag
                    
        except Exception as e:
            DatabaseChangeLogger.log_error("CREATE", "Tag", str(e))
            print(f"An error occurred with KnowledgeBaseOperations.insert_tag: {e}")
            return None

    def update_tag(self, tag: Tags.UpdateModel) -> Optional[Tags.BaseModel]:
        """Update an existing tag"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if new name already exists for this knowledge base (excluding current tag)
                    sql_check = "SELECT id FROM tags WHERE knowledge_base_id = %s AND name = %s AND id != %s;"
                    cur.execute(sql_check, (tag.knowledge_base_id, tag.name, tag.id))
                    if cur.fetchone():
                        print(f"Tag name '{tag.name}' already exists in knowledge base {tag.knowledge_base_id}")
                        return None
                    
                    sql = """UPDATE tags
                             SET name = %s, knowledge_base_id = %s
                             WHERE id = %s RETURNING id;"""
                    cur.execute(sql, (tag.name, tag.knowledge_base_id, tag.id))
                    updated_id = cur.fetchone()
                    if updated_id:
                        conn.commit()
                        
                        # Log the database change
                        DatabaseChangeLogger.log_tag_update(
                            tag_id=str(tag.id),
                            name=tag.name
                        )
                        
                        updated_tag = Tags.BaseModel(
                            id=tag.id,
                            name=tag.name,
                            knowledge_base_id=tag.knowledge_base_id
                        )
                        return updated_tag
                    else:
                        return None
                        
        except Exception as e:
            DatabaseChangeLogger.log_error("UPDATE", "Tag", str(e), str(tag.id))
            print(f"An error occurred with KnowledgeBaseOperations.update_tag: {e}")
            return None

    def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag and all its article associations"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Get tag name before deletion for logging
                    tag_info = self.get_tag_by_id(tag_id)
                    tag_name = tag_info.name if tag_info else None
                    
                    # Delete tag (article_tags will be deleted automatically due to CASCADE)
                    sql = "DELETE FROM tags WHERE id = %s;"
                    cur.execute(sql, (tag_id,))
                    conn.commit()
                    
                    if cur.rowcount > 0:
                        # Log the database change
                        DatabaseChangeLogger.log_tag_delete(tag_id=tag_id, name=tag_name)
                        return True
                    return False
                    
        except Exception as e:
            DatabaseChangeLogger.log_error("DELETE", "Tag", str(e), tag_id)
            print(f"An error occurred with KnowledgeBaseOperations.delete_tag: {e}")
            return False

    # =============================================
    # ARTICLE-TAG RELATIONSHIP OPERATIONS
    # =============================================

    def get_tags_for_article(self, article_id: str) -> List[Tags.BaseModel]:
        """Get all tags associated with an article"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sql = """SELECT t.* FROM tags t
                             INNER JOIN article_tags at ON t.id = at.tag_id
                             WHERE at.article_id = %s
                             ORDER BY t.name;"""
                    cur.execute(sql, (article_id,))
                    tags = cur.fetchall()
                    return [Tags.BaseModel(**tag) for tag in tags]
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_tags_for_article: {e}")
            return []

    def get_articles_for_tag(self, tag_id: str) -> List[Article.BaseModel]:
        """Get all articles associated with a tag"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sql = """SELECT a.* FROM articles a
                             INNER JOIN article_tags at ON a.id = at.article_id
                             WHERE at.tag_id = %s AND a.is_active = TRUE
                             ORDER BY a.title;"""
                    cur.execute(sql, (tag_id,))
                    articles = cur.fetchall()
                    return [Article.BaseModel(**article) for article in articles]
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_articles_for_tag: {e}")
            return []

    def add_tag_to_article(self, article_id: str, tag_id: str) -> bool:
        """Add a tag to an article"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if relationship already exists
                    sql_check = "SELECT 1 FROM article_tags WHERE article_id = %s AND tag_id = %s;"
                    cur.execute(sql_check, (article_id, tag_id))
                    if cur.fetchone():
                        print(f"Tag {tag_id} is already associated with article {article_id}")
                        return True
                    
                    sql = "INSERT INTO article_tags (article_id, tag_id) VALUES (%s, %s);"
                    cur.execute(sql, (article_id, tag_id))
                    conn.commit()
                    
                    # Log the database change
                    DatabaseChangeLogger.log_tag_article_association(article_id, tag_id, "ADD")
                    return True
                    
        except Exception as e:
            DatabaseChangeLogger.log_error("ADD_TAG_ASSOCIATION", "Article", str(e), article_id)
            print(f"An error occurred with KnowledgeBaseOperations.add_tag_to_article: {e}")
            return False

    def remove_tag_from_article(self, article_id: str, tag_id: str) -> bool:
        """Remove a tag from an article"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    sql = "DELETE FROM article_tags WHERE article_id = %s AND tag_id = %s;"
                    cur.execute(sql, (article_id, tag_id))
                    conn.commit()
                    
                    if cur.rowcount > 0:
                        # Log the database change
                        DatabaseChangeLogger.log_tag_article_association(article_id, tag_id, "REMOVE")
                        return True
                    return False
                    
        except Exception as e:
            DatabaseChangeLogger.log_error("REMOVE_TAG_ASSOCIATION", "Article", str(e), article_id)
            print(f"An error occurred with KnowledgeBaseOperations.remove_tag_from_article: {e}")
            return False

    def set_article_tags(self, article_id: str, tag_ids: List[str]) -> bool:
        """Set all tags for an article (replaces existing tags)"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Remove all existing tags for this article
                    sql_delete = "DELETE FROM article_tags WHERE article_id = %s;"
                    cur.execute(sql_delete, (article_id,))
                    
                    # Add new tags
                    if tag_ids:
                        sql_insert = "INSERT INTO article_tags (article_id, tag_id) VALUES (%s, %s);"
                        for tag_id in tag_ids:
                            cur.execute(sql_insert, (article_id, tag_id))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.set_article_tags: {e}")
            return False

    def get_tags_with_usage_count(self, knowledge_base_id: str) -> List[Tags.TagWithUsageModel]:
        """Get all tags with their usage count (how many articles use each tag)"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sql = """SELECT t.id, t.name, t.knowledge_base_id, 
                                    COALESCE(COUNT(at.article_id), 0) as usage_count
                             FROM tags t
                             LEFT JOIN article_tags at ON t.id = at.tag_id
                             LEFT JOIN articles a ON at.article_id = a.id AND a.is_active = TRUE
                             WHERE t.knowledge_base_id = %s
                             GROUP BY t.id, t.name, t.knowledge_base_id
                             ORDER BY usage_count DESC, t.name;"""
                    cur.execute(sql, (knowledge_base_id,))
                    tags = cur.fetchall()
                    return [Tags.TagWithUsageModel(**tag) for tag in tags]
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_tags_with_usage_count: {e}")
            return []

    def search_articles_by_tags(self, knowledge_base_id: str, tag_names: List[str], match_all: bool = False) -> List[Article.BaseModel]:
        """Search articles by tag names. If match_all=True, articles must have ALL tags; if False, articles must have ANY tag"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Normalize tag names to lowercase
                    tag_names = [name.lower() for name in tag_names]
                    
                    if match_all:
                        # Articles must have ALL specified tags
                        sql = """SELECT DISTINCT a.* FROM articles a
                                 INNER JOIN article_tags at ON a.id = at.article_id
                                 INNER JOIN tags t ON at.tag_id = t.id
                                 WHERE a.knowledge_base_id = %s AND a.is_active = TRUE 
                                 AND t.name = ANY(%s)
                                 GROUP BY a.id, a.knowledge_base_id, a.title, a.content, a.author_id, 
                                         a.version, a.is_active, a.parent_id, a.created_at, a.updated_at, 
                                         a.created_by, a.updated_by
                                 HAVING COUNT(DISTINCT t.id) = %s
                                 ORDER BY a.title;"""
                        cur.execute(sql, (knowledge_base_id, tag_names, len(tag_names)))
                    else:
                        # Articles must have ANY of the specified tags
                        sql = """SELECT DISTINCT a.* FROM articles a
                                 INNER JOIN article_tags at ON a.id = at.article_id
                                 INNER JOIN tags t ON at.tag_id = t.id
                                 WHERE a.knowledge_base_id = %s AND a.is_active = TRUE 
                                 AND t.name = ANY(%s)
                                 ORDER BY a.title;"""
                        cur.execute(sql, (knowledge_base_id, tag_names))
                    
                    articles = cur.fetchall()
                    return [Article.BaseModel(**article) for article in articles]
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.search_articles_by_tags: {e}")
            return []  

# # Example usage:
# ops = PostgresOperations()
# print(ops.get_root_level_articles())
# # print(ops.get_build_definitions_by_project_id('Payroll'))

# print(ops.get_articles_by_parentids(['3', '7']))