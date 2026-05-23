import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

def engineer_features(input_path, output_path):
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Copy DataFrame to avoid SettingWithCopyWarning
    features_df = df.copy()
    
    # 1. Handle Missing Values
    # Missing rent data could mean they don't rent (e.g., live with parents). Impute with worst case or median?
    # Let's impute with median for numeric columns
    features_df['rent_avg_days_late'] = features_df['rent_avg_days_late'].fillna(features_df['rent_avg_days_late'].median())
    
    # Traditional features will be missing for thin files. Leave them missing, as XGBoost handles missing data well.
    # We will just fill them with -1 if needed, but XGBoost can handle NaNs. Let's keep NaNs for traditional features.

    # 2. Financial Stability Features
    # Savings Ratio approximation: Bank balance / (Monthly income + 1)
    features_df['savings_ratio'] = features_df['avg_bank_balance'] / (features_df['monthly_income'] + 1)
    
    # Debt to Income Ratio
    features_df['debt_to_income_ratio'] = features_df['existing_debt'] / (features_df['monthly_income'] + 1)
    
    # Income Stability Score (inverse of fluctuation)
    features_df['income_stability_score'] = 100 - features_df['income_fluctuation_pct']
    
    # 3. Behavioral Features
    # Multiple Income Sources flag (Gig workers likely have multiple, or we can use employment type)
    features_df['is_gig_worker'] = (features_df['employment_type'] == 'Gig Worker').astype(int)
    
    # 4. Normalize Features
    # Normalizing alternative signals to a 0-1 scale
    scaler = MinMaxScaler()
    
    cols_to_normalize = [
        'utility_on_time_pct', 'rent_avg_days_late', 'mobile_disconnects', 
        'avg_bank_balance', 'overdraft_events', 'job_tenure_months',
        'savings_ratio', 'debt_to_income_ratio', 'income_stability_score'
    ]
    
    features_df[cols_to_normalize] = scaler.fit_transform(features_df[cols_to_normalize])
    
    # 5. Composite Risk Scores (Optional, but requested)
    # Payment Reliability Score (0-1, higher is better)
    # Utility is positive, rent and mobile disconnects are negative. 
    # Normalization above made rent and mobile disconnects 0-1 (higher means more days late / more disconnects)
    features_df['payment_reliability_score'] = (
        features_df['utility_on_time_pct'] * 0.5 +
        (1 - features_df['rent_avg_days_late']) * 0.3 +
        (1 - features_df['mobile_disconnects']) * 0.2
    )
    
    print(f"Feature engineering complete. Dataset shape: {features_df.shape}")
    
    # Save engineered dataset
    features_df.to_csv(output_path, index=False)
    print(f"Features saved to {output_path}")

if __name__ == "__main__":
    input_path = 'data/alternative_signals.csv'
    output_path = 'data/borrower_features.csv'
    
    if os.path.exists(input_path):
        engineer_features(input_path, output_path)
    else:
        print(f"Error: {input_path} not found. Run generate_synthetic_data.py first.")
