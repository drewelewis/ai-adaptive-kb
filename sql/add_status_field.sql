-- Add status field to knowledge_base table
-- This supports the workflow: to_do -> in_progress -> done

-- Add the status column with enum values
DO $$ 
BEGIN
    -- Create enum type if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'kb_status') THEN
        CREATE TYPE kb_status AS ENUM ('to_do', 'in_progress', 'done');
    END IF;
END $$;

-- Add the status column with default value 'to_do'
ALTER TABLE knowledge_base 
ADD COLUMN IF NOT EXISTS status kb_status DEFAULT 'to_do';

-- Update existing records to have 'to_do' status if NULL
UPDATE knowledge_base 
SET status = 'to_do' 
WHERE status IS NULL;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_knowledge_base_status ON knowledge_base(status);

-- Add comment for documentation
COMMENT ON COLUMN knowledge_base.status IS 'Status of the knowledge base: to_do (ready to start), in_progress (actively working), done (completed)';
