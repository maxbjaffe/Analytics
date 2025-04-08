import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("📊 Advertising Performance Dashboard")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file is not None:    
    # Load and clean the data
    try:
    df = pd.read_csv(uploaded_file)
except pd.errors.EmptyDataError:
    st.error("❌ The uploaded file is empty or unreadable. Please upload a valid CSV file.")
    st.stop()

    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Drop completely empty rows/columns
    df.dropna(how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    st.write("### Cleaned Data", df)

    # Generate automatic insights
    st.write("### 📊 Key Metrics")

    total_spend = df['spend'].sum() if 'spend' in df.columns else 0
    total_impressions = df['impressions'].sum() if 'impressions' in df.columns else 0
    total_clicks = df['clicks'].sum() if 'clicks' in df.columns else 0

    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

    st.metric("Total Spend", f"${total_spend:,.2f}")
    st.metric("Total Impressions", f"{int(total_impressions):,}")
    st.metric("Total Clicks", f"{int(total_clicks):,}")
    st.metric("CTR", f"{ctr:.2f}%")
    st.metric("CPC", f"${cpc:.2f}")

    df = pd.read_csv(uploaded_file)
    st.write("### Raw Data", df)

    st.write("### Spend vs Impressions")
    if 'Spend' in df.columns and 'Impressions' in df.columns:
        fig, ax = plt.subplots()
        ax.scatter(df['Spend'], df['Impressions'])
        ax.set_xlabel("Spend")
        ax.set_ylabel("Impressions")
        ax.set_title("Spend vs Impressions")
        st.pyplot(fig)
else:
    st.info("Please upload a CSV file to see the dashboard.")
