"""
Configuration file for Caffe Dehh application
Contains all environment variables and app settings
"""

import os
from dotenv import load_dotenv

load_dotenv()

# -------------------- CONFIG --------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT", "5432")

# Supabase storage bucket name to store menu images
STORAGE_BUCKET = os.getenv("SUPABASE_BUCKET", "menu-images")

# Basic branding
APP_TITLE = "Caffe Order"
BRAND = "Caffe Dehh"