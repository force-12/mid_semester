"""
Contains all functions for database CRUD operations.
Each function corresponds to a specific model (users, menu, orders, etc.).
"""

import json
from typing import List, Dict, Any
from config import get_db_connection
from auth import hash_password

# --- USER MODEL ---

def create_user(username: str, password: str, role: str = 'user') -> int:
    """Creates a new user and returns their ID."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s) RETURNING id",
            (username, hash_password(password), role),
        )
        uid = cur.fetchone()[0]
        conn.commit()
    return uid

# --- MENU MODEL ---

def get_all_menu_items(search: str = "") -> List[Dict[str, Any]]:
    """Fetches all menu items, optionally filtered by a search term."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        if search:
            query = "SELECT id, name, category, description, price, image_url FROM menu WHERE LOWER(name) LIKE LOWER(%s) ORDER BY category, name"
            cur.execute(query, (f"%{search}%",))
        else:
            query = "SELECT id, name, category, description, price, image_url FROM menu ORDER BY category, name"
            cur.execute(query)
        rows = cur.fetchall()
    return [
        {"id": r[0], "name": r[1], "category": r[2], "description": r[3], "price": float(r[4]), "image_url": r[5]}
        for r in rows
    ]

def get_menu_item_by_id(menu_id: int) -> Dict[str, Any] | None:
    """Fetches a single menu item by its ID."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, category, description, price, image_url FROM menu WHERE id = %s", (menu_id,))
        r = cur.fetchone()
    if not r:
        return None
    return {"id": r[0], "name": r[1], "category": r[2], "description": r[3], "price": float(r[4]), "image_url": r[5]}

def create_menu_item(name, category, description, price, image_url=None) -> int:
    """Creates a new menu item and returns its ID."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO menu (name, category, description, price, image_url) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (name, category, description, price, image_url),
        )
        mid = cur.fetchone()[0]
        conn.commit()
    return mid

def update_menu_item(menu_id, name, category, description, price, image_url=None):
    """Updates an existing menu item."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE menu SET name=%s, category=%s, description=%s, price=%s, image_url=%s WHERE id=%s",
            (name, category, description, price, image_url, menu_id),
        )
        conn.commit()

def delete_menu_item(menu_id: int):
    """Deletes a menu item."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM menu WHERE id=%s", (menu_id,))
        conn.commit()


# --- PROMO MODEL ---

def get_active_promo_by_code(code: str) -> Dict[str, Any] | None:
    """Finds an active promo by its code."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, code, discount_amount, active FROM promo WHERE code = %s AND active = TRUE", (code,))
        r = cur.fetchone()
    if not r: return None
    return {"id": r[0], "code": r[1], "discount_amount": float(r[2]), "active": r[3]}

def get_all_promos() -> List[Dict[str, Any]]:
    """Fetches all existing promo codes."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, code, discount_amount, active FROM promo ORDER BY id DESC")
        rows = cur.fetchall()
    return [{"id": r[0], "code": r[1], "discount_amount": float(r[2]), "active": r[3]} for r in rows]

def create_promo(code, amount, active=True) -> int:
    """Creates a new promo code."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO promo (code, discount_amount, active) VALUES (%s, %s, %s) RETURNING id", (code, amount, active))
        pid = cur.fetchone()[0]
        conn.commit()
    return pid

def update_promo(pid, code, amount, active):
    """Updates a promo's details."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE promo SET code=%s, discount_amount=%s, active=%s WHERE id=%s", (code, amount, active, pid))
        conn.commit()

def delete_promo(pid):
    """Deletes a promo code."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM promo WHERE id=%s", (pid,))
        conn.commit()


# --- ORDERS MODEL ---

def create_order(user_id, items: List[Dict], total_price, payment_method) -> int:
    """Creates a new order."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO orders (user_id, items_json, total_price, payment_method) VALUES (%s, %s, %s, %s) RETURNING id",
            (user_id, json.dumps(items), total_price, payment_method),
        )
        oid = cur.fetchone()[0]
        conn.commit()
    return oid

def get_all_orders() -> List[Dict[str, Any]]:
    """Fetches all orders, typically for admin view."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, user_id, items_json, total_price, status, payment_method, created_at FROM orders ORDER BY created_at DESC")
        rows = cur.fetchall()
    return [
        {"id": r[0], "user_id": r[1], "items": r[2], "total": float(r[3]), "status": r[4], "payment_method": r[5], "created_at": r[6].isoformat()}
        for r in rows
    ]

def get_orders_by_user_id(user_id: int) -> List[Dict[str, Any]]:
    """Fetches all orders for a specific user."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, items_json, total_price, status, payment_method, created_at FROM orders WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        rows = cur.fetchall()
    return [
        {"id": r[0], "items": r[1], "total": float(r[2]), "status": r[3], "payment_method": r[4], "created_at": r[5].isoformat()}
        for r in rows
    ]


def update_order_status(order_id: int, status: str):
    """Updates the status of an order."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
        conn.commit()

# --- REVIEWS MODEL ---

def create_review(user_id, menu_id, rating, text):
    """Submits a new review for a menu item."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO reviews (user_id, menu_id, rating, review_text) VALUES (%s, %s, %s, %s)", (user_id, menu_id, rating, text))
        conn.commit()

def get_reviews_for_menu_item(menu_id: int) -> List[Dict[str, Any]]:
    """Fetches all reviews for a specific menu item."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT r.id, r.user_id, u.username, r.rating, r.review_text, r.created_at FROM reviews r LEFT JOIN users u ON r.user_id = u.id WHERE r.menu_id = %s ORDER BY r.created_at DESC", (menu_id,))
        rows = cur.fetchall()
    return [
        {"id": r[0], "user_id": r[1], "username": r[2], "rating": r[3], "text": r[4], "created_at": r[5].isoformat()}
        for r in rows
    ]

def get_all_reviews() -> List[Dict[str, Any]]:
    """Fetches all reviews, typically for admin view."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT r.id, r.user_id, u.username, r.menu_id, m.name, r.rating, r.review_text, r.created_at FROM reviews r LEFT JOIN users u ON r.user_id = u.id LEFT JOIN menu m ON r.menu_id = m.id ORDER BY r.created_at DESC")
        rows = cur.fetchall()
    return [
        {"id": r[0], "user_id": r[1], "username": r[2], "menu_id": r[3], "menu_name": r[4], "rating": r[5], "text": r[6], "created_at": r[7].isoformat()}
        for r in rows
    ]
