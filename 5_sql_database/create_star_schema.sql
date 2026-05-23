-- create_star_schema.sql

-- Dimension Table: Borrower Profiles
CREATE TABLE IF NOT EXISTS dim_borrower_profiles (
    borrower_id TEXT PRIMARY KEY,
    borrower_type TEXT,
    age INTEGER,
    location TEXT,
    employment_type TEXT,
    is_gig_worker INTEGER
);

-- Dimension Table: Alternative Data Signals
CREATE TABLE IF NOT EXISTS dim_alternative_data (
    borrower_id TEXT PRIMARY KEY,
    utility_on_time_pct REAL,
    rent_avg_days_late REAL,
    mobile_disconnects INTEGER,
    avg_bank_balance REAL,
    overdraft_events INTEGER,
    job_tenure_months INTEGER,
    FOREIGN KEY (borrower_id) REFERENCES dim_borrower_profiles(borrower_id)
);

-- Dimension Table: Traditional Data Signals (Null for Thin Files)
CREATE TABLE IF NOT EXISTS dim_traditional_data (
    borrower_id TEXT PRIMARY KEY,
    credit_score REAL,
    payment_history_pct REAL,
    credit_inquiries REAL,
    FOREIGN KEY (borrower_id) REFERENCES dim_borrower_profiles(borrower_id)
);

-- Dimension Table: Risk Assessment
CREATE TABLE IF NOT EXISTS dim_risk_assessment (
    borrower_id TEXT PRIMARY KEY,
    assessment_date DATE,
    risk_probability REAL,
    risk_category TEXT,
    model_version TEXT,
    FOREIGN KEY (borrower_id) REFERENCES dim_borrower_profiles(borrower_id)
);

-- Dimension Table: Loan Performance
CREATE TABLE IF NOT EXISTS dim_loan_performance (
    borrower_id TEXT PRIMARY KEY,
    is_default INTEGER,
    months_to_default INTEGER, 
    final_payment_status TEXT,
    FOREIGN KEY (borrower_id) REFERENCES dim_borrower_profiles(borrower_id)
);

-- Fact Table: Borrower Loan Applications
CREATE TABLE IF NOT EXISTS fact_loan_applications (
    application_id TEXT PRIMARY KEY,
    borrower_id TEXT,
    application_date DATE,
    requested_loan_amount REAL,
    approved_loan_amount REAL,
    loan_status TEXT,
    FOREIGN KEY (borrower_id) REFERENCES dim_borrower_profiles(borrower_id)
);
