"""
Komponen UI yang dapat digunakan kembali untuk aplikasi Streamlit, seperti tampilan keranjang dan pesanan.
"""
import streamlit as st
import database as models
from datetime import datetime

# --- Pembantu Navigasi ---
def go(page_name: str):
    """Mengatur status sesi untuk menavigasi ke halaman baru."""
    st.session_state['page'] = page_name

# --- Manajemen Keranjang ---

def add_to_cart(menu_id: int, quantity: int = 1):
    """Menambahkan item ke keranjang sesi."""
    cart = st.session_state.get('cart', {})
    menu_id_str = str(menu_id)
    cart[menu_id_str] = cart.get(menu_id_str, 0) + int(quantity)
    st.session_state['cart'] = cart
    # Menggunakan notifikasi yang lebih cepat dan modern
    st.toast("✅ Ditambahkan ke keranjang!") 

def remove_from_cart(menu_id: int):
    """Menghapus item dari keranjang sesi."""
    cart = st.session_state.get('cart', {})
    menu_id_str = str(menu_id)
    if menu_id_str in cart:
        del cart[menu_id_str]
    st.session_state['cart'] = cart
    st.experimental_rerun()

def show_cart():
    """Merender UI keranjang belanja."""
    st.markdown("## 🛒 Keranjang Belanja Anda")
    cart = st.session_state['cart']
    
    # Menggunakan metrik untuk menampilkan jumlah item di keranjang
    col_cart_status = st.columns([1, 3])
    total_items = sum(cart.values())
    col_cart_status[0].metric(label="Jumlah Item", value=total_items)

    if not cart:
        st.info("Keranjang Anda kosong. Mari pesan sesuatu!")
        return

    total = 0
    items_payload = []
    
    st.markdown("---")
    st.subheader("Daftar Item")

    # Menggunakan kolom untuk tampilan daftar item yang lebih ringkas
    for item_id_str, quantity in cart.items():
        item = models.get_menu_item(int(item_id_str)) # Ambil detail item
        if item:
            item_total = item['harga'] * quantity
            total += item_total
            
            col_item, col_price, col_action = st.columns([4, 2, 1])
            
            with col_item:
                st.markdown(f"**{item['nama']}**")
                st.caption(f"Jumlah: {quantity} x Rp {int(item['harga']):,}")
                
            with col_price:
                st.markdown(f"<p style='text-align: right; font-weight: bold;'>Rp {int(item_total):,}</p>", unsafe_allow_html=True)

            with col_action:
                if st.button("🗑️", key=f"rm_{item_id_str}", help="Hapus item ini", use_container_width=True):
                    remove_from_cart(int(item_id_str))
            
            items_payload.append({
                'id_menu': item['id'],
                'nama': item['nama'],
                'harga': item['harga'],
                'qty': quantity
            })
            st.markdown("---")

    st.markdown(f"**Subtotal:** <p style='text-align: right; font-weight: bold; font-size: 1.1em;'>Rp {int(total):,}</p>", unsafe_allow_html=True)

    # Bagian Kode Promo
    st.subheader("🔖 Kode Promo")
    col_promo = st.columns([3, 1])
    with col_promo[0]:
        promo_code = st.text_input("Masukkan Kode Promo", key='promo_input', label_visibility="collapsed", placeholder="Contoh: CAFFEDEHH25")
    with col_promo[1]:
        # Tambahkan margin-top untuk menyelaraskan tombol dengan input text
        st.markdown("<div style='margin-top: 25px;'>", unsafe_allow_html=True)
        if st.button("Terapkan", use_container_width=True):
            if promo_code:
                promo = models.get_active_promo(promo_code)
                if promo:
                    st.session_state['promo_applied'] = promo
                    st.success(f"Promo '{promo['kode']}' diterapkan! Diskon: Rp {int(promo['jumlah_diskon']):,}")
                else:
                    st.session_state['promo_applied'] = None
                    st.error("Kode promo tidak valid atau tidak aktif.")
            else:
                 st.session_state['promo_applied'] = None
                 st.info("Masukkan kode promo.")
        st.markdown("</div>", unsafe_allow_html=True)

    discount = 0
    if st.session_state.get('promo_applied'):
        promo_info = st.session_state['promo_applied']
        discount = float(promo_info['jumlah_diskon'])
        st.markdown(f"**Diskon ({promo_info['kode']}):** <p style='text-align: right; color: red; font-weight: bold; font-size: 1.1em;'>- Rp {int(discount):,}</p>", unsafe_allow_html=True)
        
    grand_total = max(0, total - discount)
    st.markdown("---")
    st.markdown(f"<h3 style='text-align: right;'>Total Akhir: Rp {int(grand_total):,}</h3>", unsafe_allow_html=True)

    # Bagian Checkout
    st.subheader("💳 Informasi Pesanan")
    with st.form("checkout_form", clear_on_submit=True):
        st.text_input("Nama Anda", help="Nama untuk dipanggil saat pesanan siap", placeholder="Contoh: Risa")
        st.text_input("Nomor Meja", help="Nomor meja Anda saat ini", placeholder="Contoh: 05")
        payment_method = st.selectbox("Metode Pembayaran", ["Tunai", "QRIS", "E-Wallet"])
        submitted = st.form_submit_button("Buat Pesanan & Bayar")

        if submitted:
            user = st.session_state.get('user')
            if not user:
                st.error("Anda harus masuk untuk membuat pesanan.")
                return

            try:
                order_id = models.create_order(user['id'], items_payload, grand_total, payment_method)
                st.balloons() # Efek visual sukses
                st.success(f"Pesanan berhasil dibuat! ID Pesanan: **{order_id}**. Silakan lanjutkan ke kasir untuk pembayaran.")
                # Kosongkan keranjang dan promo setelah pesanan berhasil
                st.session_state['cart'] = {}
                st.session_state['promo_applied'] = None
                # st.experimental_rerun() # Tidak perlu rerun karena form clear_on_submit=True
            except Exception as e:
                st.error(f"Gagal membuat pesanan: {e}")


def show_user_orders():
    """Merender riwayat pesanan untuk pengguna saat ini."""
    st.markdown("## 📋 Riwayat Pesanan Anda")
    user = st.session_state.get('user')
    if not user:
        st.warning("Silakan masuk untuk melihat pesanan Anda.")
        return

    orders = models.get_user_orders(user['id'])

    if not orders:
        st.info("Anda belum memiliki pesanan sebelumnya.")
        return

    # Tampilkan pesanan terbaru di bagian atas
    for order in orders:
        # Menggunakan warna dan ikon status yang lebih menarik
        status = order['status']
        if status == 'Selesai':
            status_style = "background-color: #D4EDDA; color: #155724; border: 1px solid #C3E6CB;"
            icon = "✅"
        elif status == 'Sedang Diproses':
            status_style = "background-color: #FFF3CD; color: #856404; border: 1px solid #FFEEBA;"
            icon = "⏳"
        elif status == 'Dibatalkan':
            status_style = "background-color: #F8D7DA; color: #721C24; border: 1px solid #F5C6CB;"
            icon = "❌"
        else:
            status_style = "background-color: #CCE5FF; color: #004085; border: 1px solid #B8DAFF;"
            icon = "📝" # Tertunda
            
        
        st.markdown(f"""
            <div class='stContainer' style='{status_style} padding: 15px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <h5 style='margin: 0; color: #36454F;'>{icon} Pesanan #{order['id']}</h5>
                    <span style='font-weight: bold; padding: 5px 10px; border-radius: 5px;'>{status}</span>
                </div>
                <p style='margin-bottom: 5px;'>**Total:** Rp {int(order['total']):,} | **Pembayaran:** {order['metode_pembayaran']}</p>
                <p style='font-size: 0.8em; color: #555;'>Tanggal: {order['dibuat_pada'].strftime('%d-%m-%Y %H:%M')}</p>
        """, unsafe_allow_html=True)


        # Detail Pesanan di dalam expander
        with st.expander("Lihat Detail Item"):
            for item in order['item']:
                st.write(f"- {item['nama']} x {item['qty']}")
        
        # Tombol review, hanya muncul jika status Selesai
        if status == 'Selesai': 
            col_review = st.columns([3, 1])
            with col_review[1]:
                if st.button(f"⭐ Beri Peringkat", key=f"rate_{order['id']}", use_container_width=True):
                    st.session_state['review_target_order'] = order['id']
                    go('review')
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("") # Margin antar pesanan
