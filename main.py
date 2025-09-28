"""
Main application file for Caffe Dehh
Entry point that handles routing and session management
"""

import streamlit as st
from config import APP_TITLE, BRAND
from database import init_db
from auth import page_login, show_register
from user_dashboard import show_user_dashboard, page_review
from admin_dashboard import show_admin_dashboard, page_admin_edit_menu

# Initialize database
init_db()

# Session state initialization
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'cart' not in st.session_state:
    st.session_state['cart'] = {}
if 'promo_applied' not in st.session_state:
    st.session_state['promo_applied'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None

# Page configuration
st.set_page_config(page_title=f"{APP_TITLE} - {BRAND}", layout='wide')

# Top bar
st.markdown(f"# {BRAND} — {APP_TITLE}")

# Navigation helper
def go(page: str):
    st.session_state['page'] = page

# Page routing
PAGE_MAP = {
    'login': page_login,
    'register': show_register,
    'user_dashboard': show_user_dashboard,
    'admin_dashboard': show_admin_dashboard,
    'admin_edit_menu': page_admin_edit_menu,
    'review': page_review,
}

# Router logic
if st.session_state['logged_in']:
    if st.session_state['role'] == "admin":
        if st.session_state['page'] not in ['admin_dashboard', 'admin_edit_menu']:
            st.session_state['page'] = 'admin_dashboard'
    elif st.session_state['role'] == "user":
        if st.session_state['page'] not in ['user_dashboard', 'review']:
            st.session_state['page'] = 'user_dashboard'
    else:
        st.error("Peran pengguna tidak dikenal. Silakan hubungi admin.")
        st.session_state['logged_in'] = False
        st.session_state['page'] = 'login'
        st.rerun()
elif st.session_state['page'] not in ['login', 'register']:
    st.session_state['page'] = 'login'

# Render current page
page = st.session_state['page']
if page in PAGE_MAP:
    PAGE_MAP[page]()
else:
    st.error("Unknown page")

# Footer
st.markdown("---")
st.caption("Built with Streamlit • Caffe Dehh")