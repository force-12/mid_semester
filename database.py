"""
Operasi database untuk aplikasi Caffe Dehh
Berisi semua operasi CRUD dan fungsi untuk fitur-fitur baru.
"""

import streamlit as st
import psycopg2
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from config import DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT

# -------------------- UTILITAS DATABASE --------------------

def get_db_conn():
    """Mendapatkan koneksi database - membuat koneksi baru setiap kali"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST, 
            dbname=DB_NAME, 
            user=DB_USER, 
            password=DB_PASS, 
            port=DB_PORT,
            connect_timeout=10,
            sslmode='require'
        )
        return conn
    except Exception as e:
        st.error(f"Kesalahan koneksi DB: {e}")
        return None

def hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def init_db():
    """Membuat tabel jika belum ada. Dijalankan sekali saat startup."""
    conn = None
    cur = None
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pengguna (
                id SERIAL PRIMARY KEY,
                nama_pengguna TEXT UNIQUE NOT NULL,
                kata_sandi TEXT NOT NULL,
                peran TEXT NOT NULL DEFAULT 'user'
            );
            CREATE TABLE IF NOT EXISTS menu (
                id SERIAL PRIMARY KEY,
                nama TEXT NOT NULL,
                kategori TEXT NOT NULL,
                deskripsi TEXT,
                harga NUMERIC NOT NULL,
                url_gambar TEXT,
                tersedia BOOLEAN DEFAULT TRUE
            );
            CREATE TABLE IF NOT EXISTS promo (
                id SERIAL PRIMARY KEY,
                kode TEXT UNIQUE NOT NULL,
                jumlah_diskon NUMERIC NOT NULL,
                aktif BOOLEAN DEFAULT TRUE
            );
            CREATE TABLE IF NOT EXISTS pesanan (
                id SERIAL PRIMARY KEY,
                id_pengguna INTEGER REFERENCES pengguna(id),
                item JSONB,
                total NUMERIC,
                status TEXT DEFAULT 'Tertunda',
                metode_pembayaran TEXT,
                dibuat_pada TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS ulasan (
                id SERIAL PRIMARY KEY,
                id_pengguna INTEGER REFERENCES pengguna(id),
                id_menu INTEGER REFERENCES menu(id),
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                teks_ulasan TEXT,
                dibuat_pada TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS menu_favorit (
                id SERIAL PRIMARY KEY,
                id_pengguna INTEGER REFERENCES pengguna(id),
                id_menu INTEGER REFERENCES menu(id),
                UNIQUE(id_pengguna, id_menu)
            );
            """
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Kesalahan inisialisasi database: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# -------------------- FUNGSI PENGGUNA --------------------
# (Fungsi Pengguna, Promo, Pesanan, Ulasan tidak berubah secara signifikan, jadi disingkat)
def create_user(username: str, password: str, role: str = 'user'):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO pengguna (nama_pengguna, kata_sandi, peran) VALUES (%s, %s, %s) RETURNING id",
            (username, hash_password(password), role),
        )
        uid = cur.fetchone()[0]
        conn.commit()
        return uid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def authenticate(username: str, password: str):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, kata_sandi, peran FROM pengguna WHERE nama_pengguna = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    uid, pwd_hash, role = row
    if hash_password(password) == pwd_hash:
        return {"id": uid, "nama_pengguna": username, "peran": role}
    return None

def user_exists(username: str) -> bool:
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM pengguna WHERE nama_pengguna = %s", (username,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def update_user_password(username: str, new_password: str):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        hashed_password = hash_password(new_password)
        cur.execute("UPDATE pengguna SET kata_sandi = %s WHERE nama_pengguna = %s", (hashed_password, username))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def read_users():
    conn = get_db_conn()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, nama_pengguna, peran FROM pengguna ORDER BY id ASC")
            result = cursor.fetchall()
        conn.close()
        return result
    return []

def update_user_role(username, new_role):
    conn = get_db_conn()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE pengguna SET peran=%s WHERE nama_pengguna=%s",
                (new_role, username)
            )
        conn.commit()
        conn.close()

def delete_user(username):
    conn = get_db_conn()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM pengguna WHERE nama_pengguna=%s", (username,))
        conn.commit()
        conn.close()
# -------------------- FUNGSI MENU --------------------

def get_all_menu(search: str = "", user_id: int = None) -> List[Dict[str, Any]]:
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Kueri ini sekarang juga mengambil status 'tersedia' dan apakah menu ini favorit pengguna
    base_query = """
        SELECT 
            m.id, m.nama, m.kategori, m.deskripsi, m.harga, m.url_gambar, m.tersedia,
            COALESCE(AVG(u.rating), 0) as rating_rata_rata,
            COUNT(u.id) as jumlah_ulasan,
            CASE WHEN f.id_menu IS NOT NULL THEN TRUE ELSE FALSE END as is_favorite
        FROM menu m
        LEFT JOIN ulasan u ON m.id = u.id_menu
        LEFT JOIN menu_favorit f ON m.id = f.id_menu AND f.id_pengguna = %(user_id)s
    """
    
    params = {'user_id': user_id}

    if search:
        query = base_query + " WHERE LOWER(m.nama) LIKE LOWER(%(search)s) GROUP BY m.id, f.id_menu ORDER BY m.kategori, m.nama"
        params['search'] = f"%{search}%"
    else:
        query = base_query + " GROUP BY m.id, f.id_menu ORDER BY m.kategori, m.nama"
        
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "nama": r[1], "kategori": r[2], "deskripsi": r[3], "harga": float(r[4]), 
         "url_gambar": r[5], "tersedia": r[6], "rating_rata_rata": float(r[7]), 
         "jumlah_ulasan": int(r[8]), "is_favorite": r[9]}
        for r in rows
    ]

def update_menu_availability(menu_id: int, is_available: bool):
    """Mengubah status ketersediaan menu."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE menu SET tersedia = %s WHERE id = %s", (is_available, menu_id))
    conn.commit()
    cur.close()
    conn.close()

# -------------------- FUNGSI MENU FAVORIT --------------------

def add_to_favorites(user_id: int, menu_id: int):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO menu_favorit (id_pengguna, id_menu) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user_id, menu_id))
    conn.commit()
    cur.close()
    conn.close()

def remove_from_favorites(user_id: int, menu_id: int):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM menu_favorit WHERE id_pengguna = %s AND id_menu = %s", (user_id, menu_id))
    conn.commit()
    cur.close()
    conn.close()

def get_favorite_menus(user_id: int) -> List[Dict[str, Any]]:
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            m.id, m.nama, m.kategori, m.deskripsi, m.harga, m.url_gambar, m.tersedia,
            COALESCE(AVG(u.rating), 0) as rating_rata_rata,
            COUNT(u.id) as jumlah_ulasan
        FROM menu_favorit f
        JOIN menu m ON f.id_menu = m.id
        LEFT JOIN ulasan u ON m.id = u.id_menu
        WHERE f.id_pengguna = %s
        GROUP BY m.id
        ORDER BY m.nama
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "nama": r[1], "kategori": r[2], "deskripsi": r[3], "harga": float(r[4]), 
         "url_gambar": r[5], "tersedia": r[6], "rating_rata_rata": float(r[7]), 
         "jumlah_ulasan": int(r[8]), "is_favorite": True}
        for r in rows
    ]

# -------------------- FUNGSI ANALITIK --------------------

def get_sales_data():
    """Mengambil data penjualan untuk grafik."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            DATE(dibuat_pada) as tanggal, 
            SUM(total) as total_pendapatan
        FROM pesanan
        WHERE status = 'Selesai'
        GROUP BY DATE(dibuat_pada)
        ORDER BY tanggal ASC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_top_selling_items():
    """Mengambil item menu terlaris."""
    conn = get_db_conn()
    cur = conn.cursor()
    # Kueri ini sedikit rumit karena harus "membongkar" JSON
    cur.execute("""
        SELECT 
            (item_data->>'nama')::TEXT as nama_menu,
            SUM((item_data->>'qty')::INTEGER) as jumlah_terjual
        FROM pesanan, jsonb_array_elements(item) as item_data
        WHERE pesanan.status = 'Selesai'
        GROUP BY nama_menu
        ORDER BY jumlah_terjual DESC
        LIMIT 10;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# (Tambahkan fungsi-fungsi lain yang sudah ada di sini seperti create_menu_item, create_order, dll.)
def get_menu_item(menu_id: int):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nama, kategori, deskripsi, harga, url_gambar FROM menu WHERE id = %s", (menu_id,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    if not r:
        return None
    return {"id": r[0], "nama": r[1], "kategori": r[2], "deskripsi": r[3], "harga": float(r[4]), "url_gambar": r[5]}

def create_menu_item(name, category, description, price, image_url=None):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO menu (nama, kategori, deskripsi, harga, url_gambar) VALUES (%s,%s,%s,%s,%s) RETURNING id",
        (name, category, description, price, image_url),
    )
    mid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return mid

def update_menu_item(menu_id, name, category, description, price, image_url=None):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE menu SET nama=%s, kategori=%s, deskripsi=%s, harga=%s, url_gambar=%s WHERE id=%s",
        (name, category, description, price, image_url, menu_id),
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_menu_item(menu_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM menu WHERE id=%s", (menu_id,))
    conn.commit()
    cur.close()
    conn.close()

# -------------------- FUNGSI PROMO --------------------

def get_active_promo(code: str):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, kode, jumlah_diskon, aktif FROM promo WHERE kode = %s AND aktif = TRUE", (code,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    if not r:
        return None
    return {"id": r[0], "kode": r[1], "jumlah_diskon": float(r[2]), "aktif": r[3]}

def list_promos():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, kode, jumlah_diskon, aktif FROM promo ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "kode": r[1], "jumlah_diskon": float(r[2]), "aktif": r[3]} for r in rows]

def create_promo(code, amount, active=True):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO promo (kode, jumlah_diskon, aktif) VALUES (%s,%s,%s) RETURNING id", (code, amount, active))
    pid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return pid

def update_promo(pid, code, amount, active):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE promo SET kode=%s, jumlah_diskon=%s, aktif=%s WHERE id=%s", (code, amount, active, pid))
    conn.commit()
    cur.close()
    conn.close()

def delete_promo(pid):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM promo WHERE id=%s", (pid,))
    conn.commit()
    cur.close()
    conn.close()

# -------------------- FUNGSI PESANAN --------------------

def create_order(user_id, items: List[Dict], total_price, payment_method):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pesanan (id_pengguna, item, total, metode_pembayaran) VALUES (%s,%s,%s,%s) RETURNING id",
        (user_id, json.dumps(items), total_price, payment_method),
    )
    oid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return oid

def list_orders():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, id_pengguna, item, total, status, metode_pembayaran, dibuat_pada FROM pesanan ORDER BY dibuat_pada DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "id_pengguna": r[1], "item": r[2], "total": float(r[3]), "status": r[4], "metode_pembayaran": r[5], "dibuat_pada": r[6].isoformat()}
        for r in rows
    ]

def update_order_status(order_id, status):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE pesanan SET status=%s WHERE id=%s", (status, order_id))
    conn.commit()
    cur.close()
    conn.close()

def get_user_orders(user_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, item, total, status, metode_pembayaran, dibuat_pada FROM pesanan WHERE id_pengguna = %s ORDER BY dibuat_pada DESC", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "item": r[1], "total": float(r[2]), "status": r[3], "metode_pembayaran": r[4], "dibuat_pada": r[5]}
        for r in rows
    ]

def get_order_by_id(order_id: int):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, item, total, status, metode_pembayaran, dibuat_pada FROM pesanan WHERE id = %s", (order_id,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    if not r:
        return None
    return {"id": r[0], "item": r[1], "total": float(r[2]), "status": r[3], "metode_pembayaran": r[4], "dibuat_pada": r[5]}


# -------------------- FUNGSI ULASAN --------------------

def submit_review(user_id, menu_id, rating, text):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO ulasan (id_pengguna, id_menu, rating, teks_ulasan) VALUES (%s,%s,%s,%s)", (user_id, menu_id, rating, text))
    conn.commit()
    cur.close()
    conn.close()

def get_reviews_for_menu(menu_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT u.id, u.id_pengguna, p.nama_pengguna, u.rating, u.teks_ulasan, u.dibuat_pada FROM ulasan u LEFT JOIN pengguna p ON u.id_pengguna = p.id WHERE u.id_menu = %s ORDER BY u.dibuat_pada DESC", (menu_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "id_pengguna": r[1], "nama_pengguna": r[2], "penilaian": r[3], "teks_ulasan": r[4], "dibuat_pada": r[5]}
        for r in rows
    ]

def get_all_reviews():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT u.id, u.id_pengguna, p.nama_pengguna, u.id_menu, m.nama, u.rating, u.teks_ulasan, u.dibuat_pada FROM ulasan u LEFT JOIN pengguna p ON u.id_pengguna = p.id LEFT JOIN menu m ON u.id_menu = m.id ORDER BY u.dibuat_pada DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "id_pengguna": r[1], "nama_pengguna": r[2], "id_menu": r[3], "nama_menu": r[4], "penilaian": r[5], "teks_ulasan": r[6], "dibuat_pada": r[7].isoformat()}
        for r in rows
    ]

