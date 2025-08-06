--POSTGRESQL SCHEMA FOR KNOWLEDGE BASE MANAGEMENT SYSTEM
DROP TABLE IF EXISTS article_versions CASCADE;
DROP TABLE IF EXISTS article_tags CASCADE;
DROP TABLE IF EXISTS articles CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS knowledge_base_versions CASCADE;
DROP TABLE IF EXISTS knowledge_base CASCADE;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);
--Knowledge Base Table
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);
-- Insert sample knowledge base entries
INSERT INTO knowledge_base (name, description, author_id, created_by, updated_by) VALUES
('Complete Guide to Retiring Before 60', 'A comprehensive guide on how to retire early and enjoy life.', 1, 1, 1),
('Comprehensive Guide to Building AI Solutions', 'A collection of tips and tricks for using AI in software development.', 2, 2, 2);

CREATE TABLE knowledge_base_versions (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER REFERENCES knowledge_base(id) ON DELETE CASCADE,
    title TEXT,
    description TEXT,
    version INTEGER,
    -- Audit fields
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Create articles table with hierarchical structure
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER REFERENCES knowledge_base(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    parent_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Create tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    knowledge_base_id INTEGER REFERENCES knowledge_base(id) ON DELETE CASCADE
);

-- Create article_tags table for many-to-many relationship between articles and tags
CREATE TABLE article_tags (
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

-- Create article_versions table for storing historical versions of articles
CREATE TABLE article_versions (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    title TEXT,
    content TEXT,
    version INTEGER,
    -- Audit fields
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);
-- Get level 1 articles (top-level articles) sql
SELECT a.id, a.title, a.content, a.created_at, a.updated_at, a.author_id, a.version, a.is_active
    FROM articles a
    WHERE parent_id IS NULL AND is_active = TRUE;


-- Insert sample users
INSERT INTO users (name, email) VALUES
('Alice Smith', 'alice@example.com'),
('Bob Johnson', 'bob@example.com');

-- =============================================
-- TRIGGERS FOR AUDIT TRAIL AND VERSIONING
-- =============================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to create article versions automatically
CREATE OR REPLACE FUNCTION create_article_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Only create version if content or title changed
    IF OLD.title IS DISTINCT FROM NEW.title OR OLD.content IS DISTINCT FROM NEW.content THEN
        INSERT INTO article_versions (article_id, title, content, version, created_by)
        VALUES (OLD.id, OLD.title, OLD.content, OLD.version, NEW.updated_by);
        
        -- Increment version number
        NEW.version = OLD.version + 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to create knowledge base versions automatically
CREATE OR REPLACE FUNCTION create_kb_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Only create version if name or description changed
    IF OLD.name IS DISTINCT FROM NEW.name OR OLD.description IS DISTINCT FROM NEW.description THEN
        INSERT INTO knowledge_base_versions (knowledge_base_id, title, description, version, created_by)
        VALUES (OLD.id, OLD.name, OLD.description, OLD.version, NEW.updated_by);
        
        -- Increment version number
        NEW.version = OLD.version + 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to knowledge_base table
CREATE TRIGGER trigger_kb_updated_at
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_kb_versioning
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW
    EXECUTE FUNCTION create_kb_version();

-- Apply triggers to articles table
CREATE TRIGGER trigger_articles_updated_at
    BEFORE UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_articles_versioning
    BEFORE UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION create_article_version();

-- Function: get_article_hierarchy(knowledge_base_id integer)
-- Returns the full article hierarchy (title and author) for a given knowledge_base_id
CREATE OR REPLACE FUNCTION get_article_hierarchy(knowledge_base_id integer)
RETURNS TABLE(
    id integer,
    title text,
    author text,
    parent_id integer
) AS $$
WITH RECURSIVE article_hierarchy AS (
    SELECT
        a.id,
        a.title,
        u.name AS author,
        a.parent_id
    FROM articles a
    LEFT JOIN users u ON a.author_id = u.id
    WHERE a.knowledge_base_id = get_article_hierarchy.knowledge_base_id AND a.parent_id IS NULL AND a.is_active = TRUE

    UNION ALL

    SELECT
        a.id,
        a.title,
        u.name AS author,
        a.parent_id
    FROM articles a
    LEFT JOIN users u ON a.author_id = u.id
    INNER JOIN article_hierarchy ah ON a.parent_id = ah.id
    WHERE a.knowledge_base_id = get_article_hierarchy.knowledge_base_id AND a.is_active = TRUE
)
SELECT id, title, author, parent_id
FROM article_hierarchy
ORDER BY parent_id NULLS FIRST, id;
$$ LANGUAGE sql STABLE;

-- Usage:
-- SELECT * FROM get_article_hierarchy(1);

-- Function: get_article_versions(article_id integer)
-- Returns all versions of a specific article
CREATE OR REPLACE FUNCTION get_article_versions(article_id integer)
RETURNS TABLE(
    version_id integer,
    title text,
    content text,
    version integer,
    created_by text,
    updated_at timestamp
) AS $$
SELECT 
    av.id as version_id,
    av.title,
    av.content,
    av.version,
    u.name as created_by,
    av.updated_at
FROM article_versions av
LEFT JOIN users u ON av.created_by = u.id
WHERE av.article_id = get_article_versions.article_id
ORDER BY av.version DESC;
$$ LANGUAGE sql STABLE;

-- Function: get_kb_versions(kb_id integer)  
-- Returns all versions of a specific knowledge base
CREATE OR REPLACE FUNCTION get_kb_versions(kb_id integer)
RETURNS TABLE(
    version_id integer,
    title text,
    description text,
    version integer,
    created_by text,
    updated_at timestamp
) AS $$
SELECT 
    kbv.id as version_id,
    kbv.title,
    kbv.description,
    kbv.version,
    u.name as created_by,
    kbv.updated_at
FROM knowledge_base_versions kbv
LEFT JOIN users u ON kbv.created_by = u.id
WHERE kbv.knowledge_base_id = get_kb_versions.kb_id
ORDER BY kbv.version DESC;
$$ LANGUAGE sql STABLE;

-- =============================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =============================================

-- Users table indexes
-- Note: users.id already has a PRIMARY KEY index (automatic with SERIAL PRIMARY KEY)
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_name ON users(name); -- For searching users by name

-- Knowledge base table indexes
CREATE INDEX idx_knowledge_base_author_id ON knowledge_base(author_id);
CREATE INDEX idx_knowledge_base_is_active ON knowledge_base(is_active);
CREATE INDEX idx_knowledge_base_created_at ON knowledge_base(created_at);
CREATE INDEX idx_knowledge_base_updated_at ON knowledge_base(updated_at);
CREATE INDEX idx_knowledge_base_active_author ON knowledge_base(is_active, author_id);

-- Knowledge base versions table indexes
CREATE INDEX idx_kb_versions_kb_id ON knowledge_base_versions(knowledge_base_id);
CREATE INDEX idx_kb_versions_version ON knowledge_base_versions(knowledge_base_id, version);
CREATE INDEX idx_kb_versions_updated_at ON knowledge_base_versions(updated_at);

-- Articles table indexes
CREATE INDEX idx_articles_knowledge_base_id ON articles(knowledge_base_id);
CREATE INDEX idx_articles_author_id ON articles(author_id);
CREATE INDEX idx_articles_parent_id ON articles(parent_id);
CREATE INDEX idx_articles_is_active ON articles(is_active);
CREATE INDEX idx_articles_created_at ON articles(created_at);
CREATE INDEX idx_articles_updated_at ON articles(updated_at);

-- Composite indexes for common query patterns
CREATE INDEX idx_articles_kb_active ON articles(knowledge_base_id, is_active);
CREATE INDEX idx_articles_parent_active ON articles(parent_id, is_active);
CREATE INDEX idx_articles_kb_parent_active ON articles(knowledge_base_id, parent_id, is_active);
CREATE INDEX idx_articles_active_created ON articles(is_active, created_at);

-- Text search indexes for LIKE queries
CREATE INDEX idx_articles_title_lower ON articles(lower(title));

-- Tags table indexes
CREATE INDEX idx_tags_knowledge_base_id ON tags(knowledge_base_id);
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_kb_name ON tags(knowledge_base_id, name);

-- Article tags table indexes (already has composite PK, but adding for reverse lookups)
CREATE INDEX idx_article_tags_tag_id ON article_tags(tag_id);
CREATE INDEX idx_article_tags_article_id ON article_tags(article_id);

-- Article versions table indexes
CREATE INDEX idx_article_versions_article_id ON article_versions(article_id);
CREATE INDEX idx_article_versions_version ON article_versions(article_id, version);
CREATE INDEX idx_article_versions_updated_at ON article_versions(updated_at);
CREATE INDEX idx_article_versions_article_updated ON article_versions(article_id, updated_at);

