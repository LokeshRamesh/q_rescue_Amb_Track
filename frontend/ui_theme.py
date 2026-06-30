import base64
from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
BACKGROUND_IMAGE = ROOT_DIR / "assets" / "app_background.jpg"


def _background_data_uri():
    if not BACKGROUND_IMAGE.exists():
        return ""

    encoded = base64.b64encode(BACKGROUND_IMAGE.read_bytes()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def apply_global_style():
    background_uri = _background_data_uri()
    if background_uri:
        background_css = (
            "linear-gradient(135deg, rgba(10, 9, 13, 0.96), rgba(28, 25, 34, 0.94)), "
            f"url('{background_uri}')"
        )
    else:
        background_css = "linear-gradient(135deg, #0b090d, #211d27)"

    st.markdown(
        f"""
        <style>
            html,
            body,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"] {{
                background: #0b090d !important;
            }}

            .stApp {{
                background: {background_css};
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                color: #ffffff;
            }}

            [data-testid="stHeader"],
            .stAppHeader,
            [data-testid="stToolbar"] {{
                background: #121016 !important;
                color: #ffffff !important;
            }}

            [data-testid="stHeader"]::before {{
                background: #121016 !important;
            }}

            [data-testid="stSidebar"] {{
                background: rgba(18, 16, 22, 0.96);
                backdrop-filter: blur(14px);
                border-right: 1px solid rgba(239, 35, 42, 0.25);
            }}

            [data-testid="stSidebar"] * {{
                color: #f7f7fb !important;
            }}

            [data-testid="stSidebar"] [aria-current="page"],
            [data-testid="stSidebar"] a:hover {{
                background: #ef232a !important;
                color: #ffffff !important;
                border-radius: 4px;
            }}

            .block-container {{
                padding-top: 1.6rem;
                padding-bottom: 3rem;
                max-width: 1480px;
            }}

            div[data-testid="stForm"],
            div[data-testid="stMetric"],
            div[data-testid="stAlert"] {{
                background: rgba(34, 31, 39, 0.94);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 6px;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.35);
            }}

            div[data-testid="stDataFrame"],
            div[data-testid="stPlotlyChart"],
            iframe {{
                border-radius: 6px;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.28);
            }}

            [data-testid="stTable"] table {{
                width: 100% !important;
                table-layout: fixed !important;
                border-collapse: collapse !important;
            }}

            [data-testid="stTable"] th,
            [data-testid="stTable"] td {{
                text-align: left !important;
                vertical-align: middle !important;
                padding: 0.7rem 0.8rem !important;
                overflow-wrap: anywhere;
            }}

            .clear-table {{
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                background: #f5f5f7;
                color: #17151b;
                border-radius: 6px;
                overflow: hidden;
            }}

            .clear-table th,
            .clear-table td {{
                text-align: left;
                vertical-align: middle;
                padding: 0.78rem 0.9rem;
                border: 1px solid #d8d8dd;
                color: #17151b !important;
                overflow-wrap: anywhere;
            }}

            .clear-table th {{
                background: #ef232a;
                color: #ffffff !important;
                font-weight: 900;
            }}

            .stSelectbox div[data-baseweb="select"] > div,
            .stTextInput input,
            .stNumberInput input {{
                background: #f5f5f7 !important;
                color: #17151b !important;
                border-radius: 4px !important;
                border: 1px solid rgba(255, 255, 255, 0.18) !important;
            }}

            .stButton button,
            [data-testid="stFormSubmitButton"] button {{
                background: #ef232a !important;
                color: #ffffff !important;
                border: 0 !important;
                border-radius: 999px !important;
                font-weight: 900 !important;
                text-transform: uppercase;
                letter-spacing: 0;
                box-shadow: 0 14px 28px rgba(239, 35, 42, 0.30);
            }}

            .stButton button:hover,
            [data-testid="stFormSubmitButton"] button:hover {{
                background: #ffffff !important;
                color: #ef232a !important;
            }}

            .page-title {{
                display: flex;
                align-items: center;
                gap: 0.95rem;
                margin: 0.4rem 0 0.9rem 0;
                padding: 1.25rem 1.35rem;
                background: rgba(18, 16, 22, 0.96);
                border-bottom: 5px solid #ef232a;
                border-radius: 6px;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.35);
            }}

            h1, h2, h3,
            .stMarkdown h1,
            .stMarkdown h2,
            .stMarkdown h3,
            [data-testid="stWidgetLabel"] p,
            [data-testid="stWidgetLabel"] label,
            label {{
                color: #ffffff !important;
                font-weight: 900 !important;
                letter-spacing: 0;
            }}

            [data-testid="stWidgetLabel"] p::before,
            [data-testid="stWidgetLabel"] label::before {{
                content: "★";
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 1.25rem;
                height: 1.25rem;
                margin-right: 0.45rem;
                border-radius: 999px;
                background: #ef232a;
                color: #ffffff;
                font-size: 0.72rem;
                box-shadow: 0 8px 18px rgba(239, 35, 42, 0.28);
            }}

            .stMarkdown h2::before,
            .stMarkdown h3::before {{
                content: "★";
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 1.6rem;
                height: 1.6rem;
                margin-right: 0.55rem;
                border-radius: 999px;
                background: #ef232a;
                color: #ffffff;
                font-size: 0.8rem;
                vertical-align: middle;
                box-shadow: 0 10px 22px rgba(239, 35, 42, 0.26);
            }}

            .page-icon {{
                width: 58px;
                height: 58px;
                border-radius: 999px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: #ef232a;
                color: #ffffff;
                font-size: 1.45rem;
                font-weight: 900;
                box-shadow: 0 14px 30px rgba(239, 35, 42, 0.35);
            }}

            .page-heading {{
                font-size: 2.45rem;
                line-height: 1.1;
                font-weight: 950;
                color: #ffffff;
                margin: 0;
                letter-spacing: 0;
                text-transform: uppercase;
            }}

            .page-subtitle {{
                max-width: 920px;
                color: #ffffff;
                font-size: 1.02rem;
                line-height: 1.6;
                margin: 0 0 1.3rem 0;
                padding: 0.95rem 1.1rem;
                background: rgba(239, 35, 42, 0.92);
                border-radius: 4px;
                font-weight: 700;
            }}

            .stMarkdown,
            .stMarkdown p,
            p,
            span,
            [data-testid="stMetricLabel"],
            [data-testid="stMetricValue"] {{
                color: #f7f7fb !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(icon, title, subtitle=None):
    st.markdown(
        f"""
        <div class="page-title">
            <div class="page-icon">{icon}</div>
            <h1 class="page-heading">{title}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if subtitle:
        st.markdown(f'<p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)


def render_table(dataframe):
    table_html = dataframe.to_html(index=False, classes="clear-table", border=0)
    st.markdown(table_html, unsafe_allow_html=True)
