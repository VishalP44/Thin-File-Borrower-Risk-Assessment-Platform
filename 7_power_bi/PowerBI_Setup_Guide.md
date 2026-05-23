# Power BI Dashboard: Thin File Lending Operations Setup Guide

This guide explains how to connect Power BI to the SQLite database and create the requested visual dashboard for lending operations teams.

## 1. Connect Power BI to SQLite Database

1. Download and install the **SQLite ODBC Driver** (e.g., from [ch-werner.de/sqliteodbc](http://www.ch-werner.de/sqliteodbc/)).
2. Open the **ODBC Data Source Administrator** on your Windows machine.
3. Add a new System DSN using the "SQLite3 ODBC Driver".
4. Name the Data Source (e.g., `LendingDB`) and browse to select the `5_sql_database/lending_operations.db` file from this project.
5. In **Power BI Desktop**, go to **Get Data > Other > ODBC**.
6. Select your `LendingDB` DSN.
7. Select all tables (`dim_borrower_profiles`, `dim_alternative_data`, `dim_risk_assessment`, `dim_loan_performance`, `fact_loan_applications`) and click **Load**.

## 2. Configure Data Model Relationships

In the **Model View** of Power BI, ensure the following 1-to-1 or 1-to-many relationships are established using `borrower_id`:
* `dim_borrower_profiles` (1) <---> (Many) `fact_loan_applications`
* `dim_borrower_profiles` (1) <---> (1) `dim_alternative_data`
* `dim_borrower_profiles` (1) <---> (1) `dim_risk_assessment`
* `dim_borrower_profiles` (1) <---> (1) `dim_loan_performance`

## 3. Create Key Measures (DAX)

Create the following measures to use in your visuals:

```dax
Total Borrowers = COUNTROWS(dim_borrower_profiles)

Approval Rate = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_loan_applications), fact_loan_applications[loan_status] = "Approved"),
    COUNTROWS(fact_loan_applications)
)

Default Rate = 
DIVIDE(
    SUM(dim_loan_performance[is_default]),
    CALCULATE(COUNTROWS(fact_loan_applications), fact_loan_applications[loan_status] = "Approved")
)

Average Risk Score = AVERAGE(dim_risk_assessment[risk_probability])
```

## 4. Build the Dashboard Layout

### Top KPIs (Card Visuals)
Add 5 Card visuals to the top of your canvas using the DAX measures:
1. **Total Borrowers**: `Total Borrowers` measure.
2. **Thin File Count vs Traditional Count**: Multi-row card grouping by `dim_borrower_profiles[borrower_type]`.
3. **Approval Rate**: `Approval Rate` measure (format as %).
4. **Default Rate**: `Default Rate` measure (format as %).
5. **Average Risk Score**: `Average Risk Score` measure.

### Analysis Cards (Charts)
1. **Approval rate trend over time**:
   * Visual: Line Chart
   * X-axis: `fact_loan_applications[application_date]` (Month/Year hierarchy)
   * Y-axis: `Approval Rate` measure
2. **Default rate by borrower type**:
   * Visual: Clustered Bar Chart
   * Y-axis: `dim_borrower_profiles[borrower_type]`
   * X-axis: `Default Rate` measure
3. **Borrower distribution (thin file vs traditional)**:
   * Visual: Donut Chart
   * Legend: `dim_borrower_profiles[borrower_type]`
   * Values: `Total Borrowers` measure
4. **Default rate by risk category and borrower type**:
   * Visual: Matrix (Heatmap)
   * Rows: `dim_risk_assessment[risk_category]`
   * Columns: `dim_borrower_profiles[borrower_type]`
   * Values: `Default Rate` measure (apply conditional formatting for background color).

### Deep Dive Tables (Table/Matrix Visuals)
1. **Top 50 approved thin file borrowers**:
   * Visual: Table
   * Columns: `borrower_id`, `risk_probability`, `approved_loan_amount`, `employment_type`.
   * Filters: `borrower_type` = "Thin File", `loan_status` = "Approved".
   * Sort: `risk_probability` descending. Limit to Top 50 using N filter.
2. **Top defaulted borrowers (Early Defaults)**:
   * Visual: Table
   * Columns: `borrower_id`, `months_to_default`.
   * Filters: `is_default` = 1.
   * Sort: `months_to_default` ascending. Limit to Top 50 using N filter.

### Filters and Slicers (Slicer Visuals)
Add Slicer visuals to the left side or top of the report:
* **Date Range**: `fact_loan_applications[application_date]`
* **Borrower Type**: `dim_borrower_profiles[borrower_type]`
* **Risk Category**: `dim_risk_assessment[risk_category]`
* **Location**: `dim_borrower_profiles[location]`
* **Employment Type**: `dim_borrower_profiles[employment_type]`

## 5. Publish and Share
Once complete, save your `.pbix` file, publish it to the Power BI Service, and share it with the Lending Operations team.
