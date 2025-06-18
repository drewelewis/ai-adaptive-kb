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
    WHERE a.knowledge_base_id = knowledge_base_id AND a.parent_id IS NULL AND a.is_active = TRUE

    UNION ALL

    SELECT
        a.id,
        a.title,
        u.name AS author,
        a.parent_id
    FROM articles a
    LEFT JOIN users u ON a.author_id = u.id
    INNER JOIN article_hierarchy ah ON a.parent_id = ah.id
    WHERE a.knowledge_base_id = knowledge_base_id AND a.is_active = TRUE
)
SELECT id, title, author, parent_id
FROM article_hierarchy
ORDER BY parent_id NULLS FIRST, id;
$$ LANGUAGE sql STABLE;

-- Usage:
-- SELECT * FROM get_article_hierarchy(1);

