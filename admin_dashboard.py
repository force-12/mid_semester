"""
Dasbor admin untuk aplikasi Caffe Dehh
Berisi manajemen menu (termasuk stok), promo, pesanan, ulasan, dan analitik.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    get_all_menu, create_menu_item, update_menu_item, delete_menu_item,
    list_promos, create_promo, update_promo, delete_promo,
    list_orders, update_order_status,
    get_all_reviews,
    read_users, create_user, update_user_role, delete_user,
    update_menu_availability, get_sales_data, get_top_selling_items
)
from storage import upload_image_to_storage

def show_admin_dashboard():
    st.title("Dasbor Admin")
    user = st.session_state.get('user', {})
    
    st.sidebar.subheader(f"Selamat datang, Admin {user.get('nama_pengguna', '')}!")
    if st.sidebar.button("Keluar"):
        st.session_state.clear()
        st.session_state['page'] = 'login'
        st.rerun()

    tabs = st.tabs(["📊 Analitik", "🍔 Kelola Menu", "🎉 Kelola Promo", "📦 Pesanan", "⭐ Ulasan", "👤 Manajemen Pengguna"])
    
    with tabs[0]:
        show_analytics_tab()
    with tabs[1]:
        manage_menu()
    with tabs[2]:
        manage_promo()
    with tabs[3]:
        admin_orders()
    with tabs[4]:
        admin_reviews()
    with tabs[5]:
        manage_users()

def show_analytics_tab():
    st.markdown("### Analitik Penjualan")
    st.markdown("#### Pendapatan Harian")
    sales_data = get_sales_data()
    if sales_data:
        df_sales = pd.DataFrame(sales_data, columns=['tanggal', 'total_pendapatan'])
        df_sales['tanggal'] = pd.to_datetime(df_sales['tanggal'])
        df_sales = df_sales.set_index('tanggal')
        st.line_chart(df_sales)
    else:
        st.info("Belum ada data penjualan yang selesai untuk ditampilkan.")

    st.markdown("#### Menu Terlaris")
    top_items = get_top_selling_items()
    if top_items:
        df_top_items = pd.DataFrame(top_items, columns=['nama_menu', 'jumlah_terjual'])
        df_top_items = df_top_items.set_index('nama_menu')
        st.bar_chart(df_top_items)
    else:
        st.info("Belum ada data item terlaris.")

def manage_menu():
    st.markdown("### Manajemen Menu")
    
    # Mengubah expander menjadi tombol navigasi
    if st.button("➕ Tambah Menu Baru"):
        st.session_state['page'] = 'admin_add_menu'
        st.rerun()

    st.markdown("---")
    st.markdown("#### Daftar Menu Saat Ini")
    items = get_all_menu()
    for it in items:
        col1, col2 = st.columns([3, 1])
        with col1:
            status = "Tersedia" if it.get('tersedia', True) else "Habis"
            st.write(f"**{it['nama']}** ({it['kategori']}) — Rp {int(it['harga'])} — *Status: {status}*")
            if it['deskripsi']:
                st.caption(it['deskripsi'])
            if it['url_gambar']:
                st.image(it['url_gambar'], width=150)
        
        with col2:
            if st.button("Ubah Status", key=f"stock_{it['id']}"):
                new_status = not it.get('tersedia', True)
                update_menu_availability(it['id'], new_status)
                st.rerun()

            if st.button("Edit", key=f"edit_{it['id']}"):
                st.session_state['edit_item'] = it
                st.session_state['page'] = 'admin_edit_menu'
                st.rerun()

            if st.button("Hapus", key=f"delete_{it['id']}"):
                delete_menu_item(it['id'])
                st.success("Menu dihapus")
                st.rerun()
        st.markdown("---")

def manage_promo():
    st.markdown("### Manajemen Promo")
    
    # Mengubah expander menjadi tombol navigasi
    if st.button("🎉 Buat Promo Baru"):
        st.session_state['page'] = 'admin_add_promo'
        st.rerun()

    st.markdown("---")
    promos = list_promos()
    for p in promos:
        cols = st.columns([2, 1, 1])
        with cols[0]:
            status_text = "Aktif" if p.get('aktif') else "Tidak Aktif"
            st.write(f"{p.get('kode')} — Rp {int(p.get('jumlah_diskon',0))} — {status_text}")
        with cols[1]:
            if st.button("Aktif/Nonaktifkan", key=f"toggle_promo_{p['id']}"):
                update_promo(p['id'], p['kode'], p['jumlah_diskon'], not p['aktif'])
                st.rerun()
        with cols[2]:
            if st.button("Hapus", key=f"delete_promo_{p['id']}"):
                delete_promo(p['id'])
                st.rerun()

def admin_orders():
    # ... (Fungsi ini tidak berubah)
    st.markdown("### Daftar Pesanan")
    orders = list_orders()
    for o in orders:
        st.write(f"Pesanan {o['id']} — Pengguna {o['id_pengguna']} — Rp {int(o['total'])} — {o['status']} — {o['metode_pembayaran']} — {o['dibuat_pada']}")
        items = o.get('item', [])
        for it in items:
            st.write(f" - {it.get('nama','N/A')} x {it.get('qty',0)}")
        
        status_options = ["Tertunda", "Sedang Diproses", "Selesai", "Dibatalkan"]
        current_index = status_options.index(o['status']) if o['status'] in status_options else 0
        new_status = st.selectbox("Ubah status", status_options, index=current_index, key=f"status_{o['id']}")
        
        if st.button("Perbarui status", key=f"update_status_{o['id']}"):
            update_order_status(o['id'], new_status)
            st.success("Status berhasil diperbarui")
            st.rerun()
        st.markdown("---")


def admin_reviews():
    # ... (Fungsi ini tidak berubah)
    st.markdown("### Ulasan")
    reviews = get_all_reviews()
    for r in reviews:
        st.write(f"{r['dibuat_pada']} | {r['nama_pengguna']} | {r['nama_menu']} | Peringkat: {r['penilaian']}")
        st.write(f"> {r['teks_ulasan']}")
        st.markdown("---")

def manage_users():
    # ... (Fungsi ini tidak berubah)
    st.markdown("### Manajemen Pengguna")
    users_data = read_users()
    df_users = pd.DataFrame(users_data, columns=["ID", "Nama Pengguna", "Peran"])
    st.dataframe(df_users, use_container_width=True)


# --- HALAMAN-HALAMAN TUGAS BARU ---

def page_admin_add_menu():
    st.subheader("Tambah Menu Baru")
    with st.form("new_menu_form"):
        name = st.text_input("Nama Menu")
        category = st.selectbox("Kategori", ["Makanan", "Minuman", "Dessert"])
        desc = st.text_area("Deskripsi")
        price = st.number_input("Harga", min_value=0.0, value=20000.0)
        img = st.file_uploader("Gambar (opsional)", type=['png', 'jpg', 'jpeg'])
        submitted = st.form_submit_button("Buat Menu Baru")

        if submitted:
            image_url = None
            if img is not None:
                bytes_data = img.getvalue()
                filename = f"{int(datetime.now().timestamp())}_{img.name}"
                try:
                    image_url = upload_image_to_storage(bytes_data, filename)
                except Exception as e:
                    st.error(f"Gagal mengunggah gambar: {e}")
            create_menu_item(name, category, desc, price, image_url)
            st.success("Menu berhasil dibuat")
            st.session_state['page'] = 'admin_dashboard'
            st.rerun()

    if st.button("Batal"):
        st.session_state['page'] = 'admin_dashboard'
        st.rerun()

def page_admin_add_promo():
    st.subheader("Buat Promo Baru")
    with st.form("new_promo_form"):
        code = st.text_input("Kode Promo")
        amt = st.number_input("Nominal Diskon (Rp)", min_value=0.0, value=5000.0)
        active = st.checkbox("Aktif", value=True)
        submitted = st.form_submit_button("Buat Promo")

        if submitted:
            create_promo(code, amt, active)
            st.success("Promo berhasil dibuat")
            st.session_state['page'] = 'admin_dashboard'
            st.rerun()
    
    if st.button("Batal"):
        st.session_state['page'] = 'admin_dashboard'
        st.rerun()

def page_admin_edit_menu():
    st.subheader("Edit Menu")
    it = st.session_state.get('edit_item')
    if not it:
        st.error("Tidak ada item yang dipilih untuk diedit.")
        if st.button("Kembali ke Dasbor"):
            st.session_state['page'] = 'admin_dashboard'
            st.rerun()
        return
    
    with st.form("edit_menu_form"):
        name = st.text_input("Nama Menu", value=it.get('nama', ''))
        categories = ["Makanan", "Minuman", "Dessert"]
        current_category = it.get('kategori', 'Makanan')
        cat_index = categories.index(current_category) if current_category in categories else 0
        category = st.selectbox("Kategori", categories, index=cat_index)
        desc = st.text_area("Deskripsi", value=it.get('deskripsi', ''))
        price = st.number_input("Harga", min_value=0.0, value=float(it.get('harga', 0.0)))
        img = st.file_uploader("Ganti Gambar (opsional)", type=['png','jpg','jpeg'])
        submitted = st.form_submit_button("Simpan Perubahan")

        if submitted:
            image_url = it.get('url_gambar')
            if img:
                try:
                    filename = f"{int(datetime.now().timestamp())}_{img.name}"
                    image_url = upload_image_to_storage(img.getvalue(), filename)
                except Exception as e:
                    st.error(f"Gagal mengunggah gambar: {e}")
            update_menu_item(it['id'], name, category, desc, price, image_url)
            st.success("Menu berhasil diperbarui")
            del st.session_state['edit_item']
            st.session_state['page'] = 'admin_dashboard'
            st.rerun()

    if st.button("Batal"):
        del st.session_state['edit_item']
        st.session_state['page'] = 'admin_dashboard'
        st.rerun()

