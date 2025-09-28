"""
Reusable UI components for the Streamlit app, like cart and order displays.
"""
import streamlit as st
import models

# --- Navigation Helper ---
def go(page_name: str):
    """Sets the session state to navigate to a new page."""
    st.session_state['page'] = page_name

# --- Cart Management ---

def add_to_cart(menu_id: int, quantity: int = 1):
    """Adds an item to the session cart."""
    cart = st.session_state.get('cart', {})
    menu_id_str = str(menu_id)
    cart[menu_id_str] = cart.get(menu_id_str, 0) + int(quantity)
    st.session_state['cart'] = cart
    st.success(f"Added to cart!")

def remove_from_cart(menu_id: int):
    """Removes an item from the session cart."""
    cart = st.session_state.get('cart', {})
    menu_id_str = str(menu_id)
    if menu_id_str in cart:
        del cart[menu_id_str]
    st.session_state['cart'] = cart
    st.experimental_rerun()

def show_cart():
    """Renders the shopping cart UI."""
    st.markdown("### Cart")
    cart = st.session_state['cart']
    if not cart:
        st.info("Your cart is empty. Add items from the Menu tab.")
        return

    # Fetch details for all items in the cart at once
    item_ids = [int(key) for key in cart.keys()]
    menu_items = {str(item['id']): item for item in [models.get_menu_item_by_id(i) for i in item_ids] if item}

    total = 0
    items_payload = []

    for item_id_str, quantity in cart.items():
        item = menu_items.get(item_id_str)
        if item:
            item_total = item['price'] * quantity
            total += item_total
            st.write(f"**{item['name']}** x {quantity} — Rp {int(item_total):,}")
            if st.button(f"Remove", key=f"rm_{item_id_str}"):
                remove_from_cart(int(item_id_str))
            items_payload.append({
                'menu_id': item['id'],
                'name': item['name'],
                'price': item['price'],
                'qty': quantity
            })
    st.markdown("---")
    st.write(f"**Subtotal: Rp {int(total):,}**")

    # Promo Code Section
    promo_code = st.text_input("Enter Promo Code", key='promo_input')
    if st.button("Apply Promo"):
        promo = models.get_active_promo_by_code(promo_code)
        if promo:
            st.session_state['promo_applied'] = promo
            st.success(f"Promo '{promo['code']}' applied! Discount: Rp {int(promo['discount_amount']):,}")
        else:
            st.session_state['promo_applied'] = None
            st.error("Invalid or inactive promo code.")

    discount = 0
    if st.session_state['promo_applied']:
        promo_info = st.session_state['promo_applied']
        discount = float(promo_info['discount_amount'])
        st.write(f"**Discount ({promo_info['code']}): - Rp {int(discount):,}**")

    grand_total = max(0, total - discount)
    st.markdown(f"### Total: Rp {int(grand_total):,}")

    # Checkout Section
    st.markdown("---")
    st.markdown("### Checkout")
    with st.form("checkout_form"):
        st.text_input("Your Name")
        st.text_input("Table Number")
        payment_method = st.selectbox("Payment Method", ["Cash", "QRIS", "E-Wallet"])
        submitted = st.form_submit_button("Place Order")

        if submitted:
            user = st.session_state.get('user')
            if not user:
                st.error("You must be logged in to place an order.")
                return

            try:
                order_id = models.create_order(user['id'], items_payload, grand_total, payment_method)
                st.success(f"Order placed successfully! Your Order ID is: {order_id}. Please proceed to the cashier for payment.")
                # Clear cart and promo after successful order
                st.session_state['cart'] = {}
                st.session_state['promo_applied'] = None
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to place order: {e}")


def show_user_orders():
    """Renders the order history for the current user."""
    st.markdown("### Your Orders")
    user = st.session_state.get('user')
    if not user:
        st.warning("Please log in to see your orders.")
        return

    orders = models.get_orders_by_user_id(user['id'])

    if not orders:
        st.info("You have no past orders.")
        return

    for order in orders:
        with st.container():
            st.markdown(f"**Order ID: {order['id']}** | Status: `{order['status']}`")
            st.write(f"Total: Rp {int(order['total']):,} | Payment: {order['payment_method']} | Date: {order['created_at']}")
            with st.expander("View Details"):
                for item in order['items']:
                    st.write(f"- {item['name']} x {item['qty']}")
            if order['status'] == 'Selesai': # Assuming this is the 'Completed' status
                if st.button(f"Rate This Order", key=f"rate_{order['id']}"):
                    st.session_state['review_target_order'] = order['id']
                    go('review')
                    st.experimental_rerun()
            st.markdown("---")
