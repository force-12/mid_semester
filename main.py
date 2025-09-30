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
from datetime import datetime

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
        show_cart()
    with tab3:
        show_user_orders()
    with tab4:
        page_favorites()
    with tab5:
        page_user_profile()
        
# --- FUNGSI DETAIL HALAMAN ---

def page_menu():
    """Menampilkan menu dengan ukuran gambar yang konsisten"""
    # CSS khusus untuk memastikan ukuran gambar konsisten
    st.markdown("""
        <style>
        /* Kontainer menu card dengan ukuran tetap */
        .menu-card {
            border: 1px solid #D3A58E;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            background-color: white;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        
        /* Container gambar dengan aspect ratio tetap */
        .menu-image-container {
            width: 100%;
            height: 200px;
            overflow: hidden;
            border-radius: 8px;
            margin-bottom: 10px;
            background-color: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .menu-image-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        /* Placeholder untuk gambar kosong */
        .menu-placeholder {
            width: 100%;
            height: 200px;
            background-color: #D3A58E;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 1.2em;
        }
        
        /* Detail menu */
        .menu-details {
            flex-grow: 1;
            margin-bottom: 10px;
        }
        
        /* Paksa warna teks selectbox agar hitam */
        div[data-testid="stSelectbox"] [data-baseweb="select"] span,
        div[data-testid="stSelectbox"] [role="button"] span {
            color: #000 !important;
            font-weight: 600 !important;
        }
        
        div[data-testid="stSelectbox"] [role="option"] {
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
        category_filter = st.selectbox("Filter Kategori", ["Semua", "Makanan", "Minuman", "Dessert"])

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

    st.markdown("---")
    
    # Tampilkan menu dalam grid 3 kolom
    for row_start in range(0, len(items), 3):
        cols = st.columns(3)
        
        for col_idx in range(3):
            item_idx = row_start + col_idx
            
            if item_idx >= len(items):
                break
                
            item = items[item_idx]
            
            with cols[col_idx]:
                # Mulai container untuk card
                st.markdown('<div class="menu-card">', unsafe_allow_html=True)
                
                # Gambar dengan ukuran tetap
                if item['url_gambar']:
                    st.markdown(f'''
                        <div class="menu-image-container">
                            <img src="{item['url_gambar']}" alt="{item['nama']}">
                        </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('''
                        <div class="menu-placeholder">
                            [Gambar Menu]
                        </div>
                    ''', unsafe_allow_html=True)
                
                # Detail menu
                st.markdown('<div class="menu-details">', unsafe_allow_html=True)
                st.markdown(f"**{item['nama']}**")
                st.markdown(f"*{item['kategori']}* | **Rp {int(item['harga']):,}**")
                
                # Status dan Rating
                status_icon = "✅" if item.get('tersedia', True) else "🚫"
                rating_text = f"⭐ {item['rating_rata_rata']:.1f} ({item['jumlah_ulasan']} ulasan)"
                st.caption(f"{status_icon} | {rating_text}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Tombol Aksi
                col_fav, col_qty, col_add = st.columns([1, 1, 2])
                
                with col_fav:
                    is_favorite = item.get('is_favorite', False)
                    fav_icon = "❤️" if is_favorite else "🤍"
                    
                    if st.button(fav_icon, key=f"fav_{item['id']}_{item_idx}", 
                                use_container_width=True, help="Favorit"):
                        if is_favorite:
                            remove_from_favorites(user_id, item['id'])
                            st.toast("💔 Dihapus dari favorit.")
                        else:
                            add_to_favorites(user_id, item['id'])
                            st.toast("❤️ Ditambahkan ke favorit!")
                        st.rerun()
                
                with col_qty:
                    qty = st.number_input("", min_value=1, value=1, 
                                         key=f"qty_{item['id']}_{item_idx}",
                                         label_visibility="collapsed")
                
                with col_add:
                    if st.button("➕ Tambah", key=f"add_{item['id']}_{item_idx}", 
                                use_container_width=True, 
                                disabled=not item.get('tersedia', True)):
                        from ui import add_to_cart
                        add_to_cart(item['id'], qty)
                
                # Tutup card
                st.markdown('</div>', unsafe_allow_html=True)

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
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("")

# --- FUNGSI HALAMAN REVIEW ---

def page_review():
    st.markdown("## ⭐ Beri Ulasan Anda")
    order_id = st.session_state.get('review_target_order')

    if not order_id:
        st.error("Tidak ada pesanan yang dipilih untuk diulas.")
        if st.button("Kembali ke Pesanan Saya"):
            go('user_dashboard')
            st.rerun()
        return

    order = get_order_by_id(order_id)
    if not order:
        st.error("Detail pesanan tidak ditemukan.")
        if st.button("Kembali"):
            del st.session_state['review_target_order']
            go('user_dashboard')
            st.rerun()
        return

    st.info(f"Anda mengulas Pesanan **#{order_id}** yang terdiri dari:")
    
    # Mengambil semua item dalam pesanan untuk diulas
    reviewable_items = []
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
            st.rerun()
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
                        st.rerun()
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
        st.rerun()

# --- FUNGSI HALAMAN PROFIL PENGGUNA ---

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
            st.session_state['page'] = 'forgot_password' 
            st.session_state['reset_step'] = 2 
            st.session_state['username_to_reset'] = user.get('nama_pengguna')
            st.rerun()

    with col_logout:
        if st.button("Keluar Akun", use_container_width=True):
            st.session_state.clear()
            st.session_state['page'] = 'login'
            st.rerun()

    st.markdown("---")
    st.caption("Fungsi Profil memungkinkan Anda untuk mengelola detail akun Anda.")