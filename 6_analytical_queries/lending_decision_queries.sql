-- 1. What is the approval rate for thin file borrowers vs traditional borrowers?
SELECT 
    p.borrower_type,
    COUNT(a.application_id) as total_applications,
    SUM(CASE WHEN a.loan_status = 'Approved' THEN 1 ELSE 0 END) as approved_applications,
    ROUND(CAST(SUM(CASE WHEN a.loan_status = 'Approved' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(a.application_id) * 100, 2) as approval_rate_pct
FROM fact_loan_applications a
JOIN dim_borrower_profiles p ON a.borrower_id = p.borrower_id
GROUP BY p.borrower_type;

-- 2. What is the default rate by borrower risk category?
SELECT 
    r.risk_category,
    COUNT(p.borrower_id) as total_loans,
    SUM(l.is_default) as defaulted_loans,
    ROUND(CAST(SUM(l.is_default) AS FLOAT) / COUNT(p.borrower_id) * 100, 2) as default_rate_pct
FROM dim_loan_performance l
JOIN dim_risk_assessment r ON l.borrower_id = r.borrower_id
JOIN dim_borrower_profiles p ON l.borrower_id = p.borrower_id
JOIN fact_loan_applications a ON l.borrower_id = a.borrower_id
WHERE a.loan_status = 'Approved'
GROUP BY r.risk_category
ORDER BY default_rate_pct ASC;

-- 3. Which alternative signals have the strongest correlation with default for Thin Files?
-- We can look at the average signals for defaulted vs non-defaulted thin files
SELECT 
    l.is_default,
    COUNT(*) as count,
    ROUND(AVG(ad.utility_on_time_pct), 2) as avg_utility_on_time_pct,
    ROUND(AVG(ad.rent_avg_days_late), 2) as avg_rent_days_late,
    ROUND(AVG(ad.avg_bank_balance), 2) as avg_bank_balance,
    ROUND(AVG(ad.overdraft_events), 2) as avg_overdraft_events
FROM dim_loan_performance l
JOIN dim_borrower_profiles p ON l.borrower_id = p.borrower_id
JOIN dim_alternative_data ad ON l.borrower_id = ad.borrower_id
WHERE p.borrower_type = 'Thin File'
GROUP BY l.is_default;

-- 4. For approved loans, what is the loan amount distribution by borrower type?
SELECT 
    p.borrower_type,
    COUNT(*) as num_approved_loans,
    ROUND(AVG(a.approved_loan_amount), 2) as avg_loan_amount,
    ROUND(MIN(a.approved_loan_amount), 2) as min_loan_amount,
    ROUND(MAX(a.approved_loan_amount), 2) as max_loan_amount
FROM fact_loan_applications a
JOIN dim_borrower_profiles p ON a.borrower_id = p.borrower_id
WHERE a.loan_status = 'Approved'
GROUP BY p.borrower_type;

-- 5. What is the default rate by loan amount range?
WITH LoanBuckets AS (
    SELECT 
        l.is_default,
        CASE 
            WHEN a.approved_loan_amount < 5000 THEN 'Under 5k'
            WHEN a.approved_loan_amount >= 5000 AND a.approved_loan_amount < 15000 THEN '5k - 15k'
            WHEN a.approved_loan_amount >= 15000 AND a.approved_loan_amount < 30000 THEN '15k - 30k'
            ELSE '30k+' 
        END as loan_bucket
    FROM fact_loan_applications a
    JOIN dim_loan_performance l ON a.borrower_id = l.borrower_id
    WHERE a.loan_status = 'Approved'
)
SELECT 
    loan_bucket,
    COUNT(*) as total_loans,
    SUM(is_default) as defaulted_loans,
    ROUND(CAST(SUM(is_default) AS FLOAT) / COUNT(*) * 100, 2) as default_rate_pct
FROM LoanBuckets
GROUP BY loan_bucket
ORDER BY default_rate_pct;

-- 6. How many thin file borrowers could be approved if we accepted medium risk?
-- Assuming currently only 'Low Risk' is approved, what is the delta?
SELECT 
    'Medium Risk Expansion' as scenario,
    COUNT(CASE WHEN r.risk_category = 'Medium Risk' THEN 1 END) as new_approvals_possible,
    ROUND(CAST(COUNT(CASE WHEN r.risk_category = 'Medium Risk' THEN 1 END) AS FLOAT) / COUNT(*) * 100, 2) as pct_volume_increase
FROM dim_risk_assessment r
JOIN dim_borrower_profiles p ON r.borrower_id = p.borrower_id
WHERE p.borrower_type = 'Thin File';

-- 7. What is the average risk score by age group, location, employment type?
SELECT 
    p.employment_type,
    p.location,
    CASE 
        WHEN p.age < 25 THEN 'Under 25'
        WHEN p.age BETWEEN 25 AND 40 THEN '25 - 40'
        ELSE 'Over 40' 
    END as age_group,
    ROUND(AVG(r.risk_probability), 4) as avg_risk_probability
FROM dim_borrower_profiles p
JOIN dim_risk_assessment r ON p.borrower_id = r.borrower_id
GROUP BY p.employment_type, p.location, age_group
ORDER BY avg_risk_probability DESC
LIMIT 10;

-- 8. Which borrowers defaulted within the first 6 months? (Early Defaults)
SELECT 
    p.borrower_id,
    p.borrower_type,
    r.risk_category,
    a.approved_loan_amount,
    l.months_to_default
FROM dim_loan_performance l
JOIN dim_borrower_profiles p ON l.borrower_id = p.borrower_id
JOIN dim_risk_assessment r ON l.borrower_id = r.borrower_id
JOIN fact_loan_applications a ON l.borrower_id = a.borrower_id
WHERE l.is_default = 1 AND l.months_to_default <= 6
ORDER BY l.months_to_default ASC
LIMIT 10;
