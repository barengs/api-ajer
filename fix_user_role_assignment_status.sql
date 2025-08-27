-- SQL script to add the missing status field to user_role_assignments table
-- This should fix the FieldDoesNotExist error

-- First, let's check if the table exists and what columns it has
.schema user_role_assignments;

-- Add the status column if it doesn't exist
ALTER TABLE user_role_assignments
ADD COLUMN status VARCHAR(20) DEFAULT 'active';

-- Add the other missing columns that were added in the migration
ALTER TABLE user_role_assignments
ADD COLUMN effective_from DATETIME DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE user_role_assignments
ADD COLUMN effective_until DATETIME NULL;

ALTER TABLE user_role_assignments
ADD COLUMN assignment_reason TEXT DEFAULT '';

ALTER TABLE user_role_assignments ADD COLUMN notes TEXT DEFAULT '';

ALTER TABLE user_role_assignments
ADD COLUMN revoked_at DATETIME NULL;

ALTER TABLE user_role_assignments
ADD COLUMN revocation_reason TEXT DEFAULT '';

-- Add foreign key column for revoked_by (this might need to be adjusted based on your user table structure)
ALTER TABLE user_role_assignments
ADD COLUMN revoked_by_id INTEGER NULL;

-- Update the existing records to have the correct default status
UPDATE user_role_assignments
SET
    status = 'active'
WHERE
    status IS NULL;

-- Create indexes for the new columns
CREATE INDEX IF NOT EXISTS user_role_a_user_id_3de978_idx ON user_role_assignments (user_id, status);

CREATE INDEX IF NOT EXISTS user_role_a_role_id_3504f9_idx ON user_role_assignments (role_definition_id, status);

CREATE INDEX IF NOT EXISTS user_role_a_effecti_99f62e_idx ON user_role_assignments (
    effective_from,
    effective_until
);