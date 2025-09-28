"""
Database operations for Caffe Dehh application
Contains all CRUD operations for users, menu, orders, reviews, and promos
"""

import streamlit as st
import psycopg2
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from config import DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT

# -------------------- DATABASE UTILITIES --------------------

def get_db_conn():
    """Get database connection - create new connection each time"""
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
        st.error(f"DB connection error: {e}")
        return None

def hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def init_db():
    """Create tables if they do not exist. Run once at startup."""
    conn = None
    cur = None
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            );
            CREATE TABLE IF NOT EXISTS menu (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                price NUMERIC NOT NULL,
                image_url TEXT
            );
            CREATE TABLE IF NOT EXISTS promo (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                discount_amount NUMERIC NOT NULL,
                active BOOLEAN DEFAULT TRUE
            );
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                items_json JSONB,
                total_price NUMERIC,
                status TEXT DEFAULT 'Pending',
                payment_method TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                menu_id INTEGER REFERENCES menu(id),
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                review_text TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# -------------------- USER FUNCTIONS --------------------

def create_user(username: str, password: str, role: str = 'user'):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s) RETURNING id",
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

def authenticate(username: str, password: str):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, password, role FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    uid, pwd_hash, role = row
    if hash_password(password) == pwd_hash:
        return {"id": uid, "username": username, "role": role}
    return None

def read_users():
    conn = get_db_conn()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role FROM users ORDER BY id ASC")
            result = cursor.fetchall()
        conn.close()
        return result
    return []

def update_user_role(username, new_role):
    conn = get_db_conn()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role=%s WHERE username=%s",
                (new_role, username)
            )
        conn.commit()
        conn.close()

def delete_user(username):
    conn = get_db_conn()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE username=%s", (username,))
        conn.commit()
        conn.close()

# -------------------- MENU FUNCTIONS --------------------

def get_all_menu(search: str = "") -> List[Dict[str, Any]]:
    conn = get_db_conn()
    cur = conn.cursor()
    if search:
        cur.execute(
            "SELECT id, name, category, description, price, image_url FROM menu WHERE LOWER(name) LIKE LOWER(%s) ORDER BY category, name",
            (f"%{search}%",),
        )
    else:
        cur.execute("SELECT id, name, category, description, price, image_url FROM menu ORDER BY category, name")
    rows = cur.fetchall()
    cur.close()
    return [
        {"id": r[0], "name": r[1], "category": r[2], "description": r[3], "price": float(r[4]), "image_url": r[5]}
        for r in rows
    ]

def get_menu_item(menu_id: int):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, category, description, price, image_url FROM menu WHERE id = %s", (menu_id,))
    r = cur.fetchone()
    cur.close()
    if not r:
        return None
    return {"id": r[0], "name": r[1], "category": r[2], "description": r[3], "price": float(r[4]), "image_url": r[5]}

def create_menu_item(name, category, description, price, image_url=None):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO menu (name, category, description, price, image_url) VALUES (%s,%s,%s,%s,%s) RETURNING id",
        (name, category, description, price, image_url),
    )
    mid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return mid

def update_menu_item(menu_id, name, category, description, price, image_url=None):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE menu SET name=%s, category=%s, description=%s, price=%s, image_url=%s WHERE id=%s",
        (name, category, description, price, image_url, menu_id),
    )
    conn.commit()
    cur.close()

def delete_menu_item(menu_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM menu WHERE id=%s", (menu_id,))
    conn.commit()
    cur.close()

# -------------------- PROMO FUNCTIONS --------------------

def get_active_promo(code: str):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, code, discount_amount, active FROM promo WHERE code = %s AND active = TRUE", (code,))
    r = cur.fetchone()
    cur.close()
    if not r:
        return None
    return {"id": r[0], "code": r[1], "discount_amount": float(r[2]), "active": r[3]}

def list_promos():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, code, discount_amount, active FROM promo ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    return [{"id": r[0], "code": r[1], "discount_amount": float(r[2]), "active": r[3]} for r in rows]

def create_promo(code, amount, active=True):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO promo (code, discount_amount, active) VALUES (%s,%s,%s) RETURNING id", (code, amount, active))
    pid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return pid

def update_promo(pid, code, amount, active):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE promo SET code=%s, discount_amount=%s, active=%s WHERE id=%s", (code, amount, active, pid))
    conn.commit()
    cur.close()

def delete_promo(pid):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM promo WHERE id=%s", (pid,))
    conn.commit()
    cur.close()

# -------------------- ORDER FUNCTIONS --------------------

def create_order(user_id, items: List[Dict], total_price, payment_method):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (user_id, items_json, total_price, payment_method) VALUES (%s,%s,%s,%s) RETURNING id",
        (user_id, json.dumps(items), total_price, payment_method),
    )
    oid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return oid

def list_orders():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, items_json, total_price, status, payment_method, created_at FROM orders ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    return [
        {"id": r[0], "user_id": r[1], "items": r[2], "total": float(r[3]), "status": r[4], "payment_method": r[5], "created_at": r[6].isoformat()}
        for r in rows
    ]

def update_order_status(order_id, status):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
    conn.commit()
    cur.close()

def get_user_orders(user_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, items_json, total_price, status, payment_method, created_at FROM orders WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    cur.close()
    return [
        {"id": r[0], "items": r[1], "total": float(r[2]), "status": r[3], "payment_method": r[4], "created_at": r[5]}
        for r in rows
    ]

# -------------------- REVIEW FUNCTIONS --------------------

def submit_review(user_id, menu_id, rating, text):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO reviews (user_id, menu_id, rating, review_text) VALUES (%s,%s,%s,%s)", (user_id, menu_id, rating, text))
    conn.commit()
    cur.close()

def get_reviews_for_menu(menu_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT r.id, r.user_id, u.username, r.rating, r.review_text, r.created_at FROM reviews r LEFT JOIN users u ON r.user_id = u.id WHERE r.menu_id = %s ORDER BY r.created_at DESC", (menu_id,))
    rows = cur.fetchall()
    cur.close()
    return [
        {"id": r[0], "user_id": r[1], "username": r[2], "rating": r[3], "text": r[4], "created_at": r[5].isoformat()}
        for r in rows
    ]

def get_all_reviews():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT r.id, r.user_id, u.username, r.menu_id, m.name, r.rating, r.review_text, r.created_at FROM reviews r LEFT JOIN users u ON r.user_id = u.id LEFT JOIN menu m ON r.menu_id = m.id ORDER BY r.created_at DESC")
    rows = cur.fetchall()
    cur.close()
    return [
        {"id": r[0], "user_id": r[1], "username": r[2], "menu_id": r[3], "menu_name": r[4], "rating": r[5], "text": r[6], "created_at": r[7].isoformat()}
        for r in rows
    ]