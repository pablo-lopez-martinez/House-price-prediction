import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

# Obtener la clave de cookies desde secrets
COOKIE_PASSWORD = st.secrets["cookies"]["password"]

# Inicializar el gestor de cookies con la clave segura
cookies = EncryptedCookieManager(prefix="my_app", password=COOKIE_PASSWORD)

def init_cookies():
    """Inicializa el gestor de cookies y verifica si están habilitadas."""
    if not cookies.ready():
        st.warning("Las cookies no están habilitadas en tu navegador.")
        st.stop()

def set_auth_cookie(email):
    """Guarda la sesión del usuario en una cookie."""
    cookies["auth_user"] = email
    cookies.save()

def get_auth_cookie():
    """Obtiene el usuario autenticado desde la cookie."""
    return cookies.get("auth_user")

def remove_auth_cookie():
    """Elimina la cookie de autenticación y cierra la sesión."""
    cookies["auth_user"] = ""
    cookies.save()
