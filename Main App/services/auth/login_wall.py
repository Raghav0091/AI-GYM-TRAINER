import streamlit as st
from services.persistence.exercise_repository import authenticate_user, register_user


def _start_user_session(user):
    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    st.rerun()


def _render_auth_header():
    st.markdown(
        """
        <div class="auth-page">
            <div class="auth-bg-wordmark">AI FITNESS COACH</div>
            <div class="auth-card">
                <div class="auth-flame">🔥</div>
                <h1>AI Fitness Coach</h1>
                <p>Train Smarter. Move Better.</p>
        """,
        unsafe_allow_html=True,
    )


def _render_auth_footer():
    st.markdown(
        """
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True

    _render_auth_header()

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username", key="login_username")
            password = st.text_input("Password", placeholder="Enter your password", type="password", key="login_password")
            submit_button = st.form_submit_button("Login", width="stretch")

        if submit_button:
            if not username.strip() or not password:
                st.error("Username and password are required.")
            else:
                user = authenticate_user(username.strip(), password)

                if user is None:
                    st.error("Invalid username or password.")
                else:
                    _start_user_session(user)

    with register_tab:
        with st.form("register_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Choose a username", key="register_username")
            password = st.text_input("Password", placeholder="Create a password", type="password", key="register_password")
            confirm_password = st.text_input(
                "Confirm Password",
                placeholder="Re-enter your password",
                type="password",
                key="register_confirm_password",
            )
            submit_button = st.form_submit_button("Register", width="stretch")

        if submit_button:
            clean_username = username.strip()

            if not clean_username or not password or not confirm_password:
                st.error("All fields are required.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 4:
                st.error("Password must be at least 4 characters.")
            else:
                user = register_user(clean_username, password)

                if user is None:
                    st.error("That username is already registered. Please log in instead.")
                else:
                    st.success("Account created. Starting your session...")
                    _start_user_session(user)

    _render_auth_footer()

    return False
