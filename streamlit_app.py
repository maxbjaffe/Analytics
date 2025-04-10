import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pptx import Presentation
from pptx.util import Inches

st.set_page_config(page_title="Ad Insights Auto-Dashboard", layout="wide")
st.title("📊 Advertising Intelligence Dashboard")

def safe_format_number(val, as_int=True):
    try:
        return f"{int(val):,}" if as_int else f"{float(val):,.2f}"
    except (ValueError, TypeError):
        return "N/A"

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

uploaded_file = st.file_uploader("Upload your report CSV or Excel", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, sheet_name="TV Quality Index Report_data")  # 🔧 Correct sheet
        else:
            df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df.dropna(how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    report_type = detect_report_type(df.columns)
    st.subheader(f"📁 Detected Report Type: `{report_type}`")
    st.dataframe(df)

    if report_type == "TVQI Report":
        st.subheader("📈 Key Metrics")

        df['advertiser_cost_(adv_currency)'] = pd.to_numeric(df['advertiser_cost_(adv_currency)'], errors='coerce')

        impressions = df['tv_quality_index_measured_impressions'].sum()
        completed_views = df['player_completed_views'].sum()
        player_starts = df['player_starts'].sum()
        viewable_impressions = df['sampled_viewed_impressions'].sum()
        cost = df['advertiser_cost_(adv_currency)'].sum()
        tvqi_raw = df['tv_quality_index_raw'].sum()
        tvqi_score = (tvqi_raw / impressions) if impressions > 0 else None
        cpm = (cost / impressions * 1000) if impressions > 0 else None
        completion_rate = (completed_views / player_starts) if player_starts > 0 else None
        ecpcv = (cost / completed_views) if completed_views > 0 else None
        viewable_cpm = (cost / viewable_impressions * 1000) if viewable_impressions > 0 else None
        in_view_rate = (viewable_impressions / impressions) if impressions > 0 else None

        col1, col2, col3 = st.columns(3)
        col1.metric("TVQI Measured Impressions", safe_format_number(impressions))
        col2.metric("Completed Views", safe_format_number(completed_views))
        col3.metric("Total Cost", f"${safe_format_number(cost, as_int=False)}")

        col4, col5, col6 = st.columns(3)
        col4.metric("CPM", f"${safe_format_number(cpm, as_int=False)}")
        col5.metric("Completion Rate", f"{completion_rate:.2%}" if completion_rate else "N/A")
        col6.metric("eCPCV", f"${safe_format_number(ecpcv, as_int=False)}")

        col7, col8, col9 = st.columns(3)
        col7.metric("Viewable CPM", f"${safe_format_number(viewable_cpm, as_int=False)}")
        col8.metric("In-View Rate", f"{in_view_rate:.2%}" if in_view_rate else "N/A")
        col9.metric("TVQI Score", f"{tvqi_score:.4f}" if tvqi_score else "N/A")

        st.subheader("📊 Top Supply Vendors: Advertiser Cost + TVQI Score")

        if 'supply_vendor' in df.columns:
            grouped = df.groupby('supply_vendor').agg({
                'advertiser_cost_(adv_currency)': 'sum',
                'tv_quality_index_raw': 'sum',
                'tv_quality_index_measured_impressions': 'sum'
            }).reset_index()

            grouped['tvqi_score'] = grouped['tv_quality_index_raw'] / grouped['tv_quality_index_measured_impressions']
            grouped = grouped[grouped['tvqi_score'].notnull()]
            grouped = grouped.sort_values(by='advertiser_cost_(adv_currency)', ascending=False)

            all_vendors = grouped['supply_vendor'].tolist()
            default_top_10 = all_vendors[:10]
            selected_vendors = st.multiselect("Select supply vendors to show", all_vendors, default=default_top_10)

            filtered = grouped[grouped['supply_vendor'].isin(selected_vendors)]

            fig, ax1 = plt.subplots(figsize=(10, 5))
            ax2 = ax1.twinx()

            bars = ax1.bar(filtered['supply_vendor'], filtered['advertiser_cost_(adv_currency)'], color='lightgreen', label='Advertiser Cost')
            ax2.plot(filtered['supply_vendor'], filtered['tvqi_score'], color='blue', marker='o', label='TVQI Score')

            ax1.set_ylabel('Advertiser Cost ($)', color='green')
            ax2.set_ylabel('TVQI Score', color='blue')
            ax1.set_title('Advertiser Cost + TVQI Score by Supply Vendor')
            ax1.tick_params(axis='x', rotation=45)
            ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
            fig.tight_layout()
            st.pyplot(fig)

            st.subheader("📤 Export Report")
            col_pdf, col_ppt = st.columns(2)

            with col_pdf:
                if st.button("📄 Export Chart to PDF"):
                    pdf_buf = io.BytesIO()
                    fig.savefig(pdf_buf, format='pdf')
                    st.download_button("Download PDF", pdf_buf.getvalue(), file_name="tvqi_chart.pdf", mime="application/pdf")

            with col_ppt:
                if st.button("📊 Export Chart to PowerPoint"):
                    ppt = Presentation()
                    slide = ppt.slides.add_slide(ppt.slide_layouts[5])
                    title = slide.shapes.title
                    title.text = "TVQI Report Chart"

                    image_stream = io.BytesIO()
                    fig.savefig(image_stream, format='png')
                    image_stream.seek(0)

                    pic = slide.shapes.add_picture(image_stream, Inches(1), Inches(1.5), Inches(8), Inches(4.5))
                    ppt_bytes = io.BytesIO()
                    ppt.save(ppt_bytes)
                    st.download_button("Download PPT", ppt_bytes.getvalue(), file_name="tvqi_chart.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

        else:
            st.warning("⚠️ Supply Vendor data is missing.")

else:
    st.info("👈 Please upload a CSV or Excel file to get started.")
