"""
Komponen UI yang dapat digunakan kembali untuk aplikasi Streamlit, seperti tampilan keranjang dan pesanan.
"""
import streamlit as st
# Ubah impor dari 'models' ke 'database' dan beri alias agar sisa kode tidak perlu diubah
import database as models

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
    st.success(f"Ditambahkan ke keranjang!")

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
    st.markdown("### Keranjang")
    cart = st.session_state['cart']
    if not cart:
        st.info("Keranjang Anda kosong. Tambahkan item dari tab Menu.")
        return

    # Ambil detail untuk semua item di keranjang sekaligus
    item_ids = [int(key) for key in cart.keys()]
    menu_items = {str(item['id']): item for item in [models.get_menu_item(i) for i in item_ids] if item}

    total = 0
    items_payload = []

    for item_id_str, quantity in cart.items():
        item = menu_items.get(item_id_str)
        if item:
            item_total = item['harga'] * quantity
            total += item_total
            st.write(f"**{item['nama']}** x {quantity} — Rp {int(item_total):,}")
            if st.button(f"Hapus", key=f"rm_{item_id_str}"):
                remove_from_cart(int(item_id_str))
            items_payload.append({
                'id_menu': item['id'],
                'nama': item['nama'],
                'harga': item['harga'],
                'qty': quantity
            })
    st.markdown("---")
    st.write(f"**Subtotal: Rp {int(total):,}**")

    # Bagian Kode Promo
    promo_code = st.text_input("Masukkan Kode Promo", key='promo_input')
    if st.button("Terapkan Promo"):
        promo = models.get_active_promo(promo_code)
        if promo:
            st.session_state['promo_applied'] = promo
            st.success(f"Promo '{promo['kode']}' diterapkan! Diskon: Rp {int(promo['jumlah_diskon']):,}")
        else:
            st.session_state['promo_applied'] = None
            st.error("Kode promo tidak valid atau tidak aktif.")

    discount = 0
    if st.session_state.get('promo_applied'):
        promo_info = st.session_state['promo_applied']
        discount = float(promo_info['jumlah_diskon'])
        st.write(f"**Diskon ({promo_info['kode']}): - Rp {int(discount):,}**")

    grand_total = max(0, total - discount)
    st.markdown(f"### Total: Rp {int(grand_total):,}")

    # Bagian Checkout
    st.markdown("---")
    st.markdown("### Checkout")
    with st.form("checkout_form"):
        st.text_input("Nama Anda")
        st.text_input("Nomor Meja")
        payment_method = st.selectbox("Metode Pembayaran", ["Tunai", "QRIS", "E-Wallet"])
        submitted = st.form_submit_button("Buat Pesanan")

        if submitted:
            user = st.session_state.get('user')
            if not user:
                st.error("Anda harus masuk untuk membuat pesanan.")
                return

            try:
                order_id = models.create_order(user['id'], items_payload, grand_total, payment_method)
                st.success(f"Pesanan berhasil dibuat! ID Pesanan Anda adalah: {order_id}. Silakan lanjutkan ke kasir untuk pembayaran.")
                # Kosongkan keranjang dan promo setelah pesanan berhasil
                st.session_state['cart'] = {}
                st.session_state['promo_applied'] = None
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Gagal membuat pesanan: {e}")


def show_user_orders():
    """Merender riwayat pesanan untuk pengguna saat ini."""
    st.markdown("### Pesanan Anda")
    user = st.session_state.get('user')
    if not user:
        st.warning("Silakan masuk untuk melihat pesanan Anda.")
        return

    orders = models.get_user_orders(user['id'])

    if not orders:
        st.info("Anda tidak memiliki pesanan sebelumnya.")
        return

    for order in orders:
        with st.container():
            st.markdown(f"**ID Pesanan: {order['id']}** | Status: `{order['status']}`")
            st.write(f"Total: Rp {int(order['total']):,} | Pembayaran: {order['metode_pembayaran']} | Tanggal: {order['dibuat_pada']}")
            with st.expander("Lihat Detail"):
                for item in order['item']:
                    st.write(f"- {item['nama']} x {item['qty']}")
            if order['status'] == 'Selesai': 
                if st.button(f"Beri Peringkat Pesanan Ini", key=f"rate_{order['id']}"):
                    st.session_state['review_target_order'] = order['id']
                    go('review')
                    st.experimental_rerun()
            st.markdown("---")

