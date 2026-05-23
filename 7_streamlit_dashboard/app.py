import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Thin File Lending Dashboard", layout="wide")

# Connect to database
DB_PATH = "../5_sql_database/lending_operations.db"

@st.cache_data
def load_data(query):
    if not os.path.exists(DB_PATH):
        # Fallback if run from the root directory instead of the 7_streamlit_dashboard directory
        fallback_path = "5_sql_database/lending_operations.db"
        if os.path.exists(fallback_path):
            conn = sqlite3.connect(fallback_path)
        else:
            st.error("Database not found. Please ensure the data pipeline has been run.")
            return pd.DataFrame()
    else:
        conn = sqlite3.connect(DB_PATH)
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.title("Thin File Borrower Risk Assessment Platform")
st.markdown("### Operations Dashboard")

# 1. Load basic aggregated metrics
metrics_query = """
SELECT 
    COUNT(p.borrower_id) as total_borrowers,
    SUM(CASE WHEN p.borrower_type = 'Thin File' THEN 1 ELSE 0 END) as thin_file_count,
    SUM(CASE WHEN p.borrower_type = 'Traditional' THEN 1 ELSE 0 END) as traditional_count,
    CAST(SUM(CASE WHEN a.loan_status = 'Approved' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(a.application_id) * 100 as approval_rate,
    CAST(SUM(l.is_default) AS FLOAT) / SUM(CASE WHEN a.loan_status = 'Approved' THEN 1 ELSE 0 END) * 100 as default_rate,
    AVG(r.risk_probability) as avg_risk_score
FROM dim_borrower_profiles p
LEFT JOIN fact_loan_applications a ON p.borrower_id = a.borrower_id
LEFT JOIN dim_loan_performance l ON p.borrower_id = l.borrower_id
LEFT JOIN dim_risk_assessment r ON p.borrower_id = r.borrower_id
"""
metrics_df = load_data(metrics_query)

if not metrics_df.empty:
    m = metrics_df.iloc[0]
    
    # Top KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Borrowers", f"{int(m['total_borrowers']):,}")
    col2.metric("Thin File vs Traditional", f"{int(m['thin_file_count']):,} / {int(m['traditional_count']):,}")
    col3.metric("Overall Approval Rate", f"{m['approval_rate']:.1f}%")
    col4.metric("Overall Default Rate", f"{m['default_rate']:.1f}%")
    col5.metric("Avg Risk Score", f"{m['avg_risk_score']:.3f}")

st.divider()

# Charts row 1
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Borrower Distribution")
    dist_query = """
    SELECT borrower_type, COUNT(*) as count 
    FROM dim_borrower_profiles 
    GROUP BY borrower_type
    """
    dist_df = load_data(dist_query)
    fig1 = px.pie(dist_df, names='borrower_type', values='count', hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
    st.plotly_chart(fig1, use_container_width=True)

with col_chart2:
    st.subheader("Default Rate by Borrower Type")
    def_type_query = """
    SELECT 
        p.borrower_type,
        CAST(SUM(l.is_default) AS FLOAT) / COUNT(p.borrower_id) * 100 as default_rate
    FROM dim_loan_performance l
    JOIN dim_borrower_profiles p ON l.borrower_id = p.borrower_id
    JOIN fact_loan_applications a ON l.borrower_id = a.borrower_id
    WHERE a.loan_status = 'Approved'
    GROUP BY p.borrower_type
    """
    def_type_df = load_data(def_type_query)
    fig2 = px.bar(def_type_df, x='borrower_type', y='default_rate', text='default_rate', 
                  color='borrower_type', color_discrete_sequence=px.colors.qualitative.Set2)
    fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    st.plotly_chart(fig2, use_container_width=True)

# Charts row 2
st.subheader("Default Rate by Risk Category & Borrower Type")
heatmap_query = """
SELECT 
    r.risk_category,
    p.borrower_type,
    CAST(SUM(l.is_default) AS FLOAT) / COUNT(p.borrower_id) * 100 as default_rate
FROM dim_loan_performance l
JOIN dim_risk_assessment r ON l.borrower_id = r.borrower_id
JOIN dim_borrower_profiles p ON l.borrower_id = p.borrower_id
JOIN fact_loan_applications a ON l.borrower_id = a.borrower_id
WHERE a.loan_status = 'Approved'
GROUP BY r.risk_category, p.borrower_type
"""
heatmap_df = load_data(heatmap_query)
if not heatmap_df.empty:
    pivot_df = heatmap_df.pivot(index="risk_category", columns="borrower_type", values="default_rate")
    # Reorder risk categories
    pivot_df = pivot_df.reindex(["Low Risk", "Medium Risk", "High Risk"])
    
    fig3 = px.imshow(pivot_df, text_auto=".1f", color_continuous_scale="RdYlGn_r", aspect="auto",
                     labels=dict(color="Default Rate (%)"))
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# Deep Dive Tables
st.subheader("Deep Dive Analysis")

tab1, tab2 = st.tabs(["Top 50 Approved Thin File Borrowers", "Early Defaults (First 6 Months)"])

with tab1:
    top_approved_query = """
    SELECT 
        p.borrower_id, 
        p.employment_type,
        r.risk_probability, 
        r.risk_category,
        a.approved_loan_amount
    FROM dim_borrower_profiles p
    JOIN dim_risk_assessment r ON p.borrower_id = r.borrower_id
    JOIN fact_loan_applications a ON p.borrower_id = a.borrower_id
    WHERE p.borrower_type = 'Thin File' AND a.loan_status = 'Approved'
    ORDER BY r.risk_probability ASC
    LIMIT 50
    """
    top_approved_df = load_data(top_approved_query)
    st.dataframe(top_approved_df, use_container_width=True)

with tab2:
    early_defaults_query = """
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
    LIMIT 50
    """
    early_defaults_df = load_data(early_defaults_query)
    st.dataframe(early_defaults_df, use_container_width=True)
