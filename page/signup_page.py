import streamlit as st
import re
from utils.db_handler import DatabaseManager
import time

def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def input_field(input_param, type):
    if type == 'text':
        st.session_state[input_param] = st.text_input(input_param)
    elif type == 'number':
        st.session_state[input_param] = st.number_input(input_param, step=1)

def signup_page(extra_input_params=False, confirmPass=False):
    if st.button("Back to Login"):
        st.session_state['page'] = 'login'
        st.rerun()

    with st.empty().container(border=True):
        st.title("Sign Up Page")

        if extra_input_params:
            for input_param, input_type in st.session_state['extra_input_params'].items():
                print(input_param, input_type)
                input_field(input_param, input_type)

        st.session_state['email'] = st.text_input("Email")
        if st.session_state['email'] and not is_valid_email(st.session_state['email']):
            st.error("Please enter a valid email address")

        st.session_state['password'] = st.text_input("Password", type='password')

        if confirmPass:
            confirm_password = st.text_input("Confirm Password", type='password')

        if st.session_state['email'] and st.session_state['password'] and \
           (not confirmPass or (confirmPass and st.session_state['password'] == confirm_password)):

            if extra_input_params and not all(st.session_state.get(param) for param in st.session_state['extra_input_params']):
                st.error("Please fill in all required fields")
            else:
                if st.button("Register"):
                    if DatabaseManager.verify_duplicate_user(st.session_state['email']):
                        st.error("User already exists")
                    else:
                        extra_params_values = {param.lower(): st.session_state.get(param) for param in st.session_state['extra_input_params']}
                        role = "user"  
                        if DatabaseManager.save_user(st.session_state['email'], st.session_state['password'], role, extra_params_values):
                            st.success("Registration successful")
                            time.sleep(1)
                            st.session_state['page'] = 'login'
                            st.rerun()
                        else: 
                            st.error("Registration failed. Please try again.")
        else:
            if confirmPass and st.session_state['password'] != confirm_password:
                st.error("Passwords do not match")
            elif st.button("Register"):
                st.error("Please fill in all required fields")
