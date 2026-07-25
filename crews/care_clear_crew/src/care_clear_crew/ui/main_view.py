import streamlit as st
import logging
from care_clear_crew.auth import create_user_record, verify_login
from care_clear_crew.history_db import log_activity

def render_main_view():
    """Renders the login and registration screen inside a glass card."""
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    auth_mode = st.radio("Acceso al Sistema", ["Iniciar Sesión", "Crear cuenta"], horizontal=True)

    if auth_mode == "Iniciar Sesión":
        st.subheader("🔑 Iniciar Sesión en CareClearCrew")
        with st.form("login_form"):
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            submit_btn = st.form_submit_button("Iniciar Sesión", use_container_width=True)

            if submit_btn:
                try:
                    user_data = verify_login(email, password)
                    if user_data:
                        st.session_state["user"] = user_data
                        log_activity(
                            user_data["id"], user_data["full_name"], user_data["institution_name"],
                            "login", "Inicio de sesión exitoso desde app"
                        )
                        st.success(f"¡Bienvenido, {user_data['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas o usuario inválido.")
                except PermissionError as pe:
                    st.error(str(pe))
                except Exception as e:
                    logging.exception("Error en proceso de login")
                    st.error("Ocurrió un error inesperado al iniciar sesión.")

    else:
        st.subheader("📝 Registrar Nueva Cuenta o Institución")
        st.write("Registra la primera cuenta administrativa de tu clínica/institución para invitar y gestionar más usuarios.")
        with st.form("register_form"):
            reg_email = st.text_input("Correo electrónico de la cuenta")
            reg_password = st.text_input("Contraseña de acceso", type="password")
            reg_name = st.text_input("Nombre Completo")
            reg_institution = st.text_input("Nombre de la Clínica u Organización")

            reg_submit = st.form_submit_button("Registrar Cuenta", use_container_width=True)

            if reg_submit:
                if not reg_email or not reg_password or not reg_name or not reg_institution:
                    st.error("Todos los campos son obligatorios para el registro.")
                else:
                    try:
                        uid = create_user_record(
                            email=reg_email,
                            password=reg_password,
                            full_name=reg_name,
                            role="operativo",  # first user automatically upgraded to administrator inside create_user_record
                            institution_name=reg_institution
                        )
                        # Log activity
                        log_activity(
                            uid, reg_name.strip(), reg_institution.strip(),
                            "user_created", "Usuario auto-registrado en la plataforma"
                        )
                        st.success("¡Registro completado de manera exitosa! Ahora puedes iniciar sesión.")
                    except ValueError as val_e:
                        st.error(str(val_e))
                    except Exception as e:
                        logging.exception("Error en proceso de registro")
                        st.error("Error al registrar el usuario.")

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()
