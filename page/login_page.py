import streamlit as st
from utils.db_handler import DatabaseManager
import time

# Pages
def login_page(guest_mode=False):
    with st.empty().container(border=True):
        col1, _, col2 = st.columns([10, 1, 10])
        
        with col1:
            st.write("")
            st.write("")
            # st.video("data/demo.mp4", autoplay=True, loop=True, muted=True)
            st.image("data/house_logo.jpg")
        
        with col2:
            st.title("Login Page")

            email = st.text_input("E-mail")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                time.sleep(2)
                if not (email and password):
                    st.error("Please provide email and password")
                elif DatabaseManager.authenticate_user(email, password):
                    st.session_state['authenticated'] = True
                    st.session_state['email'] = email
                    st.session_state['guest_mode'] = False
                    
                    # ✅ Obtener y guardar el rol del usuario
                    user_role = DatabaseManager.get_user_role(email)
                    st.session_state['role'] = user_role
                    
                    st.session_state['page'] = 'app'
                    st.rerun()
                else:
                    st.error("Invalid login credentials")

            if st.button("Sign Up"):
                st.session_state['page'] = 'signup'
                st.rerun()
                
            if guest_mode:
                if st.button("Continue as Guest"):
                    st.session_state['guest_mode'] = True
                    st.session_state['authenticated'] = True
                    st.session_state['role'] = "guest"  # Rol por defecto para invitados
                    st.session_state['page'] = 'app'
                    st.rerun()
