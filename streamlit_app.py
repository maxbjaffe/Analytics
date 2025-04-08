import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Ad Performance Dashboard", layout="wide")
st.title("📊 Advertising Performance Dashboard")

# Upload CSV
uploaded_file = st.file_uploader("Upload your advertising CSV file", type=["csv"])

if uploaded_file is not None:
    st.write("Uploaded file:", uploaded_file.name)

    # Try to load the file safely
    try:
        df = pd.read_csv(uploaded_file)
    except pd.errors.EmptyDataError:
        st.error("❌ The uploaded file is empty or unreadable. Please upload a valid CSV file.")
        st.stop()

    # Clean column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Drop empty rows/columns
    df.dropna(how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    st.subheader("📋 Cleaned Data")
    st.dataframe(df)

    # Key metrics
    st.subheader("📈 Key Metrics Summary")
    total_spend = df['spend'].sum() if 'spend' in df.columns else 0
    total_impressions = df['impressions'].sum() if 'impressions' in df.columns else 0
    total_clicks = df['clicks'].sum() if 'clicks' in df.columns else 0

    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Spend", f"${total_spend:,.2f}")
    col2.metric("Total Impressions", f"{int(total_impressions):,}")
    col3.metric("Total Clicks", f"{int(total_clicks):,}")
    col4.metric("CTR", f"{ctr:.2f}%")
    col5.metric("CPC", f"${cpc:.2f}")

    # Chart: Spend vs Impressions
    if 'spend' in df.columns and 'impressions' in df.columns:
        st.subheader("📊 Spend vs Impressions")
        fig, ax = plt.subplots()
        ax.scatter(df['spend'], df['impressions'])
        ax.set_xlabel("Spend")
        ax.set_ylabel("Impressions")
        ax.set_title("Spend vs Impressions")
        st.pyplot(fig)
else:
    st.info("👈 Please upload a CSV file to get started.")
