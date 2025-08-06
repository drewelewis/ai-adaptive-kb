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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    author_id INTEGER REFERENCES users(id),
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE
);
-- Insert sample knowledge base entries
INSERT INTO knowledge_base (name, description, author_id) VALUES
('Complete Guide to Retiring Before 60', 'A comprehensive guide on how to retire early and enjoy life.', 1),
('Comprehensive Guide to Building AI Solutions', 'A collection of tips and tricks for using AI in software development.', 2);

CREATE TABLE knowledge_base_versions (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER REFERENCES knowledge_base(id),
    title TEXT,
    description TEXT,
    version INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create articles table with hierarchical structure
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER REFERENCES knowledge_base(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    author_id INTEGER REFERENCES users(id),
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    parent_id INTEGER REFERENCES articles(id)
);

-- Create tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    knowledge_base_id INTEGER REFERENCES knowledge_base(id)
);

-- Create article_tags table for many-to-many relationship between articles and tags
CREATE TABLE article_tags (
    article_id INTEGER REFERENCES articles(id),
    tag_id INTEGER REFERENCES tags(id),
    PRIMARY KEY (article_id, tag_id)
);

-- Create article_versions table for storing historical versions of articles
CREATE TABLE article_versions (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    title TEXT,
    content TEXT,
    version INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Get level 1 articles (top-level articles) sql
SELECT a.id, a.title, a.content, a.created_at, a.updated_at, a.author_id, a.version, a.is_active
    FROM articles a
    WHERE parent_id IS NULL AND is_active = TRUE;


-- Insert sample users
INSERT INTO users (name, email) VALUES
('Alice Smith', 'alice@example.com'),
('Bob Johnson', 'bob@example.com');

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

