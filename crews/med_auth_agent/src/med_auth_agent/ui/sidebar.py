import streamlit as st
from med_auth_agent.history_db import log_activity

def render_sidebar():
    """Renders the sidebar with user info, logout button, and navigation options."""
    current_user = st.session_state.get("user")
    if not current_user:
        return None

    institution = current_user["institution_name"]
    role = current_user["role"]
    user_id = current_user["id"]
    user_name = current_user["full_name"]

    st.sidebar.markdown(f"### Usuario: **{user_name}**")
    st.sidebar.markdown(f"Rol: `{role.capitalize()}`")
    st.sidebar.markdown(f"Institución: **{institution}**")

    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        log_activity(user_id, user_name, institution, "logout", "Cierre de sesión manual")
        st.session_state["user"] = None
        st.rerun()

    # Define navigation options based on role
    menu_options = ["Nuevo Análisis", "Simulador Pre-Envío", "Historial de Solicitudes"]
    if role == "administrador":
        menu_options += ["Panel Ejecutivo", "Gestión de Usuarios"]
    menu_options += ["Configuración y LLM"]

    menu = st.sidebar.radio("Navegación", menu_options)
    return menu
