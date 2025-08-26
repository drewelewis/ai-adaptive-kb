import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT', 5432),
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    with conn.cursor() as cur:
        # Check KB 13
        cur.execute('SELECT id, name, gitlab_project_id FROM knowledge_base WHERE id = 13')
        kb_data = cur.fetchone()
        print(f'KB 13: {kb_data}')
        
        # Check reverse lookup  
        cur.execute('SELECT id, name FROM knowledge_base WHERE gitlab_project_id = 27')
        kb_reverse = cur.fetchone()
        print(f'GitLab Project 27 -> KB: {kb_reverse}')
        
        # Check all KB-GitLab associations
        cur.execute('SELECT id, name, gitlab_project_id FROM knowledge_base WHERE gitlab_project_id IS NOT NULL')
        associations = cur.fetchall()
        print(f'All KB-GitLab associations: {associations}')
        
    conn.close()
    print('✅ Database test successful')
except Exception as e:
    print(f'❌ Database error: {e}')
    import traceback
    traceback.print_exc()
