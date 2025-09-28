"""
Authentication pages for Caffe Dehh application
Contains login and registration functionality
"""

import streamlit as st
from database import authenticate, create_user

def page_login():
    st.subheader("Login / Register")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Login")
        username = st.text_input("Username", key='login_user')
        password = st.text_input("Password", type='password', key='login_pass')
        if st.button("Login"):
            if not username or not password:
                st.error("Username dan Password tidak boleh kosong.")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state['user'] = user
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['role'] = user['role']
                    st.success(f"Welcome back, {username}!")
                    if user['role'] == 'admin':
                        st.session_state['page'] = 'admin_dashboard'
                    else:
                        st.session_state['page'] = 'user_dashboard'
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    with col2:
        st.markdown("### Register")
        r_user = st.text_input("New username", key='reg_user')
        r_pass = st.text_input("New password", type='password', key='reg_pass')
        if st.button("Register"):
            if not r_user or not r_pass:
                st.error("Username dan Password tidak boleh kosong.")
            else:
                try:
                    uid = create_user(r_user, r_pass, role='user')
                    st.success("Account created — please login")
                except Exception as e:
                    if "unique constraint" in str(e).lower():
                        st.error("Username sudah terdaftar.")
                    else:
                        st.error(f"Error creating user: {e}")

def show_register():
    st.title("Halaman Pendaftaran")
    st.write("Silakan buat akun pengguna baru.")

    new_user = st.text_input("Buat Username")
    new_pass = st.text_input("Buat Password", type="password")

    if st.button("Daftar"):
        if new_user == "" or new_pass == "":
            st.error("Username/Password tidak boleh kosong.")
        else:
            try:
                create_user(new_user, new_pass, "user")
                st.success("Registrasi berhasil! Anda telah terdaftar sebagai pengguna.")
                st.session_state.page = "login"
                st.rerun()
            except Exception as e:
                if "unique constraint" in str(e).lower():
                    st.error("Username sudah terdaftar.")
                else:
                    st.error(f"Gagal registrasi: {e}")

    if st.button("Kembali ke Login"):
        st.session_state.page = "login"
        st.rerun()