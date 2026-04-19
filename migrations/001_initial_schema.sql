CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS raw_healthcare_data (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255),
    age INTEGER,
    gender VARCHAR(50),
    blood_type VARCHAR(10),
    medical_condition VARCHAR(100),
    date_of_admission TIMESTAMP,
    doctor VARCHAR(255),
    hospital VARCHAR(255),
    insurance_provider VARCHAR(100),
    billing_amount DECIMAL(10,2),
    room_number INTEGER,
    admission_type VARCHAR(50),
    discharge_date TIMESTAMP,
    medication VARCHAR(100),
    test_results VARCHAR(50),
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cleaned_healthcare_data (
    id BIGSERIAL PRIMARY KEY,
    age INTEGER,
    gender VARCHAR(50),
    blood_type VARCHAR(10),
    medical_condition VARCHAR(100),
    billing_amount DECIMAL(10,2),
    admission_type VARCHAR(50),
    insurance_provider VARCHAR(100),
    medication VARCHAR(100),
    test_results VARCHAR(50),
    source_id BIGINT REFERENCES raw_healthcare_data(id),
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Data quality constraints
    CONSTRAINT chk_age_positive CHECK (age > 0 AND age < 120),
    CONSTRAINT chk_billing_positive CHECK (billing_amount >= 0),
    CONSTRAINT chk_gender_valid CHECK (gender IN ('Male', 'Female', 'Other')),
    CONSTRAINT chk_test_results_valid CHECK (test_results IN ('Normal', 'Abnormal', 'Inconclusive')),
    CONSTRAINT chk_admission_type_valid CHECK (admission_type IN ('Emergency', 'Urgent', 'Elective', 'New Born'))
);

CREATE TABLE IF NOT EXISTS model_registry (
    id BIGSERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_path TEXT,
    model_type VARCHAR(50),
    model_metadata JSONB,
    is_production BOOLEAN DEFAULT FALSE,
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, model_version)
);

CREATE TABLE IF NOT EXISTS model_metrics (
    id BIGSERIAL PRIMARY KEY,
    model_id BIGINT REFERENCES model_registry(id),
    model_type VARCHAR(50),
    accuracy DECIMAL(5,4),
    precision DECIMAL(5,4),
    recall DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    confusion_matrix TEXT,
    classification_report TEXT,
    training_samples INTEGER,
    test_samples INTEGER,
    training_time_seconds DECIMAL(10,2),
    is_active INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Validation constraints
    CONSTRAINT chk_accuracy_range CHECK (accuracy >= 0 AND accuracy <= 1),
    CONSTRAINT chk_precision_range CHECK (precision >= 0 AND precision <= 1),
    CONSTRAINT chk_recall_range CHECK (recall >= 0 AND recall <= 1),
    CONSTRAINT chk_f1_range CHECK (f1_score >= 0 AND f1_score <= 1)
);

CREATE TABLE IF NOT EXISTS prediction_logs (
    id BIGSERIAL PRIMARY KEY,
    input_data TEXT,
    prediction VARCHAR(50),
    confidence DECIMAL(5,4),
    model_version VARCHAR(50),
    model_id BIGINT REFERENCES model_registry(id),
    processing_time_ms INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_confidence_range CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE TABLE IF NOT EXISTS pipeline_audit (
    id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100),
    source_table VARCHAR(50),
    target_table VARCHAR(50),
    records_processed INTEGER,
    records_inserted INTEGER,
    records_failed INTEGER,
    error_summary TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_pipeline_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- Raw data indexes
CREATE INDEX IF NOT EXISTS idx_raw_data_created ON raw_healthcare_data(created_at);
CREATE INDEX IF NOT EXISTS idx_raw_data_medical_condition ON raw_healthcare_data(medical_condition);
CREATE INDEX IF NOT EXISTS idx_raw_data_admission_date ON raw_healthcare_data(date_of_admission);
CREATE INDEX IF NOT EXISTS idx_raw_data_not_deleted ON raw_healthcare_data(is_deleted) WHERE is_deleted = FALSE;

-- Cleaned data indexes
CREATE INDEX IF NOT EXISTS idx_cleaned_data_condition ON cleaned_healthcare_data(medical_condition);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_insurance ON cleaned_healthcare_data(insurance_provider);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_valid ON cleaned_healthcare_data(is_valid);
CREATE INDEX IF NOT EXISTS idx_cleaned_condition_insurance ON cleaned_healthcare_data(medical_condition, insurance_provider);
CREATE INDEX IF NOT EXISTS idx_cleaned_admission_type ON cleaned_healthcare_data(admission_type);
CREATE INDEX IF NOT EXISTS idx_cleaned_test_results ON cleaned_healthcare_data(test_results);

-- Model metrics indexes
CREATE INDEX IF NOT EXISTS idx_model_metrics_active ON model_metrics(is_active);
CREATE INDEX IF NOT EXISTS idx_model_metrics_model_type ON model_metrics(model_type);
CREATE INDEX IF NOT EXISTS idx_model_metrics_model_id ON model_metrics(model_id);

-- Prediction logs indexes
CREATE INDEX IF NOT EXISTS idx_prediction_logs_created ON prediction_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_model_version ON prediction_logs(model_version);
CREATE INDEX IF NOT EXISTS idx_predictions_model_confidence ON prediction_logs(model_version, confidence DESC) WHERE confidence IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_prediction_logs_model_id ON prediction_logs(model_id);

-- Pipeline audit indexes
CREATE INDEX IF NOT EXISTS idx_pipeline_audit_status ON pipeline_audit(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_audit_started ON pipeline_audit(started_at);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_raw_data_updated_at 
    BEFORE UPDATE ON raw_healthcare_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cleaned_data_updated_at 
    BEFORE UPDATE ON cleaned_healthcare_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS on all tables
ALTER TABLE raw_healthcare_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaned_healthcare_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_audit ENABLE ROW LEVEL SECURITY;

-- Service role full access policies
CREATE POLICY "Service role full access on raw" ON raw_healthcare_data
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on cleaned" ON cleaned_healthcare_data
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on registry" ON model_registry
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on metrics" ON model_metrics
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on predictions" ON prediction_logs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on audit" ON pipeline_audit
    FOR ALL USING (auth.role() = 'service_role');


COMMENT ON TABLE raw_healthcare_data IS 'Original ingested healthcare data before any processing';
COMMENT ON TABLE cleaned_healthcare_data IS 'Cleaned and validated healthcare records ready for ML training';
COMMENT ON TABLE model_registry IS 'Central registry for all trained ML models with versioning';
COMMENT ON TABLE model_metrics IS 'Performance metrics for trained ML models';
COMMENT ON TABLE prediction_logs IS 'Historical log of all model predictions with metadata';
COMMENT ON TABLE pipeline_audit IS 'Audit trail for ETL pipeline executions';

-- Column comments for cleaned_healthcare_data
COMMENT ON COLUMN cleaned_healthcare_data.test_results IS 'Normal, Abnormal, or Inconclusive';
COMMENT ON COLUMN cleaned_healthcare_data.admission_type IS 'Emergency, Urgent, Elective, or New Born';
COMMENT ON COLUMN cleaned_healthcare_data.is_valid IS 'Indicates if record passed all validation rules';
COMMENT ON COLUMN cleaned_healthcare_data.validation_errors IS 'JSON array of validation errors if is_valid is false';

-- Column comments for model_metrics
COMMENT ON COLUMN model_metrics.confusion_matrix IS 'JSON representation of confusion matrix';
COMMENT ON COLUMN model_metrics.classification_report IS 'JSON representation of per-class metrics';
COMMENT ON COLUMN model_metrics.is_active IS '1 for currently active production model, 0 otherwise';


-- Function to get current active model
CREATE OR REPLACE FUNCTION get_active_model(model_type_param VARCHAR)
RETURNS TABLE(
    model_id BIGINT,
    model_version VARCHAR,
    model_metadata JSONB
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT mr.id, mr.model_version, mr.model_metadata
    FROM model_registry mr
    INNER JOIN model_metrics mm ON mr.id = mm.model_id
    WHERE mr.model_type = model_type_param 
      AND mm.is_active = 1
    ORDER BY mm.created_at DESC
    LIMIT 1;
END;
$$;

-- Function to log prediction
CREATE OR REPLACE FUNCTION log_prediction(
    p_input_data TEXT,
    p_prediction VARCHAR,
    p_confidence DECIMAL,
    p_model_version VARCHAR,
    p_processing_time_ms INTEGER DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS BIGINT LANGUAGE plpgsql AS $$
DECLARE
    v_model_id BIGINT;
    v_log_id BIGINT;
BEGIN
    -- Get model ID from registry
    SELECT id INTO v_model_id
    FROM model_registry
    WHERE model_version = p_model_version
    LIMIT 1;
    
    -- Insert prediction log
    INSERT INTO prediction_logs (
        input_data, prediction, confidence, model_version, 
        model_id, processing_time_ms, ip_address, user_agent
    ) VALUES (
        p_input_data, p_prediction, p_confidence, p_model_version,
        v_model_id, p_processing_time_ms, p_ip_address, p_user_agent
    )
    RETURNING id INTO v_log_id;
    
    RETURN v_log_id;
END;
$$;