import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("📊 Advertising Performance Dashboard")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file is not None:
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
