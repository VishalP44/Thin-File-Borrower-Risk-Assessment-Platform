# Thin File Borrower Risk Assessment Platform

## Project Overview
This project is an end-to-end system that assesses credit risk for borrowers with limited credit history (thin files). It aims to expand lending to underserved populations by using alternative data sources, solving a real fintech problem without relying exclusively on traditional credit scores.

## Architecture

1. **Stage 1: Data Exploration** - Gathering/generating alternative data signals (utility, rent, mobile phone, banking, employment).
2. **Stage 2: Feature Engineering** - Creating predictive features from raw data and normalizing them.
3. **Stage 3: Borrower Segmentation** - Separating borrowers into thin file vs. traditional to analyze risk drivers differently.
4. **Stage 4: Predictive Modelling** - Training separate XGBoost models for thin file and traditional borrowers to avoid bias.
5. **Stage 5: SQL Database** - A star schema storing borrower data, risk assessments, and alternative data signals.
6. **Stage 6: Analytical Queries** - SQL queries answering real lending business questions.
7. **Stage 7: Power BI Dashboard** - A guide to visualize operational metrics.
8. **Stage 8: Business Insights** - Executive report answering profitability and scaling questions.

## How to Run the Pipeline

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run data generation:
   ```bash
   python 1_data_exploration/generate_synthetic_data.py
   ```
3. Run feature engineering:
   ```bash
   python 2_feature_engineering/feature_engineering.py
   ```
4. Run borrower segmentation:
   ```bash
   python 3_borrower_segmentation/segmentation_analysis.py
   ```
5. Run predictive modelling:
   ```bash
   python 4_predictive_modelling/train_xgboost_models.py
   ```
6. Setup and load SQL Database:
   ```bash
   python 5_sql_database/load_data_to_sqlite.py
   ```
7. Review `6_analytical_queries/lending_decision_queries.sql` for analytical SQL queries.
8. Review `7_power_bi/PowerBI_Setup_Guide.md` for dashboard setup.
9. Review `8_business_insights/Executive_Summary.md` for the final report.

## Tech Stack
* **Python**: Pandas, NumPy, Scikit-Learn, XGBoost
* **Database**: SQLite / SQL
* **Visualization**: Power BI (concept/instructions)
