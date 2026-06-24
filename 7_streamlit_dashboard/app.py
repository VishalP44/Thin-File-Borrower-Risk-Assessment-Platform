import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Thin File Lending Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #6a3093, #a044ff);
        border: 1px solid #8a4fd6;
        border-radius: 10px;
        padding: 14px 16px 8px 16px;
    }
    [data-testid="stMetricLabel"] { font-weight: 600; color: #ffffff !important; opacity: 0.95; }
    [data-testid="stMetricValue"] { font-size: 1.7rem; color: #ffffff !important; }
    [data-testid="stMetric"] * { color: #ffffff !important; }
    h1, h2, h3 { font-family: "Segoe UI", sans-serif; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    section[data-testid="stSidebar"] { border-right: 1px solid #2a3142; }
    </style>
    """,
    unsafe_allow_html=True,
)

DB_PATH = "../5_sql_database/lending_operations.db"
FALLBACK_DB_PATH = "5_sql_database/lending_operations.db"


def get_connection():
    path = DB_PATH if os.path.exists(DB_PATH) else FALLBACK_DB_PATH
    return sqlite3.connect(path)


@st.cache_data
def load_data(query, params=None):
    if not os.path.exists(DB_PATH) and not os.path.exists(FALLBACK_DB_PATH):
        st.error("Database not found. Please ensure the data pipeline has been run.")
        return pd.DataFrame()
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@st.cache_data
def load_filter_options():
    return {
        "borrower_type": load_data(
            "SELECT DISTINCT borrower_type FROM dim_borrower_profiles ORDER BY 1"
        )["borrower_type"].tolist(),
        "risk_category": ["Low Risk", "Medium Risk", "High Risk"],
        "employment_type": load_data(
            "SELECT DISTINCT employment_type FROM dim_borrower_profiles ORDER BY 1"
        )["employment_type"].tolist(),
        "location": load_data(
            "SELECT DISTINCT location FROM dim_borrower_profiles ORDER BY 1"
        )["location"].tolist(),
        "loan_status": load_data(
            "SELECT DISTINCT loan_status FROM fact_loan_applications ORDER BY 1"
        )["loan_status"].tolist(),
        "age_bounds": tuple(
            load_data("SELECT MIN(age) as lo, MAX(age) as hi FROM dim_borrower_profiles").iloc[0]
        ),
    }


def build_filters(selections):
    """Returns a SQL WHERE fragment (starting with AND) plus its params, for
    columns aliased as p (profiles), r (risk), a (applications)."""
    clauses = []
    params = []

    def add_in_clause(column, values, all_values):
        if values and len(values) < len(all_values):
            placeholders = ",".join(["?"] * len(values))
            clauses.append(f"{column} IN ({placeholders})")
            params.extend(values)

    add_in_clause("p.borrower_type", selections["borrower_type"], options["borrower_type"])
    add_in_clause("r.risk_category", selections["risk_category"], options["risk_category"])
    add_in_clause("p.employment_type", selections["employment_type"], options["employment_type"])
    add_in_clause("p.location", selections["location"], options["location"])
    add_in_clause("a.loan_status", selections["loan_status"], options["loan_status"])

    clauses.append("p.age BETWEEN ? AND ?")
    params.extend([selections["age_range"][0], selections["age_range"][1]])

    return (" AND " + " AND ".join(clauses)) if clauses else "", params


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
options = load_filter_options()

st.sidebar.header("🔎 Filters")

sel_borrower_type = st.sidebar.multiselect(
    "Borrower Type", options["borrower_type"], default=options["borrower_type"]
)
sel_risk_category = st.sidebar.multiselect(
    "Risk Category", options["risk_category"], default=options["risk_category"]
)
sel_employment_type = st.sidebar.multiselect(
    "Employment Type", options["employment_type"], default=options["employment_type"]
)
sel_location = st.sidebar.multiselect(
    "Location", options["location"], default=options["location"]
)
sel_loan_status = st.sidebar.multiselect(
    "Loan Status", options["loan_status"], default=options["loan_status"]
)
sel_age_range = st.sidebar.slider(
    "Age Range",
    min_value=int(options["age_bounds"][0]),
    max_value=int(options["age_bounds"][1]),
    value=(int(options["age_bounds"][0]), int(options["age_bounds"][1])),
)

if st.sidebar.button("Reset Filters"):
    st.cache_data.clear()
    st.rerun()

selections = {
    "borrower_type": sel_borrower_type,
    "risk_category": sel_risk_category,
    "employment_type": sel_employment_type,
    "location": sel_location,
    "loan_status": sel_loan_status,
    "age_range": sel_age_range,
}
filter_sql, filter_params = build_filters(selections)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("💳 Thin File Borrower Risk Assessment Platform")
st.markdown("#### Operations Dashboard")

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
metrics_query = f"""
SELECT
    COUNT(DISTINCT p.borrower_id) as total_borrowers,
    SUM(CASE WHEN p.borrower_type = 'Thin File' THEN 1 ELSE 0 END) as thin_file_count,
    SUM(CASE WHEN p.borrower_type = 'Traditional' THEN 1 ELSE 0 END) as traditional_count,
    CAST(SUM(CASE WHEN a.loan_status = 'Approved' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(a.application_id) * 100 as approval_rate,
    CAST(SUM(l.is_default) AS FLOAT) / SUM(CASE WHEN a.loan_status = 'Approved' THEN 1 ELSE 0 END) * 100 as default_rate,
    AVG(r.risk_probability) as avg_risk_score,
    AVG(a.approved_loan_amount) as avg_approved_amount
FROM dim_borrower_profiles p
LEFT JOIN fact_loan_applications a ON p.borrower_id = a.borrower_id
LEFT JOIN dim_loan_performance l ON p.borrower_id = l.borrower_id
LEFT JOIN dim_risk_assessment r ON p.borrower_id = r.borrower_id
WHERE 1=1 {filter_sql}
"""
metrics_df = load_data(metrics_query, filter_params)

if not metrics_df.empty and metrics_df.iloc[0]["total_borrowers"]:
    m = metrics_df.iloc[0]
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Borrowers", f"{int(m['total_borrowers']):,}")
    col2.metric("Thin File / Traditional", f"{int(m['thin_file_count']):,} / {int(m['traditional_count']):,}")
    col3.metric("Approval Rate", f"{m['approval_rate']:.1f}%" if pd.notna(m['approval_rate']) else "—")
    col4.metric("Default Rate", f"{m['default_rate']:.1f}%" if pd.notna(m['default_rate']) else "—")
    col5.metric("Avg Risk Score", f"{m['avg_risk_score']:.3f}" if pd.notna(m['avg_risk_score']) else "—")
    col6.metric("Avg Approved Loan", f"${m['avg_approved_amount']:,.0f}" if pd.notna(m['avg_approved_amount']) else "—")
else:
    st.warning("No borrowers match the selected filters. Try widening your filter selection.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------------
# Charts row 1
# ---------------------------------------------------------------------------
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Borrower Distribution")
    dist_query = f"""
    SELECT p.borrower_type, COUNT(DISTINCT p.borrower_id) as count
    FROM dim_borrower_profiles p
    LEFT JOIN fact_loan_applications a ON p.borrower_id = a.borrower_id
    LEFT JOIN dim_risk_assessment r ON p.borrower_id = r.borrower_id
    WHERE 1=1 {filter_sql}
    GROUP BY p.borrower_type
    """
    dist_df = load_data(dist_query, filter_params)
    fig1 = px.pie(dist_df, names='borrower_type', values='count', hole=0.45,
                  color_discrete_sequence=px.colors.sequential.Teal)
    fig1.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig1, use_container_width=True)

with col_chart2:
    st.subheader("Default Rate by Borrower Type")
    def_type_query = f"""
    SELECT
        p.borrower_type,
        CAST(SUM(l.is_default) AS FLOAT) / COUNT(p.borrower_id) * 100 as default_rate
    FROM dim_loan_performance l
    JOIN dim_borrower_profiles p ON l.borrower_id = p.borrower_id
    JOIN fact_loan_applications a ON l.borrower_id = a.borrower_id
    JOIN dim_risk_assessment r ON l.borrower_id = r.borrower_id
    WHERE a.loan_status = 'Approved' {filter_sql}
    GROUP BY p.borrower_type
    """
    def_type_df = load_data(def_type_query, filter_params)
    fig2 = px.bar(def_type_df, x='borrower_type', y='default_rate', text='default_rate',
                  color='borrower_type', color_discrete_sequence=px.colors.qualitative.Set2)
    fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig2.update_layout(margin=dict(t=10, b=10), showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------------------------
# Charts row 2
# ---------------------------------------------------------------------------
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.subheader("Default Rate by Risk Category & Borrower Type")
    heatmap_query = f"""
    SELECT
        r.risk_category,
        p.borrower_type,
        CAST(SUM(l.is_default) AS FLOAT) / COUNT(p.borrower_id) * 100 as default_rate
    FROM dim_loan_performance l
    JOIN dim_risk_assessment r ON l.borrower_id = r.borrower_id
    JOIN dim_borrower_profiles p ON l.borrower_id = p.borrower_id
    JOIN fact_loan_applications a ON l.borrower_id = a.borrower_id
    WHERE a.loan_status = 'Approved' {filter_sql}
    GROUP BY r.risk_category, p.borrower_type
    """
    heatmap_df = load_data(heatmap_query, filter_params)
    if not heatmap_df.empty:
        pivot_df = heatmap_df.pivot(index="risk_category", columns="borrower_type", values="default_rate")
        pivot_df = pivot_df.reindex(["Low Risk", "Medium Risk", "High Risk"])
        fig3 = px.imshow(pivot_df, text_auto=".1f", color_continuous_scale="RdYlGn_r", aspect="auto",
                         labels=dict(color="Default Rate (%)"))
        fig3.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No approved loans match the current filters.")

with col_chart4:
    st.subheader("Approval Rate by Employment Type")
    approval_emp_query = f"""
    SELECT
        p.employment_type,
        CAST(SUM(CASE WHEN a.loan_status = 'Approved' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as approval_rate
    FROM dim_borrower_profiles p
    JOIN fact_loan_applications a ON p.borrower_id = a.borrower_id
    LEFT JOIN dim_risk_assessment r ON p.borrower_id = r.borrower_id
    WHERE 1=1 {filter_sql}
    GROUP BY p.employment_type
    ORDER BY approval_rate DESC
    """
    approval_emp_df = load_data(approval_emp_query, filter_params)
    fig4 = px.bar(approval_emp_df, x='approval_rate', y='employment_type', orientation='h',
                  text='approval_rate', color='employment_type',
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig4.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig4.update_layout(margin=dict(t=10, b=10), showlegend=False, yaxis_title="")
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Deep Dive Tables
# ---------------------------------------------------------------------------
st.subheader("Deep Dive Analysis")

tab1, tab2 = st.tabs(["Top 50 Approved Thin File Borrowers", "Early Defaults (First 6 Months)"])

with tab1:
    top_approved_query = f"""
    SELECT
        p.borrower_id,
        p.employment_type,
        p.location,
        r.risk_probability,
        r.risk_category,
        a.approved_loan_amount
    FROM dim_borrower_profiles p
    JOIN dim_risk_assessment r ON p.borrower_id = r.borrower_id
    JOIN fact_loan_applications a ON p.borrower_id = a.borrower_id
    WHERE p.borrower_type = 'Thin File' AND a.loan_status = 'Approved' {filter_sql}
    ORDER BY r.risk_probability ASC
    LIMIT 50
    """
    top_approved_df = load_data(top_approved_query, filter_params)
    st.dataframe(top_approved_df, use_container_width=True)

with tab2:
    early_defaults_query = f"""
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
    WHERE l.is_default = 1 AND l.months_to_default <= 6 {filter_sql}
    ORDER BY l.months_to_default ASC
    LIMIT 50
    """
    early_defaults_df = load_data(early_defaults_query, filter_params)
    st.dataframe(early_defaults_df, use_container_width=True)
