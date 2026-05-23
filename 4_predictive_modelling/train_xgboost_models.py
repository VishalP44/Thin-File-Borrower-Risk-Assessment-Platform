import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import os

def train_evaluate_model(X, y, model_name):
    print(f"\n--- Training {model_name} Model ---")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    # Predict
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    print(f"ROC AUC: {roc_auc_score(y_test, y_prob):.4f}")
    print(classification_report(y_test, y_pred))
    
    # Feature Importance
    importance = pd.DataFrame({
        'Feature': X.columns,
        'Importance': model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    print("Top 5 Important Features:")
    print(importance.head())
    
    return model

def run_modelling(input_path, output_path):
    print(f"Loading features from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Split datasets
    thin_files = df[df['borrower_type'] == 'Thin File'].copy()
    traditional = df[df['borrower_type'] == 'Traditional'].copy()
    
    # Define features
    thin_features = [
        'age', 'utility_on_time_pct', 'rent_avg_days_late', 'mobile_disconnects',
        'avg_bank_balance', 'overdraft_events', 'job_tenure_months', 'savings_ratio',
        'debt_to_income_ratio', 'income_stability_score', 'is_gig_worker', 'payment_reliability_score'
    ]
    
    trad_features = thin_features + [
        'credit_score', 'traditional_payment_history_pct', 'credit_inquiries'
    ]
    
    # Train Thin File Model
    X_thin = thin_files[thin_features]
    y_thin = thin_files['is_default']
    thin_model = train_evaluate_model(X_thin, y_thin, "Thin File")
    
    # Train Traditional Model
    X_trad = traditional[trad_features]
    y_trad = traditional['is_default']
    trad_model = train_evaluate_model(X_trad, y_trad, "Traditional")
    
    # Predict on entire dataset to save for database
    print("\nPredicting on entire dataset to generate risk scores...")
    df['risk_probability'] = np.nan
    
    # Thin files prediction
    df.loc[df['borrower_type'] == 'Thin File', 'risk_probability'] = thin_model.predict_proba(df.loc[df['borrower_type'] == 'Thin File', thin_features])[:, 1]
    
    # Traditional prediction
    df.loc[df['borrower_type'] == 'Traditional', 'risk_probability'] = trad_model.predict_proba(df.loc[df['borrower_type'] == 'Traditional', trad_features])[:, 1]
    
    # Assign Risk Categories
    # Define thresholds
    def assign_risk_category(prob):
        if prob < 0.2:
            return 'Low Risk'
        elif prob < 0.6:
            return 'Medium Risk'
        else:
            return 'High Risk'
            
    df['risk_category'] = df['risk_probability'].apply(assign_risk_category)
    
    # Final cleanup before saving to DB ready file
    final_df = df.copy()
    final_df.to_csv(output_path, index=False)
    print(f"Risk assessments saved to {output_path}")

if __name__ == "__main__":
    input_path = 'data/borrower_features.csv'
    output_path = 'data/borrower_assessments.csv'
    
    if os.path.exists(input_path):
        run_modelling(input_path, output_path)
    else:
        print(f"Error: {input_path} not found. Run feature_engineering.py first.")
