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
        
# --- FUNGSI DETAIL HALAMAN (Diekspor ke main.py jika diperlukan) ---

def page_menu():
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
            # Header banner dengan nama menu
            st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #D3A58E 0%, #A0522D 100%);
                    color: white;
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                    font-weight: bold;
                    font-size: 1.3em;
                    margin-bottom: 15px;
                '>
                    {item['nama']}
                </div>
            """, unsafe_allow_html=True)
            
            # Gambar menu
            if item['url_gambar']:
                st.markdown(f"""
                    <div style='
                        width: 100%;
                        height: 200px;
                        overflow: hidden;
                        border-radius: 10px;
                        margin-bottom: 15px;
                        border: 2px solid #D3A58E;
                    '>
                        <img src='{item['url_gambar']}' style='
                            width: 100%;
                            height: 100%;
                            object-fit: cover;
                        ' />
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='
                        width: 100%;
                        height: 200px;
                        background: linear-gradient(45deg, #D3A58E 0%, #A0522D 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 10px;
                        color: white;
                        font-weight: bold;
                        margin-bottom: 15px;
                        border: 2px solid #8B4513;
                    '>[Gambar Menu]</div>
                """, unsafe_allow_html=True)
            
            # Kategori dengan badge style
            st.markdown(f"""
                <div style='
                    display: inline-block;
                    background-color: #E6E6FA;
                    color: #4B0082;
                    padding: 5px 12px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    font-weight: bold;
                    margin-bottom: 10px;
                '>
                    {item['kategori']}
                </div>
            """, unsafe_allow_html=True)
            
            # Harga dengan styling yang menonjol
            st.markdown(f"""
                <div style='
                    background: linear-gradient(90deg, #FFE4B5 0%, #FFD700 100%);
                    padding: 12px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 15px 0;
                    border: 2px solid #DAA520;
                '>
                    <span style='
                        color: #8B4513;
                        font-weight: bold;
                        font-size: 1.4em;
                    '>Rp {int(item['harga']):,}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Deskripsi
            if item.get('deskripsi'):
                desc_key = f"desc_expanded_{item['id']}_{i}"
                is_expanded = st.session_state.get(desc_key, False)
                
                if len(item['deskripsi']) > 100:
                    if is_expanded:
                        st.markdown(f"""
                            <div style='
                                background-color: #F8F9FA;
                                padding: 10px;
                                border-radius: 8px;
                                border-left: 3px solid #D3A58E;
                                margin-bottom: 10px;
                            '>
                                <div style='color: #555; font-size: 0.9em; line-height: 1.4;'>
                                    <strong>Deskripsi:</strong> {item['deskripsi']}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("Tampilkan lebih sedikit", key=f"less_{item['id']}_{i}"):
                            st.session_state[desc_key] = False
                            st.rerun()
                    else:
                        st.markdown(f"""
                            <div style='
                                background-color: #F8F9FA;
                                padding: 10px;
                                border-radius: 8px;
                                border-left: 3px solid #D3A58E;
                                margin-bottom: 10px;
                            '>
                                <div style='color: #555; font-size: 0.9em; line-height: 1.4;'>
                                    <strong>Deskripsi:</strong> {item['deskripsi'][:100]}...
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("Selengkapnya", key=f"more_{item['id']}_{i}"):
                            st.session_state[desc_key] = True
                            st.rerun()
                else:
                    st.markdown(f"""
                        <div style='
                            background-color: #F8F9FA;
                            padding: 10px;
                            border-radius: 8px;
                            border-left: 3px solid #D3A58E;
                            margin-bottom: 10px;
                        '>
                            <div style='color: #555; font-size: 0.9em; line-height: 1.4;'>
                                <strong>Deskripsi:</strong> {item['deskripsi']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='
                        background-color: #F8F9FA;
                        padding: 10px;
                        border-radius: 8px;
                        border-left: 3px solid #D3A58E;
                        margin-bottom: 10px;
                    '>
                        <div style='color: #555; font-size: 0.9em;'>
                            <strong>Deskripsi:</strong> -
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Status dan rating
            status_icon = "✅" if item.get('tersedia', True) else "🚫"
            status_text = "Tersedia" if item.get('tersedia', True) else "Habis"
            status_color = "#4CAF50" if item.get('tersedia', True) else "#F44336"
            
            st.markdown(f"""
                <div style='
                    background-color: #F5F5F5;
                    padding: 10px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                    border-left: 4px solid {status_color};
                '>
                    <div style='color: {status_color}; font-weight: bold; margin-bottom: 5px;'>
                        {status_icon} {status_text}
                    </div>
                    <div style='color: #666; font-size: 0.9em;'>
                        ⭐ {item['rating_rata_rata']:.1f} ({item['jumlah_ulasan']} ulasan)
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Area tombol
            col_fav, col_qty, col_add = st.columns([1, 2, 2])
            
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
                    st.rerun()
            
            with col_qty:
                qty = st.number_input("Qty", min_value=1, value=1, key=f"qty_{item['id']}_{i}", label_visibility="collapsed")
            
            with col_add:
                if st.button("🛒 Tambah", key=f"add_{item['id']}_{i}", use_container_width=True, disabled=not item.get('tersedia', True)):
                    from ui import add_to_cart
                    add_to_cart(item['id'], qty)
            
            st.markdown("---")
                
# --- FUNGSI HALAMAN FAVORIT ---

def page_favorites():
    st.markdown("## ❤️ Menu Favorit Anda")
    user_id = st.session_state['user']['id']
    favorite_items = get_favorite_menus(user_id)

    if not favorite_items:
        st.info("Anda belum memiliki menu favorit. Jelajahi menu untuk menambahkannya!")
        return

    st.markdown("---")
    
    # Tampilkan dalam layout sederhana tanpa banner
    cols = st.columns(2)
    
    for i, item in enumerate(favorite_items):
        with cols[i % 2]:
            # Layout horizontal sederhana
            col_img, col_detail, col_action = st.columns([1, 3, 1])
            
            with col_img:
                if item['url_gambar']:
                    st.markdown(f"""
                        <div style='
                            width: 80px;
                            height: 80px;
                            border-radius: 10px;
                            overflow: hidden;
                            border: 2px solid #D3A58E;
                        '>
                            <img src='{item['url_gambar']}' style='
                                width: 100%;
                                height: 100%;
                                object-fit: cover;
                            ' />
                        </div>
                    """, unsafe_allow_html=True)
            
            with col_detail:
                # Nama menu
                st.markdown(f"**{item['nama']}**")
                
                # Kategori dengan badge style
                st.markdown(f"""
                    <div style='
                        display: inline-block;
                        background-color: #E6E6FA;
                        color: #4B0082;
                        padding: 3px 8px;
                        border-radius: 15px;
                        font-size: 0.8em;
                        font-weight: bold;
                        margin-bottom: 8px;
                    '>
                        {item['kategori']}
                    </div>
                """, unsafe_allow_html=True)
                
                # Harga dengan styling yang menonjol
                st.markdown(f"""
                    <div style='
                        background: linear-gradient(90deg, #FFE4B5 0%, #FFD700 100%);
                        padding: 8px;
                        border-radius: 6px;
                        text-align: center;
                        margin: 10px 0;
                        border: 2px solid #DAA520;
                    '>
                        <span style='
                            color: #8B4513;
                            font-weight: bold;
                            font-size: 1.2em;
                        '>Rp {int(item['harga']):,}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Deskripsi
                if item.get('deskripsi'):
                    desc_key = f"fav_desc_expanded_{item['id']}_{i}"
                    is_expanded = st.session_state.get(desc_key, False)
                    
                    if len(item['deskripsi']) > 60:
                        if is_expanded:
                            st.markdown(f"""
                                <div style='
                                    background-color: #F8F9FA;
                                    padding: 8px;
                                    border-radius: 6px;
                                    border-left: 3px solid #D3A58E;
                                    margin-bottom: 8px;
                                '>
                                    <div style='color: #555; font-size: 0.8em; line-height: 1.3;'>
                                        <strong>Deskripsi:</strong> {item['deskripsi']}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button("Tampilkan lebih sedikit", key=f"fav_less_{item['id']}_{i}"):
                                st.session_state[desc_key] = False
                                st.rerun()
                        else:
                            st.markdown(f"""
                                <div style='
                                    background-color: #F8F9FA;
                                    padding: 8px;
                                    border-radius: 6px;
                                    border-left: 3px solid #D3A58E;
                                    margin-bottom: 8px;
                                '>
                                    <div style='color: #555; font-size: 0.8em; line-height: 1.3;'>
                                        <strong>Deskripsi:</strong> {item['deskripsi'][:60]}...
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button("Selengkapnya", key=f"fav_more_{item['id']}_{i}"):
                                st.session_state[desc_key] = True
                                st.rerun()
                    else:
                        st.markdown(f"""
                            <div style='
                                background-color: #F8F9FA;
                                padding: 8px;
                                border-radius: 6px;
                                border-left: 3px solid #D3A58E;
                                margin-bottom: 8px;
                            '>
                                <div style='color: #555; font-size: 0.8em; line-height: 1.3;'>
                                    <strong>Deskripsi:</strong> {item['deskripsi']}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style='
                            background-color: #F8F9FA;
                            padding: 8px;
                            border-radius: 6px;
                            border-left: 3px solid #D3A58E;
                            margin-bottom: 8px;
                        '>
                            <div style='color: #555; font-size: 0.8em;'>
                                <strong>Deskripsi:</strong> -
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Rating
                st.markdown(f"""
                    <div style='
                        background-color: #F5F5F5;
                        padding: 8px;
                        border-radius: 6px;
                        border-left: 4px solid #4CAF50;
                    '>
                        <div style='color: #666; font-size: 0.85em;'>
                            ⭐ {item['rating_rata_rata']:.1f} ({item['jumlah_ulasan']} ulasan)
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_action:
                # Tombol hapus
                if st.button("🗑️", key=f"remove_fav_{item['id']}_{i}", help="Hapus dari Favorit", use_container_width=True):
                    remove_from_favorites(user_id, item['id'])
                    st.toast("💔 Dihapus dari favorit.")
                    st.rerun()
            
            st.markdown("---")

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
        
        if 'reviewed_items' not in st.session_state:
            st.session_state['reviewed_items'] = set()

        for item in reviewable_items:
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