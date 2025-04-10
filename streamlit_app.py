import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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

# Upload
uploaded_file = st.file_uploader("Upload your report CSV or Excel", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, sheet_name=0)
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

        impressions = df['tv_quality_index_measured_impressions'].sum() if 'tv_quality_index_measured_impressions' in df.columns else 0
        completed_views = df['player_completed_views'].sum() if 'player_completed_views' in df.columns else 0
        player_starts = df['player_starts'].sum() if 'player_starts' in df.columns else 0
        viewable_impressions = df['sampled_viewed_impressions'].sum() if 'sampled_viewed_impressions' in df.columns else 0
        cost = pd.to_numeric(df['advertiser_cost_(adv_currency)'], errors='coerce').sum() if 'advertiser_cost_(adv_currency)' in df.columns else 0

        tvqi_raw = df['tv_quality_index_raw'].sum() if 'tv_quality_index_raw' in df.columns else 0
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
        col5.metric("Completion Rate", f"{completion_rate:.2%}" if completion_rate is not None else "N/A")
        col6.metric("eCPCV", f"${safe_format_number(ecpcv, as_int=False)}")

        col7, col8, col9 = st.columns(3)
        col7.metric("Viewable CPM", f"${safe_format_number(viewable_cpm, as_int=False)}")
        col8.metric("In-View Rate", f"{in_view_rate:.2%}" if in_view_rate is not None else "N/A")
        col9.metric("TVQI Score", f"{tvqi_score:.4f}" if tvqi_score is not None else "N/A")

        # Charts
        st.subheader("📊 Breakdown by Supply Vendor")

        if 'supply_vendor' in df.columns:
            grouped = df.groupby('supply_vendor').agg({
                'advertiser_cost_(adv_currency)': 'sum',
                'tv_quality_index_raw': 'sum',
                'tv_quality_index_measured_impressions': 'sum'
            }).reset_index()
            grouped['tvqi_score'] = grouped['tv_quality_index_raw'] / grouped['tv_quality_index_measured_impressions']
            grouped.sort_values(by='advertiser_cost_(adv_currency)', ascending=False, inplace=True)

            # Chart 1
            fig1, ax1 = plt.subplots(figsize=(10, 4))
            ax1.barh(grouped['supply_vendor'], grouped['tvqi_score'], color='skyblue')
            ax1.set_title("TVQI Score by Supply Vendor")
            ax1.set_xlabel("TVQI Score")
            ax1.invert_yaxis()
            st.pyplot(fig1)

            # Chart 2
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            ax2.barh(grouped['supply_vendor'], grouped['advertiser_cost_(adv_currency)'], color='lightgreen')
            ax2.set_title("Advertiser Cost by Supply Vendor")
            ax2.set_xlabel("Total Cost ($)")
            ax2.invert_yaxis()
            st.pyplot(fig2)

            # Export buttons
            st.subheader("📤 Export Report")
            col_pdf, col_ppt = st.columns(2)

            with col_pdf:
                if st.button("📄 Export as PDF"):
                    buf = io.BytesIO()
                    c = canvas.Canvas(buf, pagesize=letter)
                    c.drawString(100, 750, f"TVQI Score: {tvqi_score:.4f}" if tvqi_score else "TVQI Score: N/A")
                    c.drawString(100, 730, f"Total Cost: ${cost:,.2f}")
                    c.drawString(100, 710, f"CPM: ${cpm:,.2f}" if cpm else "CPM: N/A")
                    c.drawString(100, 690, f"Completion Rate: {completion_rate:.2%}" if completion_rate else "N/A")
                    c.drawString(100, 670, f"eCPCV: ${ecpcv:,.2f}" if ecpcv else "N/A")
                    c.drawString(100, 650, f"Viewable CPM: ${viewable_cpm:,.2f}" if viewable_cpm else "N/A")
                    c.save()
                    st.download_button("Download PDF", buf.getvalue(), file_name="tvqi_report.pdf", mime="application/pdf")

            with col_ppt:
                if st.button("📊 Export as PowerPoint"):
                    ppt = Presentation()
                    slide = ppt.slides.add_slide(ppt.slide_layouts[5])
                    title = slide.shapes.title
                    title.text = "TVQI Report Summary"

                    textbox = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(4))
                    frame = textbox.text_frame
                    frame.text = f"TVQI Score: {tvqi_score:.4f}" if tvqi_score else "TVQI Score: N/A"
                    frame.add_paragraph().text = f"Total Cost: ${cost:,.2f}"
                    frame.add_paragraph().text = f"CPM: ${cpm:,.2f}" if cpm else "CPM: N/A"
                    frame.add_paragraph().text = f"Completion Rate: {completion_rate:.2%}" if completion_rate else "N/A"
                    frame.add_paragraph().text = f"eCPCV: ${ecpcv:,.2f}" if ecpcv else "N/A"
                    frame.add_paragraph().text = f"Viewable CPM: ${viewable_cpm:,.2f}" if viewable_cpm else "N/A"

                    ppt_bytes = io.BytesIO()
                    ppt.save(ppt_bytes)
                    st.download_button("Download PPT", ppt_bytes.getvalue(), file_name="tvqi_report.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

        else:
            st.warning("⚠️ Supply Vendor data is missing.")

else:
    st.info("👈 Please upload a CSV or Excel file to get started.")
