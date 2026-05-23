import pandas as pd
import numpy as np
import os

np.random.seed(42)

def generate_synthetic_data(num_samples=10000):
    """
    Generates synthetic borrower data containing both traditional and alternative signals.
    Simulates ~30% thin file borrowers.
    """
    print(f"Generating synthetic dataset with {num_samples} samples...")
    
    # 1. Base Demographics
    borrower_ids = [f"B_{i:06d}" for i in range(num_samples)]
    age = np.random.randint(18, 70, num_samples)
    location = np.random.choice(['Urban', 'Suburban', 'Rural'], num_samples, p=[0.5, 0.3, 0.2])
    employment_type = np.random.choice(['Salaried', 'Self-Employed', 'Gig Worker', 'Unemployed'], num_samples, p=[0.6, 0.15, 0.2, 0.05])
    
    # 2. Assign Borrower Type (30% Thin File)
    # Thin files are more likely to be younger or gig workers
    prob_thin_file = np.where(age < 25, 0.6, 0.2)
    prob_thin_file = np.where(employment_type == 'Gig Worker', prob_thin_file + 0.3, prob_thin_file)
    prob_thin_file = np.clip(prob_thin_file, 0, 1)
    
    borrower_type = np.array(['Thin File' if np.random.rand() < p else 'Traditional' for p in prob_thin_file])
    
    # 3. Traditional Credit Features (Null for Thin File)
    credit_score = np.where(borrower_type == 'Traditional', np.random.normal(680, 80, num_samples), np.nan)
    credit_score = np.clip(credit_score, 300, 850)
    
    payment_history_pct = np.where(borrower_type == 'Traditional', np.random.beta(8, 2, num_samples) * 100, np.nan)
    credit_inquiries = np.where(borrower_type == 'Traditional', np.random.poisson(2, num_samples), np.nan)
    
    # 4. Alternative Data Signals
    # Utility
    utility_payments_on_time = np.random.beta(7, 3, num_samples) * 100
    # Adjust utility for unemployed
    utility_payments_on_time = np.where(employment_type == 'Unemployed', utility_payments_on_time - 15, utility_payments_on_time)
    
    # Rent
    rent_days_late = np.random.exponential(5, num_samples)
    
    # Mobile
    mobile_disconnects = np.random.poisson(0.5, num_samples)
    
    # Banking
    avg_bank_balance = np.random.lognormal(mean=7, sigma=1.5, size=num_samples)
    overdraft_events = np.random.poisson(1, num_samples)
    
    # Adjust banking for higher income
    avg_bank_balance = np.where(employment_type == 'Salaried', avg_bank_balance * 1.5, avg_bank_balance)
    
    # Employment & Income
    job_tenure_months = np.random.exponential(36, num_samples)
    monthly_income = np.random.lognormal(mean=8, sigma=0.8, size=num_samples)
    income_fluctuation_pct = np.random.uniform(0, 50, num_samples)
    income_fluctuation_pct = np.where(employment_type == 'Salaried', income_fluctuation_pct * 0.2, income_fluctuation_pct)
    
    existing_debt = np.random.lognormal(mean=7, sigma=1.2, size=num_samples)
    
    # 5. Calculate Target Variable (Default)
    # The probability of default is a hidden function of the signals
    
    # Base risk score (lower is worse)
    hidden_risk_score = (
        (utility_payments_on_time * 0.1) - 
        (rent_days_late * 0.5) - 
        (mobile_disconnects * 2) + 
        np.log1p(avg_bank_balance) - 
        (overdraft_events * 3) +
        (job_tenure_months * 0.05) -
        (income_fluctuation_pct * 0.1)
    )
    
    # Add traditional credit risk for traditional borrowers
    hidden_risk_score = np.where(
        borrower_type == 'Traditional', 
        hidden_risk_score + (np.nan_to_num(credit_score) - 600) * 0.05, 
        hidden_risk_score
    )
    
    # Convert score to default probability (sigmoid)
    default_prob = 1 / (1 + np.exp(hidden_risk_score * 0.1))
    default_prob = np.clip(default_prob, 0.01, 0.95)
    
    is_default = np.random.binomial(1, default_prob)
    
    # Create DataFrame
    df = pd.DataFrame({
        'borrower_id': borrower_ids,
        'age': age,
        'location': location,
        'employment_type': employment_type,
        'borrower_type': borrower_type,
        'credit_score': credit_score,
        'traditional_payment_history_pct': payment_history_pct,
        'credit_inquiries': credit_inquiries,
        'utility_on_time_pct': np.clip(utility_payments_on_time, 0, 100),
        'rent_avg_days_late': np.clip(rent_days_late, 0, 60),
        'mobile_disconnects': mobile_disconnects,
        'avg_bank_balance': np.round(avg_bank_balance, 2),
        'overdraft_events': overdraft_events,
        'job_tenure_months': np.round(job_tenure_months),
        'monthly_income': np.round(monthly_income, 2),
        'income_fluctuation_pct': np.round(income_fluctuation_pct, 2),
        'existing_debt': np.round(existing_debt, 2),
        'is_default': is_default
    })
    
    # Introduce some missing values realistically
    # Not everyone has rent data
    mask_rent = np.random.rand(num_samples) < 0.2
    df.loc[mask_rent, 'rent_avg_days_late'] = np.nan
    
    return df

if __name__ == "__main__":
    df = generate_synthetic_data(10000)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save raw alternative signals
    output_path = 'data/alternative_signals.csv'
    df.to_csv(output_path, index=False)
    
    print(f"Dataset generated and saved to {output_path}")
    print("\nDataset Summary:")
    print(df['borrower_type'].value_counts(normalize=True) * 100)
    print("\nDefault Rates by Borrower Type:")
    print(df.groupby('borrower_type')['is_default'].mean() * 100)
