
-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);

-- Create articles table with hierarchical structure
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
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
    name TEXT UNIQUE NOT NULL
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

-- Insert sample tags
INSERT INTO tags (name) VALUES
('AI'),
('Multi-agent Systems'),
('Frameworks'),
('Tutorials'),
('Research');

-- Insert sample articles with hierarchical structure
INSERT INTO articles (title, content, author_id, parent_id) VALUES
('AI Multi-agent Frameworks', 'Introduction to AI Multi-agent Frameworks', 1, NULL),
('Overview of Multi-agent Systems', 'Detailed overview of multi-agent systems', 1, 1),
('Popular Frameworks', 'Discussion on popular AI multi-agent frameworks', 2, 1),
('JADE Framework', 'Introduction to JADE Framework', 2, 3),
('JADE Framework - Installation', 'How to install JADE Framework', 2, 4),
('JADE Framework - Examples', 'Examples using JADE Framework', 2, 4),
('PyMARL Framework', 'Introduction to PyMARL Framework', 1, 3),
('PyMARL Framework - Installation', 'How to install PyMARL Framework', 1, 7),
('PyMARL Framework - Examples', 'Examples using PyMARL Framework', 1, 7);

-- Insert sample article versions
INSERT INTO article_versions (article_id, title, content, version) VALUES
(1, 'AI Multi-agent Frameworks', 'Introduction to AI Multi-agent Frameworks - Version 1', 1),
(1, 'AI Multi-agent Frameworks', 'Introduction to AI Multi-agent Frameworks - Version 2', 2),
(4, 'JADE Framework', 'Introduction to JADE Framework - Version 1', 1),
(4, 'JADE Framework', 'Introduction to JADE Framework - Version 2', 2);

-- Insert sample article tags relationships
INSERT INTO article_tags (article_id, tag_id) VALUES
(1, 1),
(1, 2),
(1, 3),
(2, 2),
(3, 3),
(4, 3),
(5, 4),
(6, 4),
(7, 3),
(8, 4),
(9, 4);


-- Indexes for articles table
CREATE INDEX idx_articles_author_id ON articles(author_id);
CREATE INDEX idx_articles_parent_id ON articles(parent_id);
CREATE INDEX idx_articles_is_active ON articles(is_active);

-- Indexes for article_tags table
CREATE INDEX idx_article_tags_article_id ON article_tags(article_id);
CREATE INDEX idx_article_tags_tag_id ON article_tags(tag_id);

-- Indexes for article_versions table
CREATE INDEX idx_article_versions_article_id ON article_versions(article_id);
CREATE INDEX idx_article_versions_version ON article_versions(version);

-- Index for tags name (for fast lookup by name, though it's already UNIQUE)
-- This is optional since UNIQUE creates an index, but you can name it explicitly if desired
-- CREATE UNIQUE INDEX idx_tags_name ON tags(name);

-- Index for users email (for fast lookup by email, though it's already UNIQUE)
-- This is optional since UNIQUE creates an index, but you can name it explicitly if desired
-- CREATE UNIQUE INDEX idx_users_email ON users(email);