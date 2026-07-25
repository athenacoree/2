import streamlit as st
import logging
from care_clear_crew.history_db import init_db
from care_clear_crew.ui import (
    inject_styles, render_header, render_sidebar, render_main_view,
    render_new_analysis, render_precheck_simulator, render_analytics_view,
    render_history_view, render_settings_view, render_users_management_view
)

logging.basicConfig(level=logging.ERROR)
init_db()

# Page config
st.set_page_config(
    page_title="CareClearCrew",
    page_icon="🩺",
    layout="wide"
)

# Custom styles & layout header
inject_styles()
render_header()

# Session and Auth Management
if "user" not in st.session_state:
    st.session_state["user"] = None

# If user is not authenticated, show main view (login/register form)
if st.session_state["user"] is None:
    render_main_view()

# Active session navigation
current_user = st.session_state["user"]
menu = render_sidebar()

# Route views
if menu == "Nuevo Análisis":
    render_new_analysis(current_user)

elif menu == "Simulador Pre-Envío":
    render_precheck_simulator(current_user)

elif menu == "Historial de Solicitudes":
    render_history_view(current_user)

elif menu == "Panel Ejecutivo":
    render_analytics_view(current_user)

elif menu == "Gestión de Usuarios":
    render_users_management_view(current_user)

elif menu == "Configuración y LLM":
    render_settings_view(current_user)
