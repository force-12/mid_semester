"""
Halaman otentikasi untuk aplikasi Caffe Dehh
Berisi fungsionalitas masuk, pendaftaran, dan lupa kata sandi
"""

import streamlit as st
from database import authenticate, create_user, user_exists, update_user_password

def page_login():
    """Menampilkan halaman login."""
    st.title("Masuk ke Akun Anda")

    with st.form("login_form"):
        username = st.text_input("Nama Pengguna")
        password = st.text_input("Kata Sandi", type='password')
        submitted = st.form_submit_button("Masuk")

        if submitted:
            if not username or not password:
                st.error("Nama pengguna dan kata sandi tidak boleh kosong.")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state['user'] = user
                    st.session_state['logged_in'] = True
                    st.session_state['nama_pengguna'] = username
                    st.session_state['peran'] = user['peran']
                    st.success(f"Selamat datang kembali, {username}!")
                    if user['peran'] == 'admin':
                        st.session_state['page'] = 'admin_dashboard'
                    else:
                        st.session_state['page'] = 'user_dashboard'
                    st.rerun()
                else:
                    st.error("Nama pengguna atau kata sandi salah.")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Belum punya akun?")
        if st.button("Daftar di sini"):
            st.session_state['page'] = 'register'
            st.rerun()
    with col2:
        st.write("Lupa kata sandi Anda?")
        if st.button("Atur Ulang Sandi"):
            st.session_state['page'] = 'forgot_password'
            st.rerun()

def page_register():
    """Menampilkan halaman pendaftaran."""
    st.title("Buat Akun Baru")
    
    with st.form("register_form"):
        new_user = st.text_input("Nama Pengguna")
        new_pass = st.text_input("Kata Sandi", type="password")
        confirm_pass = st.text_input("Konfirmasi Kata Sandi", type="password")
        submitted = st.form_submit_button("Daftar")

        if submitted:
            if not new_user or not new_pass or not confirm_pass:
                st.error("Semua kolom harus diisi.")
            elif new_pass != confirm_pass:
                st.error("Kata sandi dan konfirmasi kata sandi tidak cocok.")
            else:
                try:
                    create_user(new_user, new_pass, "user")
                    st.success("Registrasi berhasil! Silakan masuk.")
                    st.session_state['page'] = 'login'
                    # st.rerun() # Tidak perlu rerun, biarkan pengguna melihat pesan sukses
                except Exception as e:
                    if "unique constraint" in str(e).lower():
                        st.error("Nama pengguna sudah terdaftar.")
                    else:
                        st.error(f"Gagal registrasi: {e}")

    st.markdown("---")
    st.write("Sudah punya akun?")
    if st.button("Masuk di sini"):
        st.session_state.page = "login"
        st.rerun()

def page_forgot_password():
    """Menampilkan halaman untuk mengatur ulang kata sandi."""
    st.title("Lupa Kata Sandi")

    # Step 1: Meminta username
    if 'reset_step' not in st.session_state:
        st.session_state.reset_step = 1

    if st.session_state.reset_step == 1:
        with st.form("find_user_form"):
            username_to_reset = st.text_input("Masukkan nama pengguna Anda")
            submitted = st.form_submit_button("Cari Akun")

            if submitted:
                if user_exists(username_to_reset):
                    st.session_state.username_to_reset = username_to_reset
                    st.session_state.reset_step = 2
                    st.rerun()
                else:
                    st.error("Pengguna tidak ditemukan.")

    # Step 2: Mengatur ulang password
    if st.session_state.reset_step == 2:
        username = st.session_state.get('username_to_reset', '')
        st.write(f"Mengatur ulang kata sandi untuk pengguna: **{username}**")

        with st.form("reset_password_form"):
            new_password = st.text_input("Kata Sandi Baru", type="password")
            confirm_password = st.text_input("Konfirmasi Kata Sandi Baru", type="password")
            submitted = st.form_submit_button("Ubah Kata Sandi")

            if submitted:
                if not new_password or not confirm_password:
                    st.error("Kata sandi tidak boleh kosong.")
                elif new_password != confirm_password:
                    st.error("Kata sandi tidak cocok.")
                else:
                    try:
                        update_user_password(username, new_password)
                        st.success("Kata sandi berhasil diubah! Silakan masuk dengan sandi baru Anda.")
                        # Reset state dan kembali ke login
                        del st.session_state.reset_step
                        del st.session_state.username_to_reset
                        st.session_state.page = "login"
                        # st.rerun() # Biarkan pengguna melihat pesan sukses
                    except Exception as e:
                        st.error(f"Gagal memperbarui kata sandi: {e}")

    st.markdown("---")
    if st.button("Kembali ke Halaman Masuk"):
        # Pastikan untuk mereset state jika pengguna kembali
        if 'reset_step' in st.session_state:
            del st.session_state.reset_step
        if 'username_to_reset' in st.session_state:
            del st.session_state.username_to_reset
        st.session_state.page = "login"
        st.rerun()

