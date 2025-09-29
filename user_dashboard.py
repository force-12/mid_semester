"""
Dasbor pengguna untuk aplikasi Caffe Dehh
Berisi tampilan menu, keranjang, riwayat pesanan, dan fitur favorit.
"""

import streamlit as st
from database import (
    get_all_menu, 
    add_to_favorites, 
    remove_from_favorites, 
    get_favorite_menus,
    get_order_by_id,
    submit_review,
    get_reviews_for_menu
)
from ui import show_cart, show_user_orders, go
from datetime import datetime # Diperlukan untuk formatting tanggal jika tidak ada di ui.py

# --- FUNGSI HALAMAN UTAMA ---

def show_user_dashboard():
    """Menampilkan halaman utama pengguna dengan navigasi berbasis header dan tabs."""
    user = st.session_state.get('user', {})
    
    # Header dengan sambutan di kiri dan tombol keluar di kanan
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### Selamat Datang, {user.get('nama_pengguna', 'Pelanggan')}!")
    with col2:
        if st.button("Keluar", key='user_logout', use_container_width=True):
            st.session_state.clear()
            st.session_state['page'] = 'login'
            st.rerun()

    st.markdown("---")

    # Navigasi utama menggunakan komponen st.tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Menu", "Keranjang", "Pesanan Saya", "Favorit", "Profil"])

    with tab1:
        page_menu()
    with tab2:
        # show_cart diimpor dari ui.py
        show_cart()
    with tab3:
        # show_user_orders diimpor dari ui.py
        show_user_orders()
    with tab4:
        page_favorites()
    with tab5:
        page_user_profile()
        
# --- FUNGSI DETAIL HALAMAN (Diekspor ke main.py jika diperlukan) ---

def page_menu():
    # CSS khusus agar teks selectbox kategori selalu hitam dan terlihat
    st.markdown("""
        <style>
        /* Paksa warna teks value selectbox kategori agar selalu hitam (untuk berbagai versi Streamlit/react-select) */
        div[data-testid="stSelectbox"] .css-1dimb5e-singleValue,
        div[data-testid="stSelectbox"] .css-1wa3eu0-placeholder,
        div[data-testid="stSelectbox"] [data-baseweb="select"] [role="button"] span {
            color: #000 !important;
        }
        /* Untuk dropdown option */
        div[data-testid="stSelectbox"] [data-baseweb="select"] [role="option"] {
            color: #000 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("## 📃 Daftar Menu Caffe Dehh")
    
    # Filter dan Pencarian
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_term = st.text_input("Cari Menu", placeholder="Ketik nama makanan atau minuman...")
    with col_filter:
        category_filter = st.selectbox("Filter Kategori", ["Semua", "Makanan", "Minuman", "Dessert"], label_visibility="visible")

    user_id = st.session_state['user']['id']
    all_items = get_all_menu(search=search_term, user_id=user_id)

    # Filter berdasarkan kategori
    if category_filter != "Semua":
        items = [item for item in all_items if item['kategori'] == category_filter]
    else:
        items = all_items

    if not items:
        st.info("Menu tidak ditemukan.")
        return

    # Tampilkan menu dalam layout kolom yang menarik
    st.markdown("---")
    
    # Menggunakan kolom responsif (3 kolom di layar lebar)
    cols = st.columns(3)
    
    for i, item in enumerate(items):
        with cols[i % 3]:
            # Menggunakan st.container untuk efek kartu menu
            with st.container():
                st.markdown("<div class='stContainer' style='padding: 10px; border: 1px solid #D3A58E;'>", unsafe_allow_html=True)
                
                # Gambar menu
                if item['url_gambar']:
                    # DIPERBAIKI: Mengganti use_column_width dengan use_container_width
                    st.image(item['url_gambar'], use_container_width=True, caption=item['nama'])
                else:
                    st.markdown("<div style='height: 150px; background-color: #D3A58E; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;'>[Gambar Menu]</div>", unsafe_allow_html=True)
                
                # Detail
                st.markdown(f"**{item['nama']}**")
                st.markdown(f"*{item['kategori']}* | **Rp {int(item['harga']):,}**")
                
                # Ketersediaan dan Rating
                status_icon = "✅" if item.get('tersedia', True) else "🚫"
                rating_text = f"⭐ {item['rating_rata_rata']:.1f} ({item['jumlah_ulasan']} ulasan)"

                st.caption(f"{status_icon} | {rating_text}")

                # Aksi
                col_fav, col_add = st.columns([1, 2])
                
                with col_fav:
                    is_favorite = item.get('is_favorite', False)
                    fav_icon = "❤️" if is_favorite else "🤍"
                    fav_key = f"fav_{item['id']}_{i}"

                    if st.button(fav_icon, key=fav_key, use_container_width=True, help="Tambahkan/Hapus dari Favorit"):
                        if is_favorite:
                            remove_from_favorites(user_id, item['id'])
                            st.toast("💔 Dihapus dari favorit.")
                        else:
                            add_to_favorites(user_id, item['id'])
                            st.toast("❤️ Ditambahkan ke favorit!")
                        st.rerun() # Diperbaiki: Menggunakan st.rerun()
                
                with col_add:
                    # Input kuantitas dan tombol Add to Cart
                    qty = st.number_input("Jumlah", min_value=1, value=1, key=f"qty_{item['id']}_{i}", label_visibility="collapsed")
                    if st.button("➕ Tambah", key=f"add_{item['id']}_{i}", use_container_width=True, disabled=not item.get('tersedia', True)):
                        # Menggunakan fungsi add_to_cart dari ui.py
                        from ui import add_to_cart
                        add_to_cart(item['id'], qty)
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("") # Spasi
                
# --- FUNGSI HALAMAN FAVORIT ---

def page_favorites():
    st.markdown("## ❤️ Menu Favorit Anda")
    user_id = st.session_state['user']['id']
    favorite_items = get_favorite_menus(user_id)

    if not favorite_items:
        st.info("Anda belum memiliki menu favorit. Jelajahi menu untuk menambahkannya!")
        return

    st.markdown("---")
    
    # Tampilkan dalam kartu 2 kolom
    cols = st.columns(2)
    
    for i, item in enumerate(favorite_items):
        with cols[i % 2]:
            with st.container():
                st.markdown("<div class='stContainer' style='padding: 15px; border: 2px solid #D3A58E;'>", unsafe_allow_html=True)
                
                col_img, col_detail, col_action = st.columns([1, 3, 1])
                
                with col_img:
                    if item['url_gambar']:
                        st.image(item['url_gambar'], width=80)
                
                with col_detail:
                    st.markdown(f"**{item['nama']}**")
                    st.markdown(f"**Rp {int(item['harga']):,}**")
                    st.caption(f"⭐ {item['rating_rata_rata']:.1f} | Kategori: {item['kategori']}")
                
                with col_action:
                    if st.button("🗑️", key=f"remove_fav_{item['id']}_{i}", help="Hapus dari Favorit", use_container_width=True):
                        remove_from_favorites(user_id, item['id'])
                        st.toast("💔 Dihapus dari favorit.")
                        st.rerun() # Diperbaiki: Menggunakan st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("")

# --- FUNGSI HALAMAN REVIEW ---
# Fungsi ini diekspor ke main.py
def page_review():
    st.markdown("## ⭐ Beri Ulasan Anda")
    order_id = st.session_state.get('review_target_order')

    if not order_id:
        st.error("Tidak ada pesanan yang dipilih untuk diulas.")
        if st.button("Kembali ke Pesanan Saya"):
            go('user_dashboard')
            st.rerun() # Diperbaiki: Menggunakan st.rerun()
        return

    order = get_order_by_id(order_id)
    if not order:
        st.error("Detail pesanan tidak ditemukan.")
        if st.button("Kembali"):
            del st.session_state['review_target_order']
            go('user_dashboard')
            st.rerun() # Diperbaiki: Menggunakan st.rerun()
        return

    st.info(f"Anda mengulas Pesanan **#{order_id}** yang terdiri dari:")
    
    # Mengambil semua item dalam pesanan untuk diulas
    reviewable_items = []
    # Memastikan 'item' adalah list/array sebelum iterasi
    if isinstance(order.get('item'), list):
        for item_data in order['item']:
            menu_id = item_data.get('id_menu')
            nama_menu = item_data.get('nama', 'Menu Tidak Dikenal')
            if menu_id:
                reviewable_items.append({'id': menu_id, 'nama': nama_menu})

    if not reviewable_items:
        st.warning("Pesanan ini tidak memiliki item yang dapat diulas.")
        if st.button("Selesai Ulasan"):
            del st.session_state['review_target_order']
            go('user_dashboard')
            st.rerun() # Diperbaiki: Menggunakan st.rerun()
        return

    # Formulir Ulasan
    with st.container():
        st.markdown("<div class='stContainer' style='padding: 20px;'>", unsafe_allow_html=True)
        st.subheader("Ulas Item")
        
        # Menggunakan session state untuk melacak item yang sudah diulas
        if 'reviewed_items' not in st.session_state:
            st.session_state['reviewed_items'] = set()

        for item in reviewable_items:
            # Periksa apakah item ini sudah diulas dalam sesi ini
            if item['id'] in st.session_state['reviewed_items']:
                st.markdown(f"**{item['nama']}** (✅ Sudah Diulas)")
                continue

            st.markdown(f"---")
            st.markdown(f"#### {item['nama']}")
            
            with st.form(f"review_form_{item['id']}", clear_on_submit=True):
                rating = st.slider("Peringkat (1-5 Bintang)", min_value=1, max_value=5, value=5, key=f"rating_{item['id']}")
                review_text = st.text_area("Teks Ulasan (Opsional)", key=f"text_{item['id']}", placeholder="Bagaimana pengalaman Anda dengan menu ini?")
                
                col_submit, col_placeholder = st.columns([1, 2])
                with col_submit:
                    submitted = st.form_submit_button("Kirim Ulasan")

                if submitted:
                    user_id = st.session_state['user']['id']
                    try:
                        submit_review(user_id, item['id'], rating, review_text)
                        st.success(f"Ulasan untuk {item['nama']} berhasil dikirim!")
                        st.session_state['reviewed_items'].add(item['id'])
                        st.rerun() # Diperbaiki: Menggunakan st.rerun()
                    except Exception as e:
                        st.error(f"Gagal mengirim ulasan: {e}")

        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("Selesai & Kembali ke Pesanan Saya", key='finish_review_btn'):
        if 'review_target_order' in st.session_state:
            del st.session_state['review_target_order']
        if 'reviewed_items' in st.session_state:
            del st.session_state['reviewed_items']
        go('user_dashboard')
        st.rerun() # Diperbaiki: Menggunakan st.rerun()

# --- FUNGSI HALAMAN PROFIL PENGGUNA ---
# Fungsi ini diekspor ke main.py
def page_user_profile():
    st.markdown("## 👤 Profil Saya")
    user = st.session_state.get('user', {})
    
    if not user:
        st.error("Anda harus masuk untuk melihat profil.")
        return
    
    st.markdown(f"""
        <div class='stContainer' style='padding: 20px; text-align: center;'>
            <h3 style='color: #A0522D;'>{user.get('nama_pengguna', 'N/A').upper()}</h3>
            <p style='font-weight: bold;'>Peran: <span style='color: green;'>{user.get('peran', 'N/A').capitalize()}</span></p>
            <p>ID Pengguna: <code>{user.get('id')}</code></p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Aksi Akun")
    
    col_password, col_logout = st.columns(2)
    
    with col_password:
        if st.button("Ubah Kata Sandi", use_container_width=True):
            # Mengatur state untuk navigasi ke reset password di auth.py
            st.session_state['page'] = 'forgot_password' 
            st.session_state['reset_step'] = 2 
            st.session_state['username_to_reset'] = user.get('nama_pengguna')
            st.rerun() # Diperbaiki: Menggunakan st.rerun()

    with col_logout:
        if st.button("Keluar Akun", use_container_width=True):
            st.session_state.clear()
            st.session_state['page'] = 'login'
            st.rerun() # Diperbaiki: Menggunakan st.rerun()

    st.markdown("---")
    st.caption("Fungsi Profil memungkinkan Anda untuk mengelola detail akun Anda.")

