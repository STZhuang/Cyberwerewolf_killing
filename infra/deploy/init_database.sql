-- Database initialization script for Cyber Werewolves
-- This script creates all necessary tables and indexes

-- Create database (uncomment if needed)
-- CREATE DATABASE cyber_werewolves;
-- \c cyber_werewolves;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    username VARCHAR(100) UNIQUE NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    banned BOOLEAN DEFAULT FALSE
);

-- Rooms table
CREATE TABLE IF NOT EXISTS rooms (
    id VARCHAR(255) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    code VARCHAR(10) UNIQUE NOT NULL,
    host_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'playing', 'closed')),
    max_players INTEGER DEFAULT 9,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Room members table
CREATE TABLE IF NOT EXISTS room_members (
    room_id VARCHAR(255) NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seat INTEGER,
    is_bot BOOLEAN DEFAULT FALSE,
    agent_id VARCHAR(255),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,
    PRIMARY KEY (room_id, user_id)
);

-- Games table
CREATE TABLE IF NOT EXISTS games (
    id VARCHAR(255) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    room_id VARCHAR(255) NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    seed VARCHAR(255) NOT NULL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    config JSONB,
    version INTEGER DEFAULT 1,
    current_phase VARCHAR(20) DEFAULT 'Lobby',
    current_round INTEGER DEFAULT 0
);

-- Game players table
CREATE TABLE IF NOT EXISTS game_players (
    game_id VARCHAR(255) NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seat INTEGER NOT NULL,
    role VARCHAR(20),
    alive BOOLEAN DEFAULT TRUE,
    alignment VARCHAR(20),
    is_bot BOOLEAN DEFAULT FALSE,
    agent_id VARCHAR(255),
    PRIMARY KEY (game_id, user_id)
);

-- Events table (event sourcing)
CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(255) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    game_id VARCHAR(255) NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(50) NOT NULL,
    actor VARCHAR(20), -- seat number or "system"
    payload JSONB,
    hash VARCHAR(64) NOT NULL,
    prev_hash VARCHAR(64)
);

-- Action records table (idempotency)
CREATE TABLE IF NOT EXISTS actions (
    idempotency_key VARCHAR(255) PRIMARY KEY,
    request JSONB,
    status VARCHAR(20),
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM Providers table
CREATE TABLE IF NOT EXISTS providers (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('openai', 'anthropic', 'gemini', 'openrouter', 'vllm', 'custom')),
    base_url TEXT NOT NULL,
    api_key TEXT NOT NULL, -- Should be encrypted in production
    default_model VARCHAR(100) NOT NULL,
    headers JSONB DEFAULT '{}',
    timeout_s INTEGER DEFAULT 60,
    rate_limit_tpm INTEGER,
    rate_limit_rpm INTEGER,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM Presets table
CREATE TABLE IF NOT EXISTS presets (
    id VARCHAR(255) PRIMARY KEY,
    provider_id VARCHAR(255) NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    temperature INTEGER DEFAULT 70, -- stored as int * 100
    top_p INTEGER DEFAULT 100,
    max_tokens INTEGER DEFAULT 2048,
    seed INTEGER,
    stop JSONB,
    modalities JSONB DEFAULT '["text"]',
    tools_allowed BOOLEAN DEFAULT TRUE,
    vision_max_pixels INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM Bindings table
CREATE TABLE IF NOT EXISTS bindings (
    id VARCHAR(255) PRIMARY KEY,
    scope VARCHAR(20) NOT NULL CHECK (scope IN ('global', 'room', 'seat', 'agent_role')),
    scope_key VARCHAR(255) NOT NULL,
    preset_id VARCHAR(255) NOT NULL REFERENCES presets(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_rooms_host_id ON rooms(host_id);
CREATE INDEX IF NOT EXISTS idx_rooms_status ON rooms(status);
CREATE INDEX IF NOT EXISTS idx_room_members_room_id ON room_members(room_id);
CREATE INDEX IF NOT EXISTS idx_room_members_user_id ON room_members(user_id);
CREATE INDEX IF NOT EXISTS idx_games_room_id ON games(room_id);
CREATE INDEX IF NOT EXISTS idx_game_players_game_id ON game_players(game_id);
CREATE INDEX IF NOT EXISTS idx_game_players_seat ON game_players(game_id, seat);
CREATE INDEX IF NOT EXISTS idx_events_game_id ON events(game_id);
CREATE INDEX IF NOT EXISTS idx_events_game_id_idx ON events(game_id, idx);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_presets_provider_id ON presets(provider_id);
CREATE INDEX IF NOT EXISTS idx_bindings_scope ON bindings(scope, scope_key);
CREATE INDEX IF NOT EXISTS idx_bindings_preset_id ON bindings(preset_id);

-- Insert default LLM configurations
INSERT INTO providers (id, name, type, base_url, api_key, default_model) VALUES 
('prov-openai-default', 'OpenAI Default', 'openai', 'https://api.openai.com/v1', 'placeholder-key', 'gpt-4o-mini')
ON CONFLICT (id) DO NOTHING;

INSERT INTO presets (id, provider_id, model_id, name, temperature, max_tokens) VALUES 
('preset-default', 'prov-openai-default', 'gpt-4o-mini', 'Default Config', 70, 2048),
('preset-creative-wolf', 'prov-openai-default', 'gpt-4o-mini', 'Creative Werewolf', 85, 1536),
('preset-analytical-seer', 'prov-openai-default', 'gpt-4o-mini', 'Analytical Seer', 40, 1024)
ON CONFLICT (id) DO NOTHING;

INSERT INTO bindings (id, scope, scope_key, preset_id, priority) VALUES 
('bind-global-default', 'global', '*', 'preset-default', 0),
('bind-role-werewolf', 'agent_role', 'Werewolf', 'preset-creative-wolf', 10),
('bind-role-seer', 'agent_role', 'Seer', 'preset-analytical-seer', 10)
ON CONFLICT (id) DO NOTHING;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO werewolf_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO werewolf_user;