"""
Admin dashboard for Caffe Dehh application
Contains menu management, promo management, order management and review monitoring
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    get_all_menu, create_menu_item, update_menu_item, delete_menu_item,
    list_promos, create_promo, update_promo, delete_promo,
    list_orders, update_order_status,
    get_all_reviews,
    read_users, create_user, update_user_role, delete_user
)
from storage import upload_image_to_storage

def show_admin_dashboard():
    st.title("Dashboard Admin")

    if not st.session_state.get("logged_in", False) or st.session_state.get("role") != "admin":
        st.error("Anda tidak memiliki izin untuk mengakses halaman ini.")
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.subheader(f"Selamat datang, Admin {st.session_state.username}!")
    
    user = st.session_state['user']
    st.write(f"Logged in as admin: {user['username']}")
    
    if st.button("Logout"):
        st.session_state['user'] = None
        st.session_state['logged_in'] = False
        st.session_state['page'] = 'login'
        st.rerun()

    tabs = st.tabs(["Manage Menu", "Manage Promo", "Orders", "Reviews", "User Management"])
    
    with tabs[0]:
        manage_menu()
    with tabs[1]:
        manage_promo()
    with tabs[2]:
        admin_orders()
    with tabs[3]:
        admin_reviews()
    with tabs[4]:
        manage_users()

def manage_menu():
    st.markdown("### Menu Management")
    
    with st.expander("Add new menu item"):
        name = st.text_input("Name", key='m_name')
        category = st.selectbox("Category", ["Food", "Drink", "Dessert"], key='m_cat')
        desc = st.text_area("Description", key='m_desc')
        price = st.number_input("Price", min_value=0.0, value=20000.0, key='m_price')
        img = st.file_uploader("Image (optional)", type=['png', 'jpg', 'jpeg'], key='m_img')
        
        if st.button("Create Menu Item"):
            image_url = None
            if img is not None:
                bytes_data = img.getvalue()
                filename = f"{int(datetime.now().timestamp())}_{img.name}"
                try:
                    image_url = upload_image_to_storage(bytes_data, filename)
                except Exception as e:
                    st.error(f"Upload error: {e}")
            create_menu_item(name, category, desc, price, image_url)
            st.success("Menu item created")
    
    st.markdown("---")
    st.markdown("#### Existing items")
    items = get_all_menu()
    
    for it in items:
        cols = st.columns([2,1,1])
        with cols[0]:
            st.write(f"{it['name']} ({it['category']}) — Rp {int(it['price'])}")
            st.write(it['description'])
            if it['image_url']:
                st.image(it['image_url'], width=150)
        with cols[1]:
            if st.button(f"Edit_{it['id']}"):
                st.session_state['edit_item'] = it
                st.session_state['page'] = 'admin_edit_menu'
                st.rerun()
        with cols[2]:
            if st.button(f"Delete_{it['id']}"):
                delete_menu_item(it['id'])
                st.success("Deleted")
                st.rerun()

def manage_promo():
    st.markdown("### Promo Management")
    
    with st.expander("Create promo"):
        code = st.text_input("Code", key='p_code')
        amt = st.number_input("Discount amount (Rp)", min_value=0.0, value=5000.0, key='p_amt')
        active = st.checkbox("Active", value=True, key='p_active')
        
        if st.button("Create Promo"):
            create_promo(code, amt, active)
            st.success("Promo created")
    
    st.markdown("---")
    promos = list_promos()
    
    for p in promos:
        cols = st.columns([2,1,1])
        with cols[0]:
            st.write(f"{p['code']} — Rp {int(p['discount_amount'])} — {'Active' if p['active'] else 'Inactive'}")
        with cols[1]:
            if st.button(f"Toggle_{p['id']}"):
                update_promo(p['id'], p['code'], p['discount_amount'], not p['active'])
                st.rerun()
        with cols[2]:
            if st.button(f"DeletePromo_{p['id']}"):
                delete_promo(p['id'])
                st.rerun()

def admin_orders():
    st.markdown("### Orders")
    orders = list_orders()
    
    for o in orders:
        st.write(f"Order {o['id']} — User {o['user_id']} — Rp {int(o['total'])} — {o['status']} — {o['payment_method']} — {o['created_at']}")
        items = o['items']
        for it in items:
            st.write(f" - {it['name']} x {it['qty']}")
        
        new_status = st.selectbox(f"Update status for {o['id']}", 
                                 ["Pending","Sedang Diproses","Selesai"], 
                                 key=f"status_{o['id']}")
        if st.button(f"Update_{o['id']}"):
            update_order_status(o['id'], new_status)
            st.success("Status updated")
            st.rerun()

def admin_reviews():
    st.markdown("### Reviews")
    reviews = get_all_reviews()
    
    for r in reviews:
        st.write(f"{r['created_at']} | {r['username']} | {r['menu_name']} | Rating: {r['rating']}")
        st.write(r['text'])

def manage_users():
    st.markdown("### User Management")
    
    user_menu = st.radio("Pilih Operasi", ["Lihat Pengguna", "Tambah Pengguna", "Ubah Peran", "Hapus Pengguna"])

    if user_menu == "Lihat Pengguna":
        st.write("Berikut adalah daftar semua pengguna:")
        users_data = read_users()
        df_users = pd.DataFrame(users_data, columns=["ID", "Username", "Role"])
        st.dataframe(df_users)
    
    elif user_menu == "Tambah Pengguna":
        st.write("Silakan isi detail pengguna baru:")
        new_username = st.text_input("Username Baru")
        new_password = st.text_input("Password Baru", type="password")
        new_role = st.selectbox("Peran", ["user", "admin"])
        if st.button("Tambahkan Pengguna"):
            try:
                create_user(new_username, new_password, new_role)
                st.success(f"Pengguna {new_username} berhasil ditambahkan dengan peran {new_role}!")
            except Exception as e:
                if "unique constraint" in str(e).lower():
                    st.error("Username sudah terdaftar.")
                else:
                    st.error(f"Error: {e}")
    
    elif user_menu == "Ubah Peran":
        users_data = read_users()
        usernames = [row[1] for row in users_data]
        selected_username = st.selectbox("Pilih Pengguna", usernames)
        new_role_update = st.selectbox("Ubah Peran menjadi", ["user", "admin"])
        if st.button("Perbarui Peran"):
            update_user_role(selected_username, new_role_update)
            st.success(f"Peran pengguna {selected_username} berhasil diubah menjadi {new_role_update}!")
    
    elif user_menu == "Hapus Pengguna":
        users_data = read_users()
        usernames = [row[1] for row in users_data]
        selected_username_delete = st.selectbox("Pilih Pengguna yang akan Dihapus", usernames)
        if st.button("Hapus Pengguna"):
            delete_user(selected_username_delete)
            st.success(f"Pengguna {selected_username_delete} berhasil dihapus!")

def page_admin_edit_menu():
    it = st.session_state.get('edit_item')
    if not it:
        st.error("No item selected")
        st.session_state['page'] = 'admin_dashboard'
        return
    
    st.subheader(f"Edit: {it['name']}")
    name = st.text_input("Name", value=it['name'])
    category = st.selectbox("Category", ["Food", "Drink", "Dessert"], 
                           index=["Food","Drink","Dessert"].index(it['category']))
    desc = st.text_area("Description", value=it['description'])
    price = st.number_input("Price", min_value=0.0, value=it['price'])
    img = st.file_uploader("Image (optional)", type=['png','jpg','jpeg'])
    
    if st.button("Save Changes"):
        image_url = it['image_url']
        if img:
            try:
                filename = f"{int(datetime.now().timestamp())}_{img.name}"
                image_url = upload_image_to_storage(img.getvalue(), filename)
            except Exception as e:
                st.error(f"Upload error: {e}")
        
        update_menu_item(it['id'], name, category, desc, price, image_url)
        st.success("Updated")
        st.session_state['page'] = 'admin_dashboard'
        st.rerun()
    
    if st.button("Cancel"):
        st.session_state['page'] = 'admin_dashboard'
        st.rerun()