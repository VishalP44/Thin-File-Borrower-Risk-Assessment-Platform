import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def load_data_to_sqlite(csv_path, db_path, schema_path):
    print(f"Connecting to SQLite database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Execute schema creation
    print("Creating schema...")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    
    # 2. Load data
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # 3. Populate dim_borrower_profiles
    print("Populating dim_borrower_profiles...")
    profiles = df[['borrower_id', 'borrower_type', 'age', 'location', 'employment_type', 'is_gig_worker']].copy()
    profiles.to_sql('dim_borrower_profiles', conn, if_exists='replace', index=False)
    
    # 4. Populate dim_alternative_data
    print("Populating dim_alternative_data...")
    alt_data = df[['borrower_id', 'utility_on_time_pct', 'rent_avg_days_late', 'mobile_disconnects', 
                   'avg_bank_balance', 'overdraft_events', 'job_tenure_months']].copy()
    alt_data.to_sql('dim_alternative_data', conn, if_exists='replace', index=False)
    
    # 5. Populate dim_traditional_data
    print("Populating dim_traditional_data...")
    trad_data = df[['borrower_id', 'credit_score', 'traditional_payment_history_pct', 'credit_inquiries']].copy()
    trad_data.rename(columns={'traditional_payment_history_pct': 'payment_history_pct'}, inplace=True)
    trad_data.to_sql('dim_traditional_data', conn, if_exists='replace', index=False)
    
    # 6. Populate dim_risk_assessment
    print("Populating dim_risk_assessment...")
    risk_data = df[['borrower_id', 'risk_probability', 'risk_category']].copy()
    risk_data['assessment_date'] = datetime.now().strftime('%Y-%m-%d')
    risk_data['model_version'] = 'v1.0'
    risk_data.to_sql('dim_risk_assessment', conn, if_exists='replace', index=False)
    
    # 7. Populate dim_loan_performance
    print("Populating dim_loan_performance...")
    perf_data = df[['borrower_id', 'is_default']].copy()
    # Simulate months to default for those who defaulted
    perf_data['months_to_default'] = np.where(perf_data['is_default'] == 1, np.random.randint(1, 36, len(perf_data)), np.nan)
    perf_data['final_payment_status'] = np.where(perf_data['is_default'] == 1, 'Charged Off', 'Current')
    perf_data.to_sql('dim_loan_performance', conn, if_exists='replace', index=False)
    
    # 8. Populate fact_loan_applications
    print("Populating fact_loan_applications...")
    apps = pd.DataFrame()
    apps['borrower_id'] = df['borrower_id']
    apps['application_id'] = ['APP_' + str(i).zfill(6) for i in range(len(apps))]
    
    # Simulate application dates over the last year
    base_date = datetime.now() - timedelta(days=365)
    apps['application_date'] = [base_date + timedelta(days=np.random.randint(0, 365)) for _ in range(len(apps))]
    apps['application_date'] = apps['application_date'].dt.strftime('%Y-%m-%d')
    
    # Simulate loan amounts based on income and risk
    requested = df['monthly_income'] * np.random.uniform(1, 5, len(df))
    apps['requested_loan_amount'] = np.round(requested, 2)
    
    # Approval logic based on risk_category
    def determine_approval(row):
        risk = row['risk_category']
        if risk == 'Low Risk':
            return 'Approved'
        elif risk == 'Medium Risk':
            return np.random.choice(['Approved', 'Declined'], p=[0.7, 0.3])
        else:
            return np.random.choice(['Approved', 'Declined'], p=[0.2, 0.8])
            
    apps['loan_status'] = df.apply(determine_approval, axis=1)
    apps['approved_loan_amount'] = np.where(apps['loan_status'] == 'Approved', apps['requested_loan_amount'], 0)
    
    apps.to_sql('fact_loan_applications', conn, if_exists='replace', index=False)
    
    conn.commit()
    conn.close()
    print("Database population complete!")

if __name__ == "__main__":
    csv_path = 'data/borrower_assessments.csv'
    db_path = '5_sql_database/lending_operations.db'
    schema_path = '5_sql_database/create_star_schema.sql'
    
    if os.path.exists(csv_path):
        load_data_to_sqlite(csv_path, db_path, schema_path)
    else:
        print(f"Error: {csv_path} not found. Run train_xgboost_models.py first.")
