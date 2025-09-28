"""
Operasi penyimpanan Supabase untuk aplikasi Caffe Dehh
Menangani pengunggahan gambar dan manajemen penyimpanan
"""

import streamlit as st
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, STORAGE_BUCKET

# -------------------- UTILITAS PENYIMPANAN --------------------

@st.cache_resource
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Kredensial Supabase tidak diatur. Atur SUPABASE_URL dan SUPABASE_KEY di env.")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image_to_storage(file_bytes: bytes, filename: str) -> str:
    sb = get_supabase()
    if not sb:
        raise Exception("Klien Supabase tidak dikonfigurasi")
    
    path = f"{filename}"
    try:
        # Pustaka supabase-py v2 akan langsung memberikan galat (exception) jika gagal,
        # jadi kita tidak perlu lagi memeriksa 'error' secara manual dengan .get().
        sb.storage.from_(STORAGE_BUCKET).upload(path, file_bytes)
        
        # Fungsi get_public_url sekarang mengembalikan URL dalam bentuk string secara langsung.
        public_url = sb.storage.from_(STORAGE_BUCKET).get_public_url(path)
        return public_url
    except Exception as e:
        # Menangkap dan meneruskan galat agar dapat ditampilkan di antarmuka pengguna.
        raise e

def delete_image_from_storage(filename: str):
    sb = get_supabase()
    if not sb:
        raise Exception("Klien Supabase tidak dikonfigurasi")
    try:
        # Sama seperti upload, fungsi remove juga akan memberikan galat jika gagal.
        sb.storage.from_(STORAGE_BUCKET).remove([filename])
        return True
    except Exception as e:
        raise e

