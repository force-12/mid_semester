"""
File konfigurasi untuk aplikasi Caffe Dehh
Berisi semua variabel lingkungan dan pengaturan aplikasi
"""

import os
from dotenv import load_dotenv

load_dotenv()

# -------------------- KONFIGURASI --------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT", "5432")

# Nama bucket penyimpanan Supabase untuk menyimpan gambar menu
STORAGE_BUCKET = os.getenv("SUPABASE_BUCKET", "menu-images")

# Penjenamaan dasar
APP_TITLE = "Pesanan Kafe"
BRAND = "Caffe Dehh"
