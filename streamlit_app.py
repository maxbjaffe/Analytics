import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Ad Insights Auto-Dashboard", layout="wide")
st.title("📊 Advertising Intelligence Dashboard")

# Helper to safely format numbers
def safe_format_number(val, as_int=True):
    try:
        return f"{int(val):,}" if as_int else f"{float(val):,.2f}"
    except (ValueError, TypeError):
        return "N/A"

# Upload CSV or Excel
uploaded_file = st.file_uploader("Upload your report CSV or Excel", type=["csv", "xlsx"])

# Auto-detect report type
def detect_report_type(columns):
    col_set = set(columns)
    if "player_completed_views" in col_set or "tv_quality_index_raw" in col_set:
        return "TVQI Report"
    elif "campaign_name" in col_set and "frequency_savings_impressions" in col_set:
        return "Campaign FC Savings"
    elif "advertiser_name" in col_set and "frequency_savings_impressions" in col_set:
        return "Advertiser FC Savings"
    elif "frequency_exposure" in col_set and "unique_households_percentage" in col_set:
        return "Frequency Distribution"
    else:
        return "Unknown Report"

if uploaded_file is not None:
    st.write("Uploaded file:", uploaded_file.name)

    try:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, sheet_name=0)
        else:
            df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"❌ Could not read file: {e}")
        st.stop()

    # Standardize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df.dropna(how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    # Detect report type
    report_type = detect_report_type(df.columns)
    st.subheader(f"📁 Detected Report Type: `{report_type}`")
    st.dataframe(df)

    st.subheader("📈 Key Insights")

    if report_type == "TVQI Report":
        impressions = df['tv_quality_index_measured_impressions'].sum() if 'tv_quality_index_measured_impressions' in df.columns else 0
        completed_views = df['player_completed_views'].sum() if 'player_completed_views' in df.columns else 0
        player_starts = df['player_starts'].sum() if 'player_starts' in df.columns else 0
        viewable_impressions = df['sampled_viewed_impressions'].sum() if 'sampled_viewed_impressions' in df.columns else 0

        # Clean and sum spend
        cost = pd.to_numeric(df['advertiser_cost_(adv_currency)'], errors='coerce').sum() if 'advertiser_cost_(adv_currency)' in df.columns else 0

        # TVQI Score Fix: raw / measured impressions
        tvqi_raw = df['tv_quality_index_raw'].sum() if 'tv_quality_index_raw' in df.columns else 0
        tvqi_score = (tvqi_raw / impressions) if impressions > 0 else None

        # Calculated Metrics
        cpm = (cost / impressions * 1000) if impressions > 0 else None
        completion_rate = (completed_views / player_starts) if player_starts > 0 else None
        ecpcv = (cost / completed_views) if completed_views > 0 else None
        viewable_cpm = (cost / viewable_impressions * 1000) if viewable_impressions > 0 else None
        in_view_rate = (viewable_impressions / impressions) if impressions > 0 else None

        # Show Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("TVQI Measured Impressions", safe_format_number(impressions))
        col2.metric("Completed Views", safe_format_number(completed_views))
        col3.metric("Total Cost", f"${safe_format_number(cost, as_int=False)}")

        col4, col5, col6 = st.columns(3)
        col4.metric("CPM", f"${safe_format_number(cpm, as_int=False)}")
        col5.metric("Completion Rate", f"{completion_rate:.2%}" if completion_rate is not None else "N/A")
        col6.metric("eCPCV", f"${safe_format_number(ecpcv, as_int=False)}")

        col7, col8, col9 = st.columns(3)
        col7.metric("Viewable CPM", f"${safe_format_number(viewable_cpm, as_int=False)}")
        col8.metric("In-View Rate", f"{in_view_rate:.2%}" if in_view_rate is not None else "N/A")
        col9.metric("TVQI Score", f"{tvqi_score:.4f}" if tvqi_score is not None else "N/A")

    elif report_type == "Campaign FC Savings":
        cost = df['advertiser_cost_(adv_currency)'].sum()
        impressions = df['impressions'].sum()
        savings_impressions = df['frequency_savings_impressions'].sum()
        savings_cost = df['frequency_savings_cost_(adv_currency)'].sum()

        st.metric("Impressions", safe_format_number(impressions))
        st.metric("Total Cost", f"${safe_format_number(cost, as_int=False)}")
        st.metric("Saved Impressions", safe_format_number(savings_impressions))
        st.metric("Saved Cost", f"${safe_format_number(savings_cost, as_int=False)}")

    elif report_type == "Advertiser FC Savings":
        impressions = df['impressions'].sum()
        cost = df['advertiser_cost_(adv_currency)'].sum()
        unique_hh = df['unique_households'].sum()
        frequency_hh = df['frequency_per_household'].mean()

        st.metric("Total Impressions", safe_format_number(impressions))
        st.metric("Total Cost", f"${safe_format_number(cost, as_int=False)}")
        st.metric("Unique Households", safe_format_number(unique_hh))
        st.metric("Avg Frequency/HH", f"{safe_format_number(frequency_hh, as_int=False)}")

    elif report_type == "Frequency Distribution":
        st.dataframe(df)

        if 'frequency_exposure' in df.columns and 'unique_households_percentage' in df.columns:
            st.subheader("📊 Frequency Exposure Distribution")
            fig, ax = plt.subplots()
            ax.bar(df['frequency_exposure'], df['unique_households_percentage'])
            ax.set_xlabel("Frequency Exposure")
            ax.set_ylabel("Unique Households %")
            ax.set_title("Frequency Distribution")
            st.pyplot(fig)

    else:
        st.warning("⚠️ Unknown report type. Displaying raw data only.")

else:
    st.info("👈 Please upload a CSV or Excel file to get started.")
