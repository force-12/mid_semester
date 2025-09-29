"""
Halaman otentikasi untuk aplikasi Caffe Dehh
Berisi fungsionalitas masuk, pendaftaran, dan lupa kata sandi
"""

import streamlit as st
from database import authenticate, create_user, user_exists, update_user_password

def page_login():
    """Menampilkan halaman login."""
    # Pusatkan konten
    col_center = st.columns([1, 2, 1])
    with col_center[1]:
        st.title("Selamat Datang")
        st.markdown("<h3 style='text-align: center;'>Masuk ke Akun Anda</h3>", unsafe_allow_html=True)

        # Menggunakan st.container untuk efek kartu
        with st.container():
            st.markdown("<div class='stContainer' style='padding: 30px; border: 2px solid #D3A58E;'>", unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Nama Pengguna", placeholder="Masukkan nama pengguna")
                password = st.text_input("Kata Sandi", type='password', placeholder="Masukkan kata sandi")
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
            st.markdown("</div>", unsafe_allow_html=True)
    
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<p style='margin-top: 10px;'>Belum punya akun?</p>", unsafe_allow_html=True)
            if st.button("Daftar di sini", key='btn_register'):
                st.session_state['page'] = 'register'
                st.rerun()
        with col2:
            st.markdown("<p style='margin-top: 10px;'>Lupa kata sandi Anda?</p>", unsafe_allow_html=True)
            if st.button("Atur Ulang Sandi", key='btn_forgot'):
                st.session_state['page'] = 'forgot_password'
                st.rerun()

def page_register():
    """Menampilkan halaman pendaftaran."""
    col_center = st.columns([1, 2, 1])
    with col_center[1]:
        st.title("Daftar")
        st.markdown("<h3 style='text-align: center;'>Buat Akun Baru</h3>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div class='stContainer' style='padding: 30px; border: 2px solid #D3A58E;'>", unsafe_allow_html=True)
            with st.form("register_form"):
                new_user = st.text_input("Nama Pengguna", placeholder="Pilih nama pengguna unik")
                new_pass = st.text_input("Kata Sandi", type="password", placeholder="Buat kata sandi")
                confirm_pass = st.text_input("Konfirmasi Kata Sandi", type="password", placeholder="Ulangi kata sandi")
                submitted = st.form_submit_button("Daftar")

                if submitted:
                    if not new_user or not new_pass or not confirm_pass:
                        st.error("Semua kolom harus diisi.")
                    elif new_pass != confirm_pass:
                        st.error("Kata sandi dan konfirmasi kata sandi tidak cocok.")
                    else:
                        try:
                            # Menggunakan `user` sebagai peran default, sesuai aslinya
                            create_user(new_user, new_pass, "user")
                            st.success("Registrasi berhasil! Silakan masuk.")
                            st.session_state['page'] = 'login'
                        except Exception as e:
                            if "unique constraint" in str(e).lower():
                                st.error("Nama pengguna sudah terdaftar.")
                            else:
                                st.error(f"Gagal registrasi: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Masuk di sini", key='btn_login_from_reg'):
        st.session_state.page = "login"
        st.rerun()

def page_forgot_password():
    """Menampilkan halaman untuk mengatur ulang kata sandi."""
    col_center = st.columns([1, 2, 1])
    with col_center[1]:
        st.title("Lupa Kata Sandi")

        if 'reset_step' not in st.session_state:
            st.session_state.reset_step = 1

        with st.container():
            st.markdown("<div class='stContainer' style='padding: 30px; border: 2px solid #D3A58E;'>", unsafe_allow_html=True)
            if st.session_state.reset_step == 1:
                with st.form("find_user_form"):
                    username_to_reset = st.text_input("Masukkan nama pengguna Anda", placeholder="Nama pengguna terdaftar")
                    submitted = st.form_submit_button("Cari Akun")

                    if submitted:
                        if user_exists(username_to_reset):
                            st.session_state.username_to_reset = username_to_reset
                            st.session_state.reset_step = 2
                            st.rerun()
                        else:
                            st.error("Pengguna tidak ditemukan.")

            if st.session_state.reset_step == 2:
                username = st.session_state.get('username_to_reset', '')
                st.info(f"Mengatur ulang kata sandi untuk: **{username}**")

                with st.form("reset_password_form"):
                    new_password = st.text_input("Kata Sandi Baru", type="password", placeholder="Kata sandi baru")
                    confirm_password = st.text_input("Konfirmasi Kata Sandi Baru", type="password", placeholder="Ulangi kata sandi baru")
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
                                del st.session_state.reset_step
                                del st.session_state.username_to_reset
                                st.session_state.page = "login"
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal memperbarui kata sandi: {e}")
            
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Kembali ke Halaman Masuk", key='btn_back_to_login'):
        if 'reset_step' in st.session_state:
            del st.session_state.reset_step
        if 'username_to_reset' in st.session_state:
            del st.session_state.username_to_reset
        st.session_state.page = "login"
        st.rerun()
