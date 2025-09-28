"""
User dashboard for Caffe Dehh application
Contains menu viewing, cart management, order placement and review functionality
"""

import streamlit as st
from database import (
    get_all_menu, get_menu_item, create_order, get_user_orders, 
    submit_review, get_active_promo
)

def show_user_dashboard():
    st.subheader("User Dashboard")
    user = st.session_state['user']
    st.write(f"Logged in as: {user['username']}")
    
    if st.button("Logout"):
        st.session_state['user'] = None
        st.session_state['logged_in'] = False
        st.session_state['page'] = 'login'
        st.rerun()

    tabs = st.tabs(["Menu", "Cart", "Orders / Status", "Profile"])
    
    with tabs[0]:
        show_menu_tab()
    with tabs[1]:
        show_cart_tab()
    with tabs[2]:
        show_user_orders_tab()
    with tabs[3]:
        show_profile_tab()

def show_menu_tab():
    search = st.text_input("Search menu by name")
    menu_items = get_all_menu(search)
    
    # Group by category
    cats = {}
    for m in menu_items:
        cats.setdefault(m['category'], []).append(m)
    
    for cat, items in cats.items():
        st.markdown(f"### {cat}")
        cols = st.columns(3)
        for i, it in enumerate(items):
            c = cols[i % 3]
            with c:
                st.markdown(f"**{it['name']}** — Rp {int(it['price'])}")
                if it['image_url']:
                    st.image(it['image_url'], use_column_width=True)
                st.write(it['description'])
                qty = st.number_input(f"Qty_{it['id']}", min_value=1, value=1, key=f"qty_{it['id']}")
                if st.button("Add to cart", key=f"add_{it['id']}"):
                    add_to_cart(it['id'], qty)
                    st.success("Added to cart")

def show_cart_tab():
    st.markdown("### Cart")
    cart = st.session_state.get('cart', {})
    
    if not cart:
        st.info("Cart kosong — tambahkan item dari Menu")
        return
    
    ids = list(map(int, cart.keys()))
    items = [get_menu_item(i) for i in ids]
    total = 0
    
    for it in items:
        if it:  # Check if item exists
            q = cart[str(it['id'])]
            st.write(f"{it['name']} x {q} — Rp {int(it['price'])} each")
            total += it['price'] * q
            if st.button(f"Remove {it['id']}", key=f"rm_{it['id']}"):
                remove_from_cart(it['id'])
                st.rerun()
    
    st.write(f"Subtotal: Rp {int(total)}")
    
    # Promo code section
    promo_code = st.text_input("Promo code", key='promo_input')
    if st.button("Apply Promo"):
        promo = get_active_promo(promo_code)
        if promo:
            st.session_state['promo_applied'] = promo
            st.success(f"Promo applied: {promo['code']} - Rp {int(promo['discount_amount'])}")
        else:
            st.error("Invalid or inactive promo")
    
    discount = 0
    if st.session_state.get('promo_applied'):
        discount = float(st.session_state['promo_applied']['discount_amount'])
    
    grand = max(0, total - discount)
    st.write(f"Discount: Rp {int(discount)}")
    st.write(f"Total: Rp {int(grand)}")

    st.markdown("---")
    st.markdown("### Checkout")
    name = st.text_input("Nama pemesan")
    table_no = st.text_input("Nomor meja")
    payment_method = st.selectbox("Metode pembayaran", ["Cash", "QRIS", "E-Wallet"])
    
    if st.button("Place Order"):
        user = st.session_state['user']
        if not user:
            st.error("Silakan login dulu")
            return
        
        items_payload = []
        for it in items:
            if it:  # Check if item exists
                items_payload.append({
                    'menu_id': it['id'], 
                    'name': it['name'], 
                    'price': it['price'], 
                    'qty': cart[str(it['id'])]
                })
        
        oid = create_order(user['id'], items_payload, grand, payment_method)
        st.success(f"Order placed (ID: {oid}). Bayar di kasir.")
        
        # Clear cart & promo
        st.session_state['cart'] = {}
        st.session_state['promo_applied'] = None

def show_user_orders_tab():
    st.markdown("### Your Orders")
    user = st.session_state['user']
    orders = get_user_orders(user['id'])
    
    if not orders:
        st.info("Belum ada pesanan")
        return
    
    for order in orders:
        st.write(f"Order ID: {order['id']} | Status: {order['status']} | Total: Rp {int(order['total'])} | {order['created_at']} | {order['payment_method']}")
        items = order['items']
        for it in items:
            st.write(f" - {it['name']} x {it['qty']}")
        
        if order['status'] == 'Selesai':
            if st.button(f"Rate Order {order['id']}", key=f"rate_{order['id']}"):
                st.session_state['page'] = 'review'
                st.session_state['review_target_order'] = order['id']
                st.rerun()

def show_profile_tab():
    st.write("Profile - not implemented deeply")
    user = st.session_state['user']
    st.write(f"Username: {user['username']}")
    st.write(f"Role: {user['role']}")

def add_to_cart(menu_id, qty=1):
    if 'cart' not in st.session_state:
        st.session_state['cart'] = {}
    cart = st.session_state['cart']
    cart[str(menu_id)] = cart.get(str(menu_id), 0) + int(qty)
    st.session_state['cart'] = cart

def remove_from_cart(menu_id):
    cart = st.session_state.get('cart', {})
    if str(menu_id) in cart:
        del cart[str(menu_id)]
    st.session_state['cart'] = cart

def page_review():
    st.subheader("Submit Review")
    order_id = st.session_state.get('review_target_order')
    st.write(f"Reviewing order: {order_id}")
    
    # For simplicity let user pick menu item to review
    menu_items = get_all_menu()
    choices = {f"{m['id']} - {m['name']}": m['id'] for m in menu_items}
    sel = st.selectbox("Pilih menu untuk di-review", list(choices.keys()))
    rating = st.slider("Rating", 1, 5, 5)
    text = st.text_area("Review")
    
    if st.button("Submit Review"):
        uid = st.session_state['user']['id']
        mid = choices[sel]
        submit_review(uid, mid, rating, text)
        st.success("Thanks for the review!")
        st.session_state['page'] = 'user_dashboard'
        st.rerun()