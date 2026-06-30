import streamlit as st

from auth import (
    is_logged_in,
    log_in,
    render_sidebar_nav,
    validate_login,
)
from ui_theme import apply_global_style


st.set_page_config(
    page_title="Q-Rescue AI",
    page_icon=":ambulance:",
    layout="wide",
)

apply_global_style()

st.markdown(
    """
    <style>
        .login-title {
            text-align: center;
            margin: 3.5rem auto 1.5rem auto;
        }

        .login-title-mark,
        .home-title-mark {
            width: 76px;
            height: 76px;
            margin: 0 auto 1rem auto;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            background: #ef232a;
            color: #ffffff;
            font-size: 1.35rem;
            font-weight: 950;
            box-shadow: 0 18px 38px rgba(239, 35, 42, 0.38);
        }

        .login-title h1,
        .home-title h1 {
            color: #ffffff !important;
            font-size: 3.4rem;
            line-height: 1;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 0;
        }

        .login-title p {
            color: #d7d4dc !important;
            margin-top: 0.8rem;
            font-weight: 700;
        }

        .home-title {
            min-height: 70vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .home-title h1 {
            font-size: 4rem;
            text-shadow: 0 8px 32px rgba(0, 0, 0, 0.55);
        }

        .home-red-line {
            width: 150px;
            height: 7px;
            margin-top: 1.3rem;
            border-radius: 999px;
            background: #ef232a;
            box-shadow: 0 10px 24px rgba(239, 35, 42, 0.35);
        }

        @media (max-width: 700px) {
            .login-title h1,
            .home-title h1 {
                font-size: 2.35rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if not is_logged_in():
    st.markdown(
        """
        <div class="login-title">
            <div class="login-title-mark">QR</div>
            <h1>Q-Rescue AI</h1>
            <p>Sheffield Emergency Response Control Centre</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, login_col, right = st.columns([1.2, 1, 1.2])
    with login_col:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Log In", use_container_width=True)

        if submitted:
            if validate_login(username, password):
                log_in(username)
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

render_sidebar_nav()

st.markdown(
    """
    <div class="home-title">
        <div class="home-title-mark">QR</div>
        <h1>Q-Rescue Sheffield Control Centre</h1>
        <div class="home-red-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)
