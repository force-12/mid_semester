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

# --- FUNGSI UTAMA DASBOR ---

def show_admin_dashboard():
    st.title("🛡️ Dasbor Admin")
    user = st.session_state.get('user', {})
    
    # Header dengan sambutan di kiri dan tombol keluar di kanan
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader(f"Selamat datang, Admin {user.get('nama_pengguna', 'Unknown')}!")
    with col2:
        if st.button("Keluar", key='admin_logout', use_container_width=True):
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

# --- TAB ANALITIK ---

def show_analytics_tab():
    st.markdown("### Analitik Kinerja Kafe")
    
    sales_data = get_sales_data()
    df_sales = pd.DataFrame(sales_data, columns=['tanggal', 'total_pendapatan'])
    
    # Menampilkan metrik utama
    col1, col2, col3 = st.columns(3)
    
    total_sales = df_sales['total_pendapatan'].sum() if not df_sales.empty else 0
    col1.metric("💰 Total Pendapatan", f"Rp {int(total_sales):,}")
    
    orders = list_orders()
    completed_orders = len([o for o in orders if o['status'] == 'Selesai'])
    col2.metric("📦 Pesanan Selesai", completed_orders)

    menu_count = len(get_all_menu())
    col3.metric("🍔 Jumlah Menu", menu_count)
    
    st.markdown("---")

    st.markdown("#### Tren Pendapatan Harian")
    if not df_sales.empty:
        df_sales['tanggal'] = pd.to_datetime(df_sales['tanggal'])
        df_sales = df_sales.set_index('tanggal')
        st.line_chart(df_sales)
    else:
        st.info("Belum ada data penjualan yang selesai untuk ditampilkan.")

    st.markdown("#### Item Menu Terlaris (Berdasarkan Kuantitas)")
    top_items = get_top_selling_items()
    if top_items:
        df_top_items = pd.DataFrame(top_items, columns=['nama_menu', 'jumlah_terjual'])
        df_top_items = df_top_items.set_index('nama_menu')
        st.bar_chart(df_top_items)
    else:
        st.info("Belum ada data item terlaris.")

# --- TAB MANAJEMEN MENU ---

def manage_menu():
    st.markdown("### ☕ Manajemen Menu")
    
    col_add, col_info = st.columns([1, 3])
    with col_add:
        if st.button("➕ Tambah Menu Baru", use_container_width=True):
            st.session_state['page'] = 'admin_add_menu'
            st.rerun()

    st.markdown("---")
    st.markdown("#### Daftar Menu")
    items = get_all_menu()
    
    # Menggunakan tata letak kolom yang responsif untuk setiap item
    for it in items:
        # Menggunakan st.container untuk efek kartu
        with st.container():
            # Class kustom untuk kartu menu yang lebih jelas
            status_color = "#38761d" if it.get('tersedia', True) else "#cc0000"
            status_text = "✅ Tersedia" if it.get('tersedia', True) else "🚫 Habis"

            # Menggunakan columns untuk detail dan aksi
            col_img, col_detail, col_actions = st.columns([1, 4, 2])

            with col_img:
                # Tampilkan gambar atau placeholder
                if it['url_gambar']:
                    st.image(it['url_gambar'], width=100)
                else:
                    st.markdown("<div style='height: 100px; width: 100px; background-color: #ccc; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #666; font-size: 0.8em; text-align: center;'>Gambar Tidak Ada</div>", unsafe_allow_html=True)
            
            with col_detail:
                st.markdown(f"**{it['nama']}**")
                st.markdown(f"*{it['kategori']}* | **Rp {int(it['harga']):,}**")
                st.caption(f"Status: <span style='color: {status_color}; font-weight: bold;'>{status_text}</span>", unsafe_allow_html=True)
                if it['deskripsi']:
                    st.caption(it['deskripsi'])
            
            with col_actions:
                # Tombol Aksi
                new_status = not it.get('tersedia', True)
                status_btn_text = "Set Habis" if not new_status else "Set Tersedia"
                
                if st.button(status_btn_text, key=f"stock_{it['id']}", use_container_width=True):
                    update_menu_availability(it['id'], new_status)
                    st.rerun()

                if st.button("✏️ Edit", key=f"edit_{it['id']}", use_container_width=True):
                    st.session_state['edit_item'] = it
                    st.session_state['page'] = 'admin_edit_menu'
                    st.rerun()

                if st.button("🗑️ Hapus", key=f"delete_{it['id']}", use_container_width=True):
                    # Konfirmasi penghapusan (menggunakan tampilan modal sederhana/peringatan)
                    if st.warning(f"Yakin ingin menghapus {it['nama']}?"):
                         delete_menu_item(it['id'])
                         st.success("Menu dihapus")
                         st.rerun()

        st.markdown("---") # Garis pemisah antar kartu

# --- TAB MANAJEMEN PROMO ---

def manage_promo():
    st.markdown("### 🎉 Manajemen Promo")
    
    if st.button("➕ Buat Promo Baru", key='btn_add_promo'):
        st.session_state['page'] = 'admin_add_promo'
        st.rerun()

    st.markdown("---")
    st.markdown("#### Daftar Kode Promo")
    promos = list_promos()
    
    # Tabel yang lebih rapi
    promo_data = [
        {
            "Kode": p.get('kode'), 
            "Diskon (Rp)": f"Rp {int(p.get('jumlah_diskon',0)):,}", 
            "Aktif": "✅ Ya" if p.get('aktif') else "❌ Tidak",
            "ID": p.get('id')
        } for p in promos
    ]
    df_promo = pd.DataFrame(promo_data)

    if not df_promo.empty:
        st.dataframe(df_promo.drop(columns=['ID']), use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada promo.")
        
    st.markdown("---")
    # Bagian Aksi (Edit/Hapus) - Menggunakan form terpisah untuk aksi
    st.subheader("Aksi Promo")
    # DIPERBAIKI: Menggunakan 'kode' dan 'id' (huruf kecil) yang sesuai dengan data dari database
    promo_ids = {p['kode']: p['id'] for p in promos}
    
    if promos:
        selected_code = st.selectbox("Pilih Kode Promo untuk Aksi", list(promo_ids.keys()), key='promo_selector')
        selected_promo = next((p for p in promos if p['kode'] == selected_code), None)
        
        if selected_promo:
            col_toggle, col_delete = st.columns(2)
            
            # Toggle Status
            with col_toggle:
                new_status = not selected_promo['aktif']
                if st.button(f"{'Deaktifkan' if selected_promo['aktif'] else 'Aktifkan'} {selected_promo['kode']}", key=f"toggle_promo_{selected_promo['id']}", use_container_width=True):
                    update_promo(selected_promo['id'], selected_promo['kode'], selected_promo['jumlah_diskon'], new_status)
                    st.success("Status promo diperbarui.")
                    st.rerun()
            
            # Delete Promo
            with col_delete:
                if st.button("🗑️ Hapus Promo", key=f"delete_promo_{selected_promo['id']}", use_container_width=True):
                    delete_promo(selected_promo['id'])
                    st.success(f"Promo {selected_promo['kode']} dihapus.")
                    st.rerun()
    

# --- TAB PESANAN ---

def admin_orders():
    st.markdown("### 📦 Daftar Pesanan Masuk")
    orders = list_orders()
    
    if not orders:
        st.info("Belum ada pesanan baru.")
        return

    for o in orders:
        # Menggunakan kontainer dengan warna status yang lebih baik
        status = o['status']
        if status == 'Selesai':
            card_style = "border-left: 5px solid green;"
        elif status == 'Sedang Diproses':
            card_style = "border-left: 5px solid orange;"
        elif status == 'Dibatalkan':
            card_style = "border-left: 5px solid red;"
        else:
            card_style = "border-left: 5px solid blue;" # Tertunda
        
        with st.container():
            st.markdown(f"<div class='stContainer' style='{card_style}'>", unsafe_allow_html=True)
            
            st.markdown(f"#### Pesanan #{o['id']} ({status})")
            
            col_info, col_payment = st.columns(2)
            with col_info:
                st.markdown(f"**Pengguna:** ID {o['id_pengguna']}")
                st.markdown(f"**Total:** Rp {int(o['total']):,}")
            with col_payment:
                st.markdown(f"**Pembayaran:** {o['metode_pembayaran']}")
                # Pastikan datetime bisa diakses (dibuat_pada adalah objek datetime)
                st.markdown(f"**Dibuat:** {o['dibuat_pada'].strftime('%d-%m-%Y %H:%M')}") 
            
            with st.expander("Lihat Detail Item"):
                items = o.get('item', [])
                for it in items:
                    st.write(f"- {it.get('nama','N/A')} x {it.get('qty',0)}")
            
            st.markdown("---")
            
            # Aksi Status
            status_options = ["Tertunda", "Sedang Diproses", "Selesai", "Dibatalkan"]
            current_index = status_options.index(o['status']) if o['status'] in status_options else 0
            
            col_status, col_update = st.columns([3, 1])
            with col_status:
                new_status = st.selectbox("Ubah Status", status_options, index=current_index, key=f"status_{o['id']}")
            
            with col_update:
                st.markdown("<div style='margin-top: 25px;'>", unsafe_allow_html=True)
                if st.button("Perbarui Status", key=f"update_status_{o['id']}", use_container_width=True):
                    update_order_status(o['id'], new_status)
                    st.success("Status berhasil diperbarui")
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("") # Spasi antar pesanan


# --- TAB ULASAN ---

def admin_reviews():
    st.markdown("### ⭐ Ulasan Pelanggan")
    reviews = get_all_reviews()

    if not reviews:
        st.info("Belum ada ulasan yang masuk.")
        return

    for r in reviews:
        # Menghitung bintang
        stars = "⭐" * r['penilaian']
        
        with st.container():
            st.markdown(f"<div class='stContainer'>", unsafe_allow_html=True)
            col_meta, col_rating = st.columns([4, 1])
            
            with col_meta:
                st.markdown(f"**{r['nama_pengguna']}** | Menu: *{r['nama_menu']}*")
                # Pastikan datetime bisa diakses (dibuat_pada adalah objek datetime)
                st.caption(f"Tanggal: {r['dibuat_pada']}") 
            
            with col_rating:
                st.markdown(f"<h3 style='color: gold;'>{stars}</h3>", unsafe_allow_html=True)
            
            st.info(f"**Ulasan:** {r['teks_ulasan']}")
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")


# --- TAB MANAJEMEN PENGGUNA ---

def manage_users():
    st.markdown("### 👥 Manajemen Pengguna")
    users_data = read_users()
    
    # Mengubah tampilan DataFrame menjadi tabel yang lebih bagus
    df_users = pd.DataFrame(users_data, columns=["ID", "Nama Pengguna", "Peran"])
    st.dataframe(df_users, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Ubah Peran Pengguna")
    
    usernames = df_users['Nama Pengguna'].tolist()
    if usernames:
        col_user, col_role, col_action = st.columns([2, 2, 1])
        
        with col_user:
            selected_user = st.selectbox("Pilih Nama Pengguna", usernames, key='user_role_select')
        
        # Ambil peran saat ini untuk nilai default
        current_role = df_users[df_users['Nama Pengguna'] == selected_user]['Peran'].iloc[0] if selected_user else 'user'
        roles = ["user", "admin"]
        role_index = roles.index(current_role) if current_role in roles else 0
        
        with col_role:
            new_role = st.selectbox("Pilih Peran Baru", roles, index=role_index, key='new_role_select')
        
        with col_action:
            st.markdown("<div style='margin-top: 25px;'>", unsafe_allow_html=True)
            if st.button("Perbarui Peran", key='update_role_btn', use_container_width=True):
                if selected_user and new_role:
                    update_user_role(selected_user, new_role)
                    st.success(f"Peran pengguna {selected_user} berhasil diubah menjadi {new_role}.")
                    st.rerun()
                else:
                    st.error("Pilih pengguna dan peran.")
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("Hapus Pengguna")
        col_delete, _ = st.columns([2, 3])
        with col_delete:
            if st.button("🗑️ Hapus Pengguna Terpilih", key='delete_user_btn', use_container_width=True):
                if selected_user:
                    # Implementasi konfirmasi sederhana sebelum penghapusan
                    st.error(f"⚠️ **PERINGATAN!** Anda akan menghapus pengguna **{selected_user}**. Konfirmasi:")
                    if st.button("Ya, Hapus Sekarang", key='confirm_delete_user'):
                        delete_user(selected_user)
                        st.success(f"Pengguna {selected_user} berhasil dihapus.")
                        st.rerun()
                else:
                    st.warning("Pilih pengguna untuk dihapus.")


# --- HALAMAN-HALAMAN TUGAS BARU (Formulir yang lebih bersih) ---

def page_admin_add_menu():
    st.subheader("➕ Tambah Menu Baru")
    
    with st.container():
        st.markdown("<div class='stContainer' style='padding: 20px;'>", unsafe_allow_html=True)
        with st.form("new_menu_form", clear_on_submit=True):
            name = st.text_input("Nama Menu", placeholder="Nama item (Contoh: Espresso)")
            category = st.selectbox("Kategori", ["Makanan", "Minuman", "Dessert"])
            desc = st.text_area("Deskripsi", placeholder="Jelaskan item menu secara singkat")
            price = st.number_input("Harga (Rp)", min_value=0, value=20000)
            img = st.file_uploader("Gambar (opsional)", type=['png', 'jpg', 'jpeg'])
            submitted = st.form_submit_button("Buat Menu Baru")

            if submitted:
                if not name or not price:
                    st.error("Nama Menu dan Harga wajib diisi.")
                    return

                image_url = None
                if img is not None:
                    bytes_data = img.getvalue()
                    filename = f"menu_{int(datetime.now().timestamp())}_{img.name}"
                    try:
                        image_url = upload_image_to_storage(bytes_data, filename)
                        st.toast("Gambar berhasil diunggah!")
                    except Exception as e:
                        st.error(f"Gagal mengunggah gambar: {e}")
                
                create_menu_item(name, category, desc, price, image_url)
                st.success("Menu berhasil dibuat!")
                st.session_state['page'] = 'admin_dashboard'
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("← Kembali ke Dasbor"):
        st.session_state['page'] = 'admin_dashboard'
        st.rerun()

def page_admin_add_promo():
    st.subheader("🎉 Buat Promo Baru")
    
    with st.container():
        st.markdown("<div class='stContainer' style='padding: 20px;'>", unsafe_allow_html=True)
        with st.form("new_promo_form", clear_on_submit=True):
            code = st.text_input("Kode Promo", placeholder="Contoh: CAFFEDEHH25")
            amt = st.number_input("Nominal Diskon (Rp)", min_value=0, value=5000)
            active = st.checkbox("Aktifkan Promo", value=True)
            submitted = st.form_submit_button("Buat Promo")

            if submitted:
                if not code or amt <= 0:
                    st.error("Kode Promo dan Nominal Diskon harus valid.")
                    return
                try:
                    create_promo(code, amt, active)
                    st.success("Promo berhasil dibuat!")
                    st.session_state['page'] = 'admin_dashboard'
                    st.rerun()
                except Exception as e:
                    if "unique constraint" in str(e).lower():
                        st.error("Kode promo sudah ada. Gunakan kode lain.")
                    else:
                         st.error(f"Gagal membuat promo: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("← Kembali ke Dasbor"):
        st.session_state['page'] = 'admin_dashboard'
        st.rerun()

def page_admin_edit_menu():
    st.subheader("✏️ Edit Menu")
    it = st.session_state.get('edit_item')
    if not it:
        st.error("Tidak ada item yang dipilih untuk diedit.")
        if st.button("Kembali ke Dasbor"):
            st.session_state['page'] = 'admin_dashboard'
            st.rerun()
        return
    
    st.info(f"Anda sedang mengedit: **{it.get('nama')}**")

    with st.container():
        st.markdown("<div class='stContainer' style='padding: 20px;'>", unsafe_allow_html=True)
        with st.form("edit_menu_form"):
            col_left, col_right = st.columns(2)
            
            with col_left:
                name = st.text_input("Nama Menu", value=it.get('nama', ''))
                categories = ["Makanan", "Minuman", "Dessert"]
                current_category = it.get('kategori', 'Makanan')
                cat_index = categories.index(current_category) if current_category in categories else 0
                category = st.selectbox("Kategori", categories, index=cat_index)
                price = st.number_input("Harga (Rp)", min_value=0.0, value=float(it.get('harga', 0.0)))
            
            with col_right:
                desc = st.text_area("Deskripsi", value=it.get('deskripsi', ''), height=150)
                # Tampilkan gambar saat ini
                if it.get('url_gambar'):
                    st.caption("Gambar Saat Ini:")
                    st.image(it['url_gambar'], width=100)
                img = st.file_uploader("Ganti Gambar (opsional)", type=['png','jpg','jpeg'])
            
            submitted = st.form_submit_button("Simpan Perubahan")

            if submitted:
                image_url = it.get('url_gambar')
                if img:
                    try:
                        filename = f"menu_{int(datetime.now().timestamp())}_{img.name}"
                        image_url = upload_image_to_storage(img.getvalue(), filename)
                        st.toast("Gambar baru berhasil diunggah!")
                    except Exception as e:
                        st.error(f"Gagal mengunggah gambar: {e}")
                
                update_menu_item(it['id'], name, category, desc, price, image_url)
                st.success("Menu berhasil diperbarui")
                del st.session_state['edit_item']
                st.session_state['page'] = 'admin_dashboard'
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("← Batal"):
        if 'edit_item' in st.session_state:
            del st.session_state['edit_item']
        st.session_state['page'] = 'admin_dashboard'
        st.rerun()