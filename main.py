"""
File aplikasi utama untuk Caffe Dehh
Titik masuk yang menangani routing dan manajemen sesi
"""

import streamlit as st
from config import APP_TITLE, BRAND
from database import init_db
from auth import page_login, page_register, page_forgot_password
from user_dashboard import show_user_dashboard, page_review, page_user_profile
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

# Konfigurasi halaman dan estetika
st.set_page_config(
    page_title=f"{APP_TITLE} - {BRAND}", 
    layout='wide',
    initial_sidebar_state='collapsed' # Sidebar disembunyikan secara default
)

# URL Gambar Latar Belakang - Logo Caffe Dehh
BACKGROUND_IMAGE_URL = "https://i.imgur.com/TA35aIw.png"

# --- CSS Kustom ---
# Semua gaya CSS dikonsolidasikan di sini untuk kejelasan dan pemeliharaan yang lebih baik.
# Bug duplikasi dan penempatan CSS yang salah telah diperbaiki.
# PERBAIKAN: Menggunakan kurung kurawal ganda {{ }} untuk menghindari kesalahan parsing oleh linter Pylance.
CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Nunito:wght@400;600;700&display=swap');

    /* SOLUSI ULTIMATE: Isolasi total selectbox dari inheritance CSS */
    
    /* Reset inheritance untuk selectbox - jangan warisi style dari parent */
    div[data-testid="stSelectbox"] {{
        all: initial !important;
        display: block !important;
        font-family: var(--font-body) !important;
        margin-bottom: 1rem !important;
    }}
    
    /* Label selectbox */
    div[data-testid="stSelectbox"] label {{
        all: initial !important;
        display: block !important;
        font-family: var(--font-body) !important;
        font-weight: 600 !important;
        color: #000000 !important;
        margin-bottom: 0.5rem !important;
        font-size: 1rem !important;
    }}
    
    /* Container selectbox dengan background putih solid */
    div[data-testid="stSelectbox"] > div > div {{
        background-color: #FFFFFF !important;
        border: 1px solid #D3D3D3 !important;
        border-radius: 8px !important;
        padding: 0 !important;
    }}
    
    /* Base select element - PENTING: Reset semua inherited styles */
    div[data-testid="stSelectbox"] [data-baseweb="select"] {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        all: revert !important;
        font-family: var(--font-body) !important;
    }}
    
    /* CRITICAL: Text yang dipilih dan placeholder HARUS HITAM */
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
    div[data-testid="stSelectbox"] [data-baseweb="select"] span,
    div[data-testid="stSelectbox"] [data-baseweb="select"] div {{
        color: #000000 !important;
        background-color: #FFFFFF !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        opacity: 1 !important;
        text-shadow: none !important;
        font-family: var(--font-body) !important;
    }}
    
    /* Input di dalam selectbox */
    div[data-testid="stSelectbox"] input {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        background-color: #FFFFFF !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }}
    
    /* Dropdown menu - PUTIH dengan text HITAM */
    [role="listbox"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #D3D3D3 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        z-index: 9999 !important;
    }}
    
    /* Options dalam dropdown */
    [role="option"] {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        font-weight: 600 !important;
        padding: 10px 12px !important;
        font-size: 1rem !important;
        opacity: 1 !important;
        font-family: var(--font-body) !important;
    }}
    
    [role="option"]:hover {{
        background-color: #F5F5F5 !important;
        color: #000000 !important;
    }}
    
    /* Selected option */
    [role="option"][aria-selected="true"] {{
        background-color: #E8E8E8 !important;
        color: #000000 !important;
        font-weight: 700 !important;
    }}

    :root {{
        --primary-color: #A0522D; /* Sienna Brown */
        --primary-color-dark: #8B4513; /* Saddle Brown */
        --background-color: #FDFBF5; 
        --secondary-background-color: #FFFFFF; /* Diubah ke putih agar kontras */
        --text-color: #000000; /* Warna teks diubah menjadi hitam pekat */
        --font-header: 'Playfair Display', serif;
        --font-body: 'Nunito', sans-serif;
        --base-font-size: 16px; /* Ukuran font dasar yang lebih nyaman */
    }}

    /* 1. Atur Latar Belakang Utama dengan Gambar Logo */
    [data-testid="stAppViewContainer"] {{
        background: url("{BACKGROUND_IMAGE_URL}");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        background-repeat: no-repeat;
    }}
    
    /* 1a. Responsiveness untuk mobile */
    @media (max-width: 768px) {{
        [data-testid="stAppViewContainer"] {{
            background-size: contain;
            background-position: center top;
        }}
    }}
    
    /* 2. Konten utama dengan overlay semi-transparan */
    .main .block-container {{
        background-color: rgba(253, 251, 245, 0.95); /* Latar belakang lebih solid */
        border-radius: 15px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        /* backdrop-filter: blur(5px); */ /* DINONAKTIFKAN - mungkin menyebabkan masalah rendering */
        border: 1px solid rgba(255, 255, 255, 0.18);
    }}
    
    /* 3. Penyesuaian Ukuran Font Global */
    html, body, [class*="st-"] {{
        font-family: var(--font-body);
        font-size: var(--base-font-size);
        color: var(--text-color);
    }}

    /* 4. Judul Utama Aplikasi dengan Stroke Putih */
    h1 {{
        color: #000000; /* Warna teks diubah menjadi hitam */
        text-align: center;
        font-family: var(--font-header);
        font-size: 3rem; /* Sedikit diperbesar agar stroke terlihat bagus */
        letter-spacing: 2px;
        /* Trik text-shadow untuk membuat stroke putih */
        text-shadow: -1px -1px 0 #FFF, 1px -1px 0 #FFF, -1px 1px 0 #FFF, 1px 1px 0 #FFF;
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
    }}

    /* 5. Sub-judul di dalam konten */
    h2, h3, h4, h5, h6 {{
        color: var(--text-color);
        font-family: var(--font-header);
        font-weight: 700;
    }}
    h2 {{ font-size: 2rem; }}
    h3 {{ font-size: 1.75rem; }}

    /* 6. Tombol yang Lebih Besar dan Jelas */
    .stButton>button {{
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 12px 28px; /* Padding lebih besar */
        font-weight: 700;
        font-size: 1.1rem; /* Font lebih besar */
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .stButton>button:hover {{
        background-color: var(--primary-color-dark);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    
    /* 7. Input Form yang Lebih Modern */
    .stTextInput>div>div>input, .stSelectbox>div>div, .stNumberInput>div>div>input {{
        border-radius: 8px;
        border: 1px solid #D3D3D3;
        padding: 12px; /* Padding lebih besar */
        font-size: 1.1rem;
        background-color: #FFFFFF;
        color: #000000;
        font-weight: 600;
    }}
    
    /* 7a. Perbaikan: Label input diubah menjadi hitam agar terbaca */
    .stTextInput label, .stSelectbox label, .stNumberInput label, .stTextArea label {{
        font-weight: 600;
        color: var(--text-color) !important; /* Menambahkan !important untuk memastikan diterapkan */
        text-shadow: none;
    }}
    
    /* 8. Kontainer (Kartu) yang Lebih Estetik */
    .stContainer, div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {{
        padding: 1.5rem !important;
        border-radius: 12px;
        border: 1px solid #EAEAEA;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
        background-color: var(--secondary-background-color);
    }}

    /* 9. Navigasi Tabs yang Lebih Jelas */
    .stTabs [data-baseweb="tab"] {{
        font-size: 1.1rem;
        font-weight: 600;
        padding: 10px 15px;
    }}
    
    /* Hilangkan sidebar sepenuhnya dari tampilan */
    [data-testid="stSidebar"] {{
        display: none;
    }}
</style>
"""

# Injeksi CSS Kustom dengan satu panggilan `st.markdown`
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Bar atas - menggunakan h1 yang sudah didefinisikan di CSS kustom
st.markdown(f"<h1>{BRAND}</h1>", unsafe_allow_html=True)

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
    'user_profile': page_user_profile,
}

# Logika Router
# Gunakan st.session_state.get() untuk keamanan jika kunci tidak ada
current_page = st.session_state.get('page', 'login') 

# Render halaman saat ini berdasarkan state
if current_page in PAGE_MAP:
    PAGE_MAP[current_page]()
else:
    st.error("Halaman tidak dikenal. Anda akan diarahkan kembali ke halaman login.")
    st.session_state['page'] = 'login'
    st.rerun()
