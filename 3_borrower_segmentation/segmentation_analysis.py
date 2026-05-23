import pandas as pd
import os

def run_segmentation_analysis(input_path, report_output_path):
    print(f"Loading features from {input_path}...")
    df = pd.read_csv(input_path)
    
    # 1. Overall Demographics
    total_borrowers = len(df)
    thin_files = df[df['borrower_type'] == 'Thin File']
    traditional = df[df['borrower_type'] == 'Traditional']
    
    thin_file_pct = (len(thin_files) / total_borrowers) * 100
    
    with open(report_output_path, 'w') as f:
        f.write("# Borrower Segmentation Analysis\n\n")
        f.write(f"Total Borrowers: {total_borrowers}\n")
        f.write(f"Thin File Borrowers: {len(thin_files)} ({thin_file_pct:.2f}%)\n")
        f.write(f"Traditional Borrowers: {len(traditional)} ({(100 - thin_file_pct):.2f}%)\n\n")
        
        # 2. Default Rates
        f.write("## Default Rates\n")
        overall_default = df['is_default'].mean() * 100
        thin_default = thin_files['is_default'].mean() * 100
        trad_default = traditional['is_default'].mean() * 100
        
        f.write(f"Overall Default Rate: {overall_default:.2f}%\n")
        f.write(f"Thin File Default Rate: {thin_default:.2f}%\n")
        f.write(f"Traditional Default Rate: {trad_default:.2f}%\n\n")
        
        # 3. Feature Comparison
        f.write("## Feature Comparison (Means)\n")
        features_to_compare = [
            'age', 'utility_on_time_pct', 'rent_avg_days_late', 
            'avg_bank_balance', 'payment_reliability_score', 'income_stability_score'
        ]
        
        comp_df = df.groupby('borrower_type')[features_to_compare].mean().T
        f.write(comp_df.to_markdown() + "\n\n")
        
    print(f"Segmentation analysis complete. Report saved to {report_output_path}")

if __name__ == "__main__":
    input_path = 'data/borrower_features.csv'
    report_output_path = '3_borrower_segmentation/segmentation_report.md'
    
    if os.path.exists(input_path):
        run_segmentation_analysis(input_path, report_output_path)
    else:
        print(f"Error: {input_path} not found. Run feature_engineering.py first.")
