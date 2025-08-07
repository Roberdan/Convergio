-- 🗄️ Convergio Database Initialization Script
-- Dedicated to Mario and FightTheStroke Foundation 💜

-- 🔧 Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 📊 Create database if not exists (for development)
SELECT 'CREATE DATABASE convergio'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'convergio')\gexec

SELECT 'CREATE DATABASE convergio_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'convergio_test')\gexec

-- 👤 Create application user
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'convergio_app') THEN
        CREATE ROLE convergio_app WITH LOGIN PASSWORD 'convergio_secure_password';
    END IF;
END
$$;

-- 🔒 Grant permissions
GRANT CONNECT ON DATABASE convergio TO convergio_app;
GRANT CONNECT ON DATABASE convergio_test TO convergio_app;

-- 📝 Log initialization
INSERT INTO pg_stat_statements_info (dealloc) VALUES (0) ON CONFLICT DO NOTHING;

-- 🎉 Success message
DO $$
BEGIN
    RAISE NOTICE '🎉 Convergio database initialized successfully!';
    RAISE NOTICE '💜 Built with love for Mario and accessible AI for everyone';
END
$$;