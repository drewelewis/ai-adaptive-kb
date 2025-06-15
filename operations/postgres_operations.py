import os
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv(override=True)

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', 5432)
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

class PostgresOperations:
    def _get_connection(self):
        return psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )

    def get_root_level_articles(self) -> list[str]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * from articles WHERE parent_id IS NULL AND is_active = TRUE;")
                    articles = cur.fetchall()
                    return articles
        except Exception as e:
            print(f"An error occurred with PostgresOperations.get_root_level_articles: {e}")
            return []

    def get_articles_by_parentids(self, parent_ids: list[str]) -> list[str]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Dynamically build the correct number of placeholders
                    parent_ids = ', '.join(parent_ids)
                    sql = f"SELECT * FROM articles WHERE parent_id IN ({parent_ids}) AND is_active = TRUE;"
                    cur.execute(sql, parent_ids)
                    articles = cur.fetchall()
                    return articles
        except Exception as e:
            print(f"An error occurred with PostgresOperations.get_articles_by_parentids: {e}")
            return []
    
        

# # Example usage:
# ops = PostgresOperations()
# print(ops.get_root_level_articles())
# # print(ops.get_build_definitions_by_project_id('Payroll'))

# print(ops.get_articles_by_parentids(['3', '7']))