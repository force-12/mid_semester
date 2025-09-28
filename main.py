"""
File aplikasi utama untuk Caffe Dehh
Titik masuk yang menangani routing dan manajemen sesi
"""

import streamlit as st
from config import APP_TITLE, BRAND
from database import init_db  # Impor ini sudah benar
# Baris yang menyebabkan error di bawah ini akan dihapus
from auth import page_login, page_register, page_forgot_password
from user_dashboard import show_user_dashboard, page_review
from admin_dashboard import (
    show_admin_dashboard, 
    page_admin_edit_menu, 
    page_admin_add_menu, 
    page_admin_add_promo
)

# Inisialisasi database
init_db()

# Inisialisasi session state
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

# Konfigurasi halaman
st.set_page_config(page_title=f"{APP_TITLE} - {BRAND}", layout='wide')

# Bar atas
st.markdown(f"# {BRAND} — {APP_TITLE}")

# Pemetaan Halaman (Routing)
PAGE_MAP = {
    'login': page_login,
    'register': page_register,
    'forgot_password': page_forgot_password,
    'user_dashboard': show_user_dashboard,
    'admin_dashboard': show_admin_dashboard,
    'admin_edit_menu': page_admin_edit_menu,
    'admin_add_menu': page_admin_add_menu,
    'admin_add_promo': page_admin_add_promo,
    'review': page_review,
}

# Logika Router
current_page = st.session_state.get('page', 'login')

# Render halaman saat ini
if current_page in PAGE_MAP:
    PAGE_MAP[current_page]()
else:
    st.error("Halaman tidak dikenal")
    st.session_state['page'] = 'login'
    st.rerun()

# Footer
st.markdown("---")
st.caption("Dibuat dengan Streamlit • Caffe Dehh")

