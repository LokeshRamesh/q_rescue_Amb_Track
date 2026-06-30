import hmac

import streamlit as st


USERS = {
    "admin": {
        "password": "QRescue123",
        "name": "Administrator",
        "role": "Admin",
    },
    "operator": {
        "password": "Operator123",
        "name": "Control Room Operator",
        "role": "Operator",
    },
    "responder": {
        "password": "Responder123",
        "name": "Emergency Responder",
        "role": "Responder",
    },
}


def is_logged_in():
    return bool(st.session_state.get("authenticated", False))


def validate_login(username, password):
    account = USERS.get(username.strip().lower())
    if not account:
        return False
    return hmac.compare_digest(password, account["password"])


def log_in(username):
    username = username.strip().lower()
    account = USERS[username]
    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["display_name"] = account["name"]
    st.session_state["role"] = account["role"]


def log_out():
    st.session_state["authenticated"] = False
    st.session_state.pop("username", None)
    st.session_state.pop("display_name", None)
    st.session_state.pop("role", None)
    st.session_state.pop("simulation_results", None)


def render_sidebar_nav():
    """Render consistent user info and logout across all pages."""
    st.sidebar.markdown(f"**{st.session_state.get('display_name', 'User')}**")
    if st.sidebar.button("Log out", use_container_width=True):
        log_out()
        st.switch_page("Home.py")


def require_login():
    if not is_logged_in():
        st.warning("Please log in before opening this page.")
        st.page_link("Home.py", label="Go to Login")
        st.stop()

    render_sidebar_nav()
