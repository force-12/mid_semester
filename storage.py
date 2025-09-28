"""
Supabase storage operations for Caffe Dehh application
Handles image upload and storage management
"""

import streamlit as st
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, STORAGE_BUCKET

# -------------------- STORAGE UTILITIES --------------------

@st.cache_resource
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Supabase credentials not set. Set SUPABASE_URL and SUPABASE_KEY in env.")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image_to_storage(file_bytes: bytes, filename: str) -> str:
    sb = get_supabase()
    if not sb:
        raise Exception("Supabase client not configured")
    # Put into bucket
    path = f"{filename}"
    res = sb.storage.from_(SUPABASE_BUCKET).upload(path, file_bytes)
    # Note: supabase-py returns dict with 'error' key on failure
    if res.get('error'):
        raise Exception(res['error'])
    public_url = sb.storage.from_(SUPABASE_BUCKET).get_public_url(path)
    return public_url.get('publicURL') if isinstance(public_url, dict) else public_url

def delete_image_from_storage(filename: str):
    sb = get_supabase()
    if not sb:
        raise Exception("Supabase client not configured")
    res = sb.storage.from_(SUPABASE_BUCKET).remove([filename])
    if res.get('error'):
        raise Exception(res['error'])
    return True