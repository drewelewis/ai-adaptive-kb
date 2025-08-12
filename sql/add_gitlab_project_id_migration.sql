-- Migration script to add gitlab_project_id column to knowledge_base table
-- Run this script on existing databases to add GitLab integration support

-- Check if the column already exists to avoid errors
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'knowledge_base' 
        AND column_name = 'gitlab_project_id'
    ) THEN
        -- Add the gitlab_project_id column
        ALTER TABLE knowledge_base 
        ADD COLUMN gitlab_project_id INTEGER NULL;
        
        -- Add a comment to describe the column
        COMMENT ON COLUMN knowledge_base.gitlab_project_id IS 'GitLab project ID for issue tracking and project management';
        
        RAISE NOTICE 'Added gitlab_project_id column to knowledge_base table';
    ELSE
        RAISE NOTICE 'gitlab_project_id column already exists in knowledge_base table';
    END IF;
END $$;

-- Create an index on gitlab_project_id for better query performance
CREATE INDEX IF NOT EXISTS idx_knowledge_base_gitlab_project_id 
ON knowledge_base(gitlab_project_id) 
WHERE gitlab_project_id IS NOT NULL;

-- Show the updated table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'knowledge_base' 
ORDER BY ordinal_position;
