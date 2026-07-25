import os
import streamlit as st
import pandas as pd
from care_clear_crew.history_db import (
    get_all_patterns, clear_all_history, get_users_by_institution,
    update_user_status_and_role, log_activity, get_recent_activity,
    check_and_reset_limits_if_new_month, update_usage_limit_settings
)

def render_settings_view(current_user: dict):
    """Renders LLM Configuration and Insurer patterns list."""
    institution = current_user["institution_name"]
    role = current_user["role"]
    user_id = current_user["id"]
    user_name = current_user["full_name"]

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Configuración de Proveedor de LLM")
    st.write("Configure las credenciales de OpenRouter y gestione la persistencia del sistema.")

    st.text_input("OpenRouter API Key", type="password", value=os.getenv("OPENROUTER_API_KEY", ""))
    st.selectbox("OpenRouter Model", ["meta-llama/llama-3.3-70b-instruct", "grok-2-1212", "gpt-4o-mini"], index=0)
    st.selectbox("Proveedor", ["OpenRouter", "Grok", "OpenAI", "Gemini"])

    if os.getenv("OPENROUTER_API_KEY"):
        st.success("🟢 Conexión de API Key Detectada")
    else:
        st.error("🔴 API Key Faltante o No Configurada")

    st.markdown("---")
    st.subheader("🧠 Perfil de Aprendizaje de Aseguradoras")
    st.write(f"Patrones no escritos e inconsistencias recordadas automáticamente por el sistema para **{institution}**:")

    patterns_list = get_all_patterns(institution)
    if not patterns_list:
        st.info("Aún no se han aprendido patrones o requerimientos especiales de aseguradoras.")
    else:
        df_pat = pd.DataFrame(patterns_list)
        df_pat.columns = ["Aseguradora", "Patrón / Requerimiento Especial Detectado", "Veces Observado", "Última Vez Visto", "Nivel de Confianza"]
        st.dataframe(df_pat, use_container_width=True)

    if role == "administrador":
        st.markdown("---")
        st.write("### Gestión del Sistema")
        if st.button("Limpiar Todo el Historial Clínico de la Institución", key="clear_all_history_btn"):
            clear_all_history(institution)
            log_activity(user_id, user_name, institution, "user_role_changed", "Borrados todos los registros de historial clínico de la institución")
            st.success("¡Historial local borrado de manera exitosa!")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def render_users_management_view(current_user: dict):
    """Renders active accounts list, role triggers, audit logs, and consumption limits."""
    institution = current_user["institution_name"]
    role = current_user["role"]
    user_id = current_user["id"]
    user_name = current_user["full_name"]

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("👥 Gestión de Usuarios e Integridad")
    st.write(f"Administra el acceso, los roles y la seguridad de los usuarios de **{institution}**.")

    st.write("### Cuentas Activas")
    users = get_users_by_institution(institution)

    for u in users:
        col_u1, col_u2, col_u3, col_u4 = st.columns([2, 1, 1, 1])
        with col_u1:
            st.write(f"**{u['full_name']}** ({u['email']})")
        with col_u2:
            st.write(f"Rol: `{u['role']}`")
        with col_u3:
            st.write("Activo" if u['is_active'] else "Desactivado")
        with col_u4:
            if u["id"] == user_id:
                st.write("(Tú)")
            else:
                action_role = "operativo" if u["role"] == "administrador" else "administrador"
                action_active = 0 if u["is_active"] else 1
                btn_lbl_role = "Hacer Operativo" if u["role"] == "administrador" else "Hacer Admin"
                btn_lbl_act = "Desactivar" if u["is_active"] else "Activar"

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(btn_lbl_role, key=f"role_{u['id']}", use_container_width=True):
                        update_user_status_and_role(u["id"], u["is_active"], action_role, institution)
                        log_activity(user_id, user_name, institution, "user_role_changed", f"Cambiado rol de {u['full_name']} a {action_role}")
                        st.success(f"Rol de {u['full_name']} actualizado!")
                        st.rerun()
                with col_btn2:
                    if st.button(btn_lbl_act, key=f"active_{u['id']}", use_container_width=True):
                        update_user_status_and_role(u["id"], action_active, u["role"], institution)
                        log_activity(user_id, user_name, institution, "user_role_changed", f"Cambiado estado de {u['full_name']} a {'activo' if action_active else 'inactivo'}")
                        st.success(f"Estado de cuenta de {u['full_name']} actualizado!")
                        st.rerun()

    st.markdown("---")
    st.write("### 📜 Registro de Actividad Reciente (Auditoría)")
    recent_logs = get_recent_activity(institution, limit=50)
    if not recent_logs:
        st.info("No hay registros de actividad todavía.")
    else:
        df_logs = pd.DataFrame(recent_logs)
        df_logs.columns = ["Fecha/Hora", "Usuario", "Acción", "Detalles"]
        st.dataframe(df_logs, use_container_width=True)

    st.markdown("---")
    st.write("### 📊 Límites de Consumo Mensual de Análisis")
    limit_info = check_and_reset_limits_if_new_month(institution)
    monthly_limit = limit_info.get("monthly_case_limit")
    current_count = limit_info.get("current_month_case_count", 0)

    st.write(f"Consumo este mes: **{current_count}** análisis procesados.")
    if monthly_limit is None:
        st.success("🟢 Consumo ilimitado configurado.")
    else:
        percentage = (current_count / monthly_limit * 100) if monthly_limit > 0 else 100
        st.write(f"Límite configurado: **{monthly_limit}** casos mensuales.")
        st.progress(min(percentage / 100.0, 1.0))
        st.write(f"Consumo al **{round(percentage, 1)}%** del límite.")

    with st.form("limit_form"):
        new_limit = st.number_input("Establecer Nuevo Límite Mensual (0 o vacío para Ilimitado)", min_value=0, value=monthly_limit if monthly_limit else 0)
        new_alert = st.slider("Porcentaje de Alerta de Consumo (%)", min_value=50, max_value=100, value=limit_info.get("alert_threshold_percent", 80))
        limit_btn = st.form_submit_button("Actualizar Ajustes de Consumo", use_container_width=True)

        if limit_btn:
            limit_val = None if new_limit == 0 else int(new_limit)
            update_usage_limit_settings(institution, limit_val, new_alert)
            log_activity(user_id, user_name, institution, "user_role_changed", f"Configurado límite mensual a {new_limit} con alerta al {new_alert}%")
            st.success("¡Límites de consumo mensual actualizados!")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
