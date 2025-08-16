-- PostgreSQL initialization script
-- This file is executed when the database is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create database if it doesn't exist (this line might not be needed as the database is created by POSTGRES_DB)
-- CREATE DATABASE cyber_werewolves;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE cyber_werewolves TO werewolves;

-- You can add any initial data here if needed
-- For example, default LLM providers:

-- INSERT INTO providers (id, name, type, base_url, api_key, default_model, enabled) VALUES 
-- ('prov-openai-default', 'OpenAI Default', 'openai', 'https://api.openai.com/v1', 'your-api-key-here', 'gpt-4o-mini', true),
-- ('prov-anthropic-default', 'Anthropic Default', 'anthropic', 'https://api.anthropic.com', 'your-api-key-here', 'claude-3-haiku', true);