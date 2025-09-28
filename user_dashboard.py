"""
Dasbor pengguna untuk aplikasi Caffe Dehh
Dengan fitur favorit, pesan ulang, dan status real-time.
"""

import streamlit as st
import time
from database import (
    get_all_menu, get_menu_item, create_order, get_user_orders, 
    submit_review, get_active_promo, get_reviews_for_menu,
    get_order_by_id,
    add_to_favorites, remove_from_favorites, get_favorite_menus # Impor fungsi favorit
)

def show_user_dashboard():
    user = st.session_state.get('user', {})
    st.subheader(f"Selamat Datang, {user.get('nama_pengguna', 'Pengguna')}!")
    
    if st.sidebar.button("Keluar"):
        st.session_state.clear()
        st.session_state['page'] = 'login'
        st.rerun()

    # FITUR BARU: Menambahkan tab Favorit
    tabs = st.tabs(["🍔 Menu", "❤️ Favorit Saya", "🛒 Keranjang", "📦 Pesanan / Status", "👤 Profil"])
    
    with tabs[0]:
        show_menu_tab(user)
    with tabs[1]:
        show_favorites_tab(user)
    with tabs[2]:
        show_cart_tab(user)
    with tabs[3]:
        show_user_orders_tab(user)
    with tabs[4]:
        show_profile_tab(user)

def show_menu_tab(user):
    search = st.text_input("Cari menu berdasarkan nama", key="menu_search")
    # Membutuhkan user_id untuk mengetahui status favorit
    menu_items = get_all_menu(search, user_id=user.get('id'))
    
    cats = {}
    for m in menu_items:
        cats.setdefault(m['kategori'], []).append(m)
    
    for cat, items in cats.items():
        st.markdown(f"### {cat}")
        cols = st.columns(3)
        for i, it in enumerate(items):
            c = cols[i % 3]
            with c:
                # FITUR BARU: Tombol Favorit di sebelah nama
                is_fav = it.get('is_favorite', False)
                fav_icon = "❤️" if is_fav else "🤍"
                if st.button(f"{fav_icon}", key=f"fav_menu_{it['id']}", help="Tambahkan ke favorit"):
                    if is_fav:
                        remove_from_favorites(user['id'], it['id'])
                    else:
                        add_to_favorites(user['id'], it['id'])
                    st.rerun()
                
                st.markdown(f"**{it['nama']}** — Rp {int(it['harga'])}")
                
                avg_rating = it.get('rating_rata_rata', 0)
                num_reviews = it.get('jumlah_ulasan', 0)
                if num_reviews > 0:
                    st.markdown(f"⭐ {avg_rating:.1f} ({num_reviews} ulasan)")
                else:
                    st.markdown("_(Belum ada ulasan)_")

                if it['url_gambar']:
                    st.image(it['url_gambar'], use_container_width=True)
                
                st.caption(it['deskripsi'])
                
                # FITUR BARU: Menampilkan status stok
                is_available = it.get('tersedia', True)
                if is_available:
                    st.success("Tersedia")
                    qty = st.number_input("Jumlah", min_value=1, value=1, key=f"qty_{it['id']}")
                    if st.button("Tambah ke keranjang", key=f"add_{it['id']}"):
                        add_to_cart(it, qty)
                        st.success("Ditambahkan ke keranjang")
                else:
                    st.error("Habis")
                    st.button("Tambah ke keranjang", key=f"add_{it['id']}", disabled=True)

def show_favorites_tab(user):
    st.markdown("### Menu Favorit Anda")
    favorite_items = get_favorite_menus(user.get('id'))

    if not favorite_items:
        st.info("Anda belum memiliki menu favorit. Tambahkan dengan menekan ikon hati ❤️ pada halaman menu.")
        return

    for it in favorite_items:
        st.markdown(f"**{it['nama']}** — Rp {int(it['harga'])}")
        if it['url_gambar']:
            st.image(it['url_gambar'], width=200)
        
        is_available = it.get('tersedia', True)
        if is_available:
            if st.button("Tambah ke Keranjang", key=f"add_fav_{it['id']}"):
                add_to_cart(it, 1)
                st.success(f"{it['nama']} ditambahkan ke keranjang!")
        else:
            st.error("Habis")
        
        if st.button("Hapus dari Favorit", key=f"rem_fav_{it['id']}"):
            remove_from_favorites(user['id'], it['id'])
            st.rerun()
        st.markdown("---")

def show_user_orders_tab(user):
    st.markdown("### Pesanan Anda")

    placeholder = st.empty()
    
    # FITUR BARU: Simulasi real-time update
    # Dijalankan beberapa kali untuk menunjukkan pembaruan
    for i in range(5): 
        with placeholder.container():
            orders = get_user_orders(user['id'])
            
            if not orders:
                st.info("Belum ada pesanan")
                break
            
            for order in orders:
                created_at_str = order.get('dibuat_pada').strftime('%d %B %Y, %H:%M') if order.get('dibuat_pada') else 'N/A'
                st.write(f"ID: {order['id']} | **Status: {order['status']}** | Total: Rp {int(order['total'])}")
                st.caption(f"{created_at_str} | {order['metode_pembayaran']}")
                
                items = order.get('item', [])
                with st.expander("Lihat Detail Pesanan"):
                    for it in items:
                        st.write(f" - {it.get('nama', 'N/A')} x {it.get('qty', 0)}")

                # Tombol hanya muncul jika status pesanan adalah 'Selesai'
                if order['status'] == 'Selesai':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Beri Ulasan", key=f"rate_{order['id']}"):
                            st.session_state['page'] = 'review'
                            st.session_state['review_target_order'] = order['id']
                            st.rerun()
                    with col2:
                        # FITUR BARU: Tombol Pesan Ulang
                        if st.button("Pesan Ulang", key=f"reorder_{order['id']}"):
                            reorder_items(items)
                            st.success("Semua item dari pesanan ini telah ditambahkan kembali ke keranjang!")
                            time.sleep(1) # Beri waktu untuk membaca pesan
                            st.rerun() # Pindah ke halaman keranjang bisa dilakukan di sini jika diinginkan
                st.markdown("---")
        
        # Cek jika semua pesanan sudah selesai, hentikan loop
        all_done = all(o['status'] in ['Selesai', 'Dibatalkan'] for o in orders)
        if all_done:
            break
            
        time.sleep(15) # Tunggu 15 detik sebelum refresh

# --- Fungsi Helper ---

def add_to_cart(item_dict, qty=1):
    if 'cart' not in st.session_state:
        st.session_state['cart'] = {}
    cart = st.session_state['cart']
    item_id_str = str(item_dict['id'])

    # Simpan seluruh detail item di keranjang
    if item_id_str not in cart:
        cart[item_id_str] = item_dict
        cart[item_id_str]['qty'] = 0
    
    cart[item_id_str]['qty'] += int(qty)
    st.session_state['cart'] = cart

def reorder_items(items_list):
    """Fungsi untuk menambahkan semua item dari pesanan lama ke keranjang."""
    for item in items_list:
        # Kita butuh detail lengkap item menu, jadi kita ambil dari database
        menu_item_details = get_menu_item(item['id_menu'])
        if menu_item_details and menu_item_details.get('tersedia', True):
            add_to_cart(menu_item_details, item['qty'])

# (Sisa kode seperti show_cart_tab, page_review, dll. tidak banyak berubah)
def show_cart_tab(user):
    st.markdown("### Keranjang")
    cart = st.session_state.get('cart', {})
    
    if not cart:
        st.info("Keranjang kosong")
        return
    
    total = 0
    items_payload = []
    
    for item_id, item_details in cart.items():
        st.write(f"{item_details['nama']} x {item_details['qty']} — Rp {int(item_details['harga'])} per item")
        total += item_details['harga'] * item_details['qty']
        if st.button("Hapus", key=f"rm_{item_id}"):
            remove_from_cart(item_id)
            st.rerun()
        
        items_payload.append({
            'id_menu': item_details['id'], 
            'nama': item_details['nama'], 
            'harga': item_details['harga'], 
            'qty': item_details['qty']
        })

    st.write(f"Subtotal: Rp {int(total)}")
    # ... (kode promo dan checkout yang sudah ada) ...
    # Bagian kode promo
    promo_code = st.text_input("Kode promo", key='promo_input')
    if st.button("Terapkan Promo"):
        promo = get_active_promo(promo_code)
        if promo:
            st.session_state['promo_applied'] = promo
            st.success(f"Promo diterapkan: {promo['kode']} - Rp {int(promo.get('jumlah_diskon', 0))}")
        else:
            st.error("Promo tidak valid atau tidak aktif")
    
    discount = 0
    if st.session_state.get('promo_applied'):
        discount = float(st.session_state['promo_applied'].get('jumlah_diskon', 0))
    
    grand = max(0, total - discount)
    st.write(f"Diskon: Rp {int(discount)}")
    st.write(f"Total: Rp {int(grand)}")

    st.markdown("---")
    st.markdown("### Checkout")
    with st.form("checkout_form"):
        name = st.text_input("Nama pemesan")
        table_no = st.text_input("Nomor meja")
        payment_method = st.selectbox("Metode pembayaran", ["Tunai", "QRIS", "E-Wallet"])
        submitted = st.form_submit_button("Buat Pesanan")

        if submitted:
            if not items_payload:
                st.warning("Keranjang Anda kosong.")
                return
            
            oid = create_order(user['id'], items_payload, grand, payment_method)
            st.success(f"Pesanan dibuat (ID: {oid}). Bayar di kasir.")
            
            # Kosongkan keranjang & promo
            st.session_state['cart'] = {}
            st.session_state['promo_applied'] = None
            st.rerun()

def remove_from_cart(menu_id):
    cart = st.session_state.get('cart', {})
    if str(menu_id) in cart:
        del cart[str(menu_id)]
    st.session_state['cart'] = cart

def show_profile_tab(user):
    st.write("Profil - belum diimplementasikan secara mendalam")
    st.write(f"Nama pengguna: {user.get('nama_pengguna', 'N/A')}")
    st.write(f"Peran: {user.get('peran', 'N/A')}")

def page_review():
    st.subheader("Kirim Ulasan")
    order_id = st.session_state.get('review_target_order')

    if not order_id:
        st.error("Pesanan tidak ditemukan untuk diulas.")
        if st.button("Kembali ke Dasbor"):
            st.session_state['page'] = 'user_dashboard'
            st.rerun()
        return

    order_details = get_order_by_id(order_id)
    if not order_details or not order_details.get('item'):
        st.error("Tidak dapat memuat item dari pesanan ini.")
        if st.button("Kembali ke Dasbor"):
            st.session_state['page'] = 'user_dashboard'
            st.rerun()
        return

    st.write(f"Mengulas pesanan: {order_id}")
    
    items_in_order = order_details.get('item', [])
    item_choices = {item['nama']: item['id_menu'] for item in items_in_order}

    selected_item_name = st.selectbox("Pilih menu untuk diulas", list(item_choices.keys()))
    
    rating = st.slider("Peringkat", 1, 5, 5)
    text = st.text_area("Tulis ulasan Anda")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Kirim Ulasan"):
            uid = st.session_state['user']['id']
            mid = item_choices[selected_item_name]
            submit_review(uid, mid, rating, text)
            st.success("Terima kasih atas ulasannya!")
            del st.session_state['review_target_order']
            st.session_state['page'] = 'user_dashboard'
            st.rerun()

    with col2:
        if st.button("Batal"):
            del st.session_state['review_target_order']
            st.session_state['page'] = 'user_dashboard'
            st.rerun()

