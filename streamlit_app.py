import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Ad Insights Auto-Dashboard", layout="wide")
st.title("📊 Advertising Intelligence Dashboard")

# Helper function to safely format numbers
def safe_format_number(val, as_int=True):
    try:
        return f"{int(val):,}" if as_int else f"{float(val):,.2f}"
    except (ValueError, TypeError):
        return "N/A"

# Upload CSV
uploaded_file = st.file_uploader("Upload your report CSV", type=["csv"])

# Function to auto-detect report type based on columns
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
        df = pd.read_csv(uploaded_file)
    except pd.errors.EmptyDataError:
        st.error("❌ The uploaded file is empty or unreadable. Please upload a valid CSV file.")
        st.stop()

    # Clean columns
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df.dropna(how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    # Detect report type
    report_type = detect_report_type(df.columns)
    st.subheader(f"📁 Detected Report Type: `{report_type}`")
    st.dataframe(df)

    st.subheader("📈 Key Insights")

    if report_type == "TVQI Report":
        impressions = df['impressions'].sum() if 'impressions' in df.columns else 0
        cost = df['advertiser_cost_(adv_currency)'].sum() if 'advertiser_cost_(adv_currency)' in df.columns else 0
        completed_views = df['player_completed_views'].sum() if 'player_completed_views' in df.columns else 0

        st.metric("Impressions", safe_format_number(impressions))
        st.metric("Completed Views", safe_format_number(completed_views))
        st.metric("Total Cost", f"${safe_format_number(cost, as_int=False)}")

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
    st.info("👈 Please upload a CSV file to get started.")
