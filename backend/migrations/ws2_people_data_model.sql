-- WS2: People Data Model Migration
-- Adds role, tier, skills, rates, availability, and timezone to talents table
-- Creates project_assignments table for team/project relationships
-- Created: 2025-12-28

BEGIN;

-- ============================================================================
-- WS2-A: Add new columns to talents table
-- ============================================================================

-- Add role column (job title/role)
ALTER TABLE talents ADD COLUMN IF NOT EXISTS role VARCHAR(255);

-- Add tier column (seniority level: junior, mid, senior, lead, principal)
ALTER TABLE talents ADD COLUMN IF NOT EXISTS tier VARCHAR(50);

-- Add skills column (JSONB array of skill objects)
-- Example: [{"name": "Python", "level": "expert", "years": 5}, {"name": "React", "level": "intermediate", "years": 2}]
ALTER TABLE talents ADD COLUMN IF NOT EXISTS skills JSONB DEFAULT '[]'::jsonb;

-- Add hourly_rate column (in USD)
ALTER TABLE talents ADD COLUMN IF NOT EXISTS hourly_rate DECIMAL(10, 2);

-- Add daily_rate column (in USD)
ALTER TABLE talents ADD COLUMN IF NOT EXISTS daily_rate DECIMAL(10, 2);

-- Add availability column (0-100 percentage)
ALTER TABLE talents ADD COLUMN IF NOT EXISTS availability INTEGER DEFAULT 100 CHECK (availability >= 0 AND availability <= 100);

-- Add timezone column (e.g., 'Europe/Rome', 'America/New_York')
ALTER TABLE talents ADD COLUMN IF NOT EXISTS timezone VARCHAR(100) DEFAULT 'UTC';

-- Add phone column if not exists
ALTER TABLE talents ADD COLUMN IF NOT EXISTS phone VARCHAR(50);

-- Add location column if not exists
ALTER TABLE talents ADD COLUMN IF NOT EXISTS location VARCHAR(255);

-- Add experience_years column if not exists
ALTER TABLE talents ADD COLUMN IF NOT EXISTS experience_years INTEGER DEFAULT 0;

-- Add bio/description column if not exists
ALTER TABLE talents ADD COLUMN IF NOT EXISTS bio TEXT;

-- Add rating column if not exists
ALTER TABLE talents ADD COLUMN IF NOT EXISTS rating DECIMAL(3, 2) DEFAULT 0.00 CHECK (rating >= 0 AND rating <= 5);

-- ============================================================================
-- WS2-B: Create project_assignments table
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_assignments (
    id SERIAL PRIMARY KEY,

    -- Reference to project
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Resource type: 'talent' for humans, 'agent' for AI agents
    resource_type VARCHAR(20) NOT NULL CHECK (resource_type IN ('talent', 'agent')),

    -- Resource ID (talent_id or agent_id depending on resource_type)
    resource_id INTEGER NOT NULL,

    -- Allocation percentage (0-100)
    allocation_pct INTEGER NOT NULL DEFAULT 100 CHECK (allocation_pct >= 0 AND allocation_pct <= 100),

    -- Role in project (e.g., 'Lead Developer', 'QA Engineer', 'Project Manager')
    role_in_project VARCHAR(255),

    -- Assignment dates
    start_date DATE,
    end_date DATE,

    -- Status of assignment
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'cancelled')),

    -- Billing information
    billable BOOLEAN DEFAULT true,
    hourly_rate_override DECIMAL(10, 2),  -- Override talent's default rate for this project

    -- Notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure unique assignment per resource per project
    UNIQUE (project_id, resource_type, resource_id)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_project_assignments_project_id ON project_assignments(project_id);
CREATE INDEX IF NOT EXISTS idx_project_assignments_resource ON project_assignments(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_project_assignments_status ON project_assignments(status);
CREATE INDEX IF NOT EXISTS idx_project_assignments_dates ON project_assignments(start_date, end_date);

-- ============================================================================
-- Add indexes for new talent columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_talents_role ON talents(role);
CREATE INDEX IF NOT EXISTS idx_talents_tier ON talents(tier);
CREATE INDEX IF NOT EXISTS idx_talents_availability ON talents(availability);
CREATE INDEX IF NOT EXISTS idx_talents_skills ON talents USING GIN (skills);

-- ============================================================================
-- Create trigger to update updated_at on project_assignments
-- ============================================================================

CREATE OR REPLACE FUNCTION update_project_assignments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_project_assignments_updated_at ON project_assignments;
CREATE TRIGGER trigger_update_project_assignments_updated_at
    BEFORE UPDATE ON project_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_project_assignments_updated_at();

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON COLUMN talents.role IS 'Job title or role (e.g., Software Engineer, Product Manager)';
COMMENT ON COLUMN talents.tier IS 'Seniority level: junior, mid, senior, lead, principal';
COMMENT ON COLUMN talents.skills IS 'JSONB array of skill objects with name, level, and years';
COMMENT ON COLUMN talents.hourly_rate IS 'Standard hourly rate in USD';
COMMENT ON COLUMN talents.daily_rate IS 'Standard daily rate in USD';
COMMENT ON COLUMN talents.availability IS 'Current availability percentage (0-100)';
COMMENT ON COLUMN talents.timezone IS 'IANA timezone identifier (e.g., Europe/Rome)';

COMMENT ON TABLE project_assignments IS 'Links talents and AI agents to projects with allocation and billing info';
COMMENT ON COLUMN project_assignments.resource_type IS 'Type of resource: talent (human) or agent (AI)';
COMMENT ON COLUMN project_assignments.allocation_pct IS 'Percentage of time allocated to this project (0-100)';
COMMENT ON COLUMN project_assignments.role_in_project IS 'Specific role for this project (may differ from talent.role)';

COMMIT;
