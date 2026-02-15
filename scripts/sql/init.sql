-- Enterprise Database Initialization Script
-- Creates optimized schemas, indexes, and enterprise features

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create separate schemas for different concerns
CREATE SCHEMA IF NOT EXISTS app_data;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS ml;

-- Create optimized user table with enterprise features
CREATE TABLE IF NOT EXISTS app_data.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'patient' CHECK (role IN ('patient', 'doctor', 'admin', 'super_admin')),
    
    -- Profile data
    gender VARCHAR(20),
    blood_type VARCHAR(10),
    dob DATE,
    height DECIMAL(5,2),
    weight DECIMAL(5,2),
    existing_ailments TEXT,
    profile_picture TEXT,
    about_me TEXT,
    
    -- Lifestyle data
    diet VARCHAR(100),
    activity_level VARCHAR(100),
    sleep_hours DECIMAL(3,1),
    stress_level VARCHAR(50),
    
    -- Privacy and compliance
    allow_data_collection BOOLEAN DEFAULT true,
    data_retention_days INTEGER DEFAULT 2555, -- 7 years default
    consent_version VARCHAR(20) DEFAULT 'v1.0',
    
    -- Subscription
    plan_tier VARCHAR(50) DEFAULT 'free' CHECK (plan_tier IN ('free', 'pro', 'clinic', 'enterprise')),
    subscription_expiry TIMESTAMP WITH TIME ZONE,
    stripe_customer_id VARCHAR(255),
    
    -- Doctor specific
    consultation_fee DECIMAL(10,2) DEFAULT 500.00,
    license_number VARCHAR(100),
    specialization VARCHAR(255),
    
    -- AI memory
    psych_profile TEXT,
    
    -- Enterprise fields
    department VARCHAR(100),
    manager_id UUID REFERENCES app_data.users(id),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create comprehensive audit table
CREATE TABLE IF NOT EXISTS audit.activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES app_data.users(id),
    session_id VARCHAR(255),
    action_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create health records with enhanced tracking
CREATE TABLE IF NOT EXISTS app_data.health_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app_data.users(id),
    record_type VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    prediction JSONB,
    confidence_score DECIMAL(5,4),
    model_version VARCHAR(50),
    feature_importance JSONB,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'confirmed', 'flagged')),
    reviewed_by UUID REFERENCES app_data.users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    source_system VARCHAR(100),
    external_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create ML model registry
CREATE TABLE IF NOT EXISTS ml.model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100),
    framework VARCHAR(50),
    file_path VARCHAR(500),
    metadata JSONB,
    performance_metrics JSONB,
    is_active BOOLEAN DEFAULT false,
    deployed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, model_version)
);

-- Create model predictions table for monitoring
CREATE TABLE IF NOT EXISTS ml.predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES ml.model_registry(id),
    user_id UUID REFERENCES app_data.users(id),
    input_data JSONB NOT NULL,
    prediction JSONB NOT NULL,
    prediction_probability DECIMAL(5,4),
    prediction_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON app_data.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON app_data.users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON app_data.users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON app_data.users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON app_data.users(created_at);

CREATE INDEX IF NOT EXISTS idx_health_records_user_id ON app_data.health_records(user_id);
CREATE INDEX IF NOT EXISTS idx_health_records_type ON app_data.health_records(record_type);
CREATE INDEX IF NOT EXISTS idx_health_records_created_at ON app_data.health_records(created_at);
CREATE INDEX IF NOT EXISTS idx_health_records_status ON app_data.health_records(status);

CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit.activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit.activity_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action_type ON audit.activity_log(action_type);

CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON ml.predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON ml.predictions(timestamp);

-- GIN indexes for JSONB
CREATE INDEX IF NOT EXISTS idx_health_records_data_gin ON app_data.health_records USING GIN(data);
CREATE INDEX IF NOT EXISTS idx_health_records_prediction_gin ON app_data.health_records USING GIN(prediction);
CREATE INDEX IF NOT EXISTS idx_audit_old_values_gin ON audit.activity_log USING GIN(old_values);
CREATE INDEX IF NOT EXISTS idx_audit_new_values_gin ON audit.activity_log USING GIN(new_values);

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON app_data.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_health_records_updated_at BEFORE UPDATE ON app_data.health_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create audit trigger
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit.activity_log (
        user_id, action_type, resource_type, resource_id, 
        old_values, new_values, success
    ) VALUES (
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id)::TEXT,
        CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN to_jsonb(NEW) ELSE NULL END,
        true
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers
CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON app_data.users FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_health_records AFTER INSERT OR UPDATE OR DELETE ON app_data.health_records FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Create row-level security policies (HIPAA compliance)
ALTER TABLE app_data.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_data.health_records ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data (except admins)
CREATE POLICY user_isolation_policy ON app_data.users
    FOR ALL
    TO authenticated_user
    USING (id = current_setting('app.current_user_id')::UUID OR current_setting('app.user_role') = 'admin');

CREATE POLICY health_record_isolation_policy ON app_data.health_records
    FOR ALL
    TO authenticated_user
    USING (user_id = current_setting('app.current_user_id')::UUID OR current_setting('app.user_role') = 'admin');

-- Create views for common queries
CREATE OR REPLACE VIEW app_data.patient_summary AS
SELECT 
    u.id,
    u.full_name,
    u.email,
    u.dob,
    u.plan_tier,
    COUNT(hr.id) as total_records,
    MAX(hr.created_at) as last_record_date,
    array_agg(DISTINCT hr.record_type) as record_types
FROM app_data.users u
LEFT JOIN app_data.health_records hr ON u.id = hr.user_id
WHERE u.role = 'patient'
GROUP BY u.id, u.full_name, u.email, u.dob, u.plan_tier;

-- Create materialized view for analytics
CREATE MATERIALIZED VIEW app_data.health_analytics AS
SELECT 
    DATE_TRUNC('month', hr.created_at) as month,
    hr.record_type,
    COUNT(*) as record_count,
    AVG((hr.prediction->>'confidence')::DECIMAL) as avg_confidence,
    COUNT(DISTINCT hr.user_id) as unique_patients
FROM app_data.health_records hr
GROUP BY DATE_TRUNC('month', hr.created_at), hr.record_type
ORDER BY month DESC;

-- Create refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_health_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY app_data.health_analytics;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed)
GRANT USAGE ON SCHEMA app_data TO healthcare_admin;
GRANT USAGE ON SCHEMA audit TO healthcare_admin;
GRANT USAGE ON SCHEMA ml TO healthcare_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app_data TO healthcare_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO healthcare_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ml TO healthcare_admin;

-- Create default admin user (password should be changed immediately)
INSERT INTO app_data.users (username, email, hashed_password, full_name, role, plan_tier)
VALUES ('admin', 'admin@healthcare.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LFvO6', 'System Administrator', 'super_admin', 'enterprise')
ON CONFLICT (username) DO NOTHING;

COMMIT;
