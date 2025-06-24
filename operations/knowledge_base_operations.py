import os
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from models.article import Article
from models.knowledge_base import KnowledgeBase

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
                    return str(knowledge_bases)
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.get_knowledge_bases: {e}")
            return []
    # update knowledge base by id
    def update_knowledge_base(self, knowledge_base: KnowledgeBase.UpdateModel) -> Optional[KnowledgeBase.BaseModel]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    sql = """UPDATE knowledge_base
                             SET name = %s, description = %s, author_id = %s
                             WHERE id = %s RETURNING id;"""
                    cur.execute(sql, (knowledge_base.name, knowledge_base.description, knowledge_base.author_id, knowledge_base.id))
                    id = cur.fetchone()[0]
                    conn.commit()
                    updated_knowledge_base = KnowledgeBase.BaseModel(
                        id=id,
                        name=knowledge_base.name,
                        description=knowledge_base.description,
                        author_id=knowledge_base.author_id
                    )
                    return updated_knowledge_base
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.update_knowledge_base: {e}")
            return None
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
                    sql = """INSERT INTO knowledge_base (name, description, author_id)
                             VALUES (%s, %s, %s) RETURNING id;"""
                    cur.execute(sql, (knowledge_base.name, knowledge_base.description, knowledge_base.author_id))
                    id = cur.fetchone()[0]
                    conn.commit()
 
                    return id
        except Exception as e:
            print(f"An error occurred with KnowledgeBaseOperations.insert_knowledge_base: {e}")
            return None

        # get article_hierarchy function is a recursive function that returns the hierarchy of articles in a knowledge base
    def get_article_hierarchy(self, knowledge_base_id: str) -> List[Article.HierarchyModel]:
        try:
            with self._get_connection() as conn:
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
            print(f"An error occurred with KnowledgeBaseOperations.insert_article: {e}")
            return None  

# # Example usage:
# ops = PostgresOperations()
# print(ops.get_root_level_articles())
# # print(ops.get_build_definitions_by_project_id('Payroll'))

# print(ops.get_articles_by_parentids(['3', '7']))