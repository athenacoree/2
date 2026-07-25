import os
import shutil
import tempfile
import streamlit as st
import json
import pandas as pd
import asyncio
import logging
import traceback
from datetime import datetime

from med_auth_agent.crew import MedAuthAgent
from med_auth_agent.packager import create_downloadable_zip
from med_auth_agent.history_db import (
    init_db, save_request, get_history, clear_all_history,
    get_all_patterns, get_stats_summary, get_stats_by_insurer,
    get_top_denial_reasons, get_users_by_institution, update_user_status_and_role,
    log_activity, get_recent_activity, check_usage_allowed,
    increment_case_count, update_usage_limit_settings, check_and_reset_limits_if_new_month
)
from med_auth_agent.auth import create_user_record, verify_login, require_role
from med_auth_agent.analysis_runner import run_analysis_with_retry

logging.basicConfig(level=logging.ERROR)
init_db()

# Page config
st.set_page_config(
    page_title="MedAuthAgent",
    page_icon="🩺",
    layout="wide"
)

# Custom styles & layout injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 50% 50%, #15102a 0%, #080511 100%) !important;
        color: #F5F5F7 !important;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Elegant and highly visible Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0d0a1a !important;
        background-image: linear-gradient(180deg, #120e25 0%, #06040d 100%) !important;
        border-right: 2px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.5);
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #007AFF !important;
        font-weight: 800 !important;
    }

    .main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 15px 30px;
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 0 0 24px 24px;
        margin-bottom: 30px;
    }
    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .brand-logo {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #007AFF 0%, #8E2DE2 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 8px 16px rgba(0, 122, 255, 0.3);
    }
    .brand-name {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #007AFF 0%, #34C759 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }
    .stepper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 20px 0;
        background: rgba(255, 255, 255, 0.02);
        padding: 16px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        flex: 1;
    }
    .step-icon {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-bottom: 8px;
        font-size: 14px;
    }
    .step-active {
        background: #007AFF;
        color: white;
        box-shadow: 0 0 15px rgba(0, 122, 255, 0.6);
    }
    .step-done {
        background: #34C759;
        color: white;
    }
    .step-pending {
        background: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.4);
    }
    .step-text {
        font-size: 11px;
        font-weight: 500;
        color: #94A3B8;
    }
    .badge-approved {
        background: linear-gradient(135deg, rgba(52, 199, 89, 0.2) 0%, rgba(52, 199, 89, 0.05) 100%);
        color: #34C759;
        border: 1px solid rgba(52, 199, 89, 0.3);
        padding: 8px 18px;
        border-radius: 30px;
        font-weight: 700;
        display: inline-block;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(52, 199, 89, 0.2);
    }
    .badge-denied {
        background: linear-gradient(135deg, rgba(255, 59, 48, 0.2) 0%, rgba(255, 59, 48, 0.05) 100%);
        color: #FF3B30;
        border: 1px solid rgba(255, 59, 48, 0.3);
        padding: 8px 18px;
        border-radius: 30px;
        font-weight: 700;
        display: inline-block;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(255, 59, 48, 0.2);
    }

    /* Text contrast & accessibility improvements for dark theme (glassmorphism) */
    html, body, [data-testid="stAppViewContainer"], p, li, span, h1, h2, h3, h4, h5, h6, .glass-card, .glass-card h3, .glass-card h4 {
        color: #F5F5F7 !important;
    }

    /* Secondary/Helper text & descriptions */
    small, .step-text, .secondary-text, p[data-testid="stMarkdownContainer"] em, [data-testid="stForm"] p, div[data-testid="stMarkdownContainer"] p, .glass-card small, .glass-card .secondary-text {
        color: #C7C7CC !important;
    }

    /* Widget labels */
    label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    /* File Uploader area */
    [data-testid="stFileUploader"] section {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px dashed rgba(255, 255, 255, 0.2) !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] {
        color: #FFFFFF !important;
    }
    [data-testid="stFileUploader"] p, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] div {
        color: #C7C7CC !important;
    }

    /* Table styles */
    table, th, td, [data-testid="stTable"] td, [data-testid="stTable"] th, .dataframe td, .dataframe th {
        color: #FFFFFF !important;
        background-color: rgba(255, 255, 255, 0.02) !important;
    }
    th {
        font-weight: bold !important;
        background-color: rgba(255, 255, 255, 0.08) !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stExpander"] summary p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# Main logo and layout header
st.markdown("""
<div class="main-header">
    <div class="brand">
        <div class="brand-logo">🩺</div>
        <div>
            <div class="brand-name">MedAuthAgent</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- SESSION AND AUTHENTICATION MANAGEMENT -----------------
if "user" not in st.session_state:
    st.session_state["user"] = None

# If user is not authenticated, show Login & registration view inside a Glass Card
if st.session_state["user"] is None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    auth_mode = st.radio("Acceso al Sistema", ["Iniciar Sesión", "Crear cuenta"], horizontal=True)

    if auth_mode == "Iniciar Sesión":
        st.subheader("🔑 Iniciar Sesión en MedAuthAgent")
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

# ----------------- SESSION ACTIVE -----------------
current_user = st.session_state["user"]
institution = current_user["institution_name"]
role = current_user["role"]
user_id = current_user["id"]
user_name = current_user["full_name"]

# Navigation Menus depending on role
menu_options = ["Nuevo Análisis", "Simulador Pre-Envío", "Historial de Solicitudes"]

if role == "administrador":
    menu_options += ["Panel Ejecutivo", "Gestión de Usuarios"]

menu_options += ["Configuración y LLM"]

# Add logout option at sidebar top/side
st.sidebar.markdown(f"### Usuario: **{user_name}**")
st.sidebar.markdown(f"Rol: `{role.capitalize()}`")
st.sidebar.markdown(f"Institución: **{institution}**")

if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    log_activity(user_id, user_name, institution, "logout", "Cierre de sesión manual")
    st.session_state["user"] = None
    st.rerun()

menu = st.sidebar.radio("Navegación", menu_options)

# Helper to check limits before processing
def is_limit_exceeded_block() -> bool:
    if not check_usage_allowed(institution):
        st.error(
            f"🚫 **Límite mensual alcanzado.**\n\n"
            f"Se ha alcanzado el límite mensual de análisis de tu institución ({institution}). "
            f"Contacta a tu administrador para ajustar el límite en el Panel de Gestión."
        )
        return True
    return False


if menu == "Nuevo Análisis":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Subir Documentos Clínicos y Reglas de Póliza")
    st.write("Sube el expediente clínico del paciente junto con las normativas de la aseguradora para iniciar la evaluación autónoma.")

    if not is_limit_exceeded_block():
        insurer_name_input = st.text_input("Nombre de la Aseguradora (Ej: Cigna, Medicare, Blue Cross) - Opcional", key="insurer_name_analysis")

        uploaded_files = st.file_uploader(
            "Arrastra tus documentos médicos aquí o haz clic para subir",
            type=["pdf", "txt", "docx", "csv", "json"],
            accept_multiple_files=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_files:
            if st.button("Iniciar Pipeline de Análisis Autónomo", use_container_width=True):
                status_container = st.empty()
                stepper_container = st.empty()

                # Steppers showing the 4 agents in prior authorization
                stepper_container.markdown("""
                <div class="stepper">
                    <div class="step"><div class="step-icon step-active">1</div><div class="step-text">Patient Intake</div></div>
                    <div class="step"><div class="step-icon step-pending">2</div><div class="step-text">Insurance Auth</div></div>
                    <div class="step"><div class="step-icon step-pending">3</div><div class="step-text">Clinical Scribe</div></div>
                    <div class="step"><div class="step-icon step-pending">4</div><div class="step-text">Decision</div></div>
                </div>
                """, unsafe_allow_html=True)
                status_container.info("Agente 1: Patient Intake - Extrayendo datos demográficos e identificadores del paciente...")

                with tempfile.TemporaryDirectory() as temp_dir:
                    saved_paths = []
                    for f in uploaded_files:
                        fpath = os.path.join(temp_dir, f.name)
                        with open(fpath, "wb") as out_f:
                            out_f.write(f.getbuffer())
                        saved_paths.append(fpath)

                    # Step 2: Insurance Auth
                    stepper_container.markdown("""
                    <div class="stepper">
                        <div class="step"><div class="step-icon step-done">✓</div><div class="step-text">Patient Intake</div></div>
                        <div class="step"><div class="step-icon step-active">2</div><div class="step-text">Insurance Auth</div></div>
                        <div class="step"><div class="step-icon step-pending">3</div><div class="step-text">Clinical Scribe</div></div>
                        <div class="step"><div class="step-icon step-pending">4</div><div class="step-text">Decision</div></div>
                    </div>
                    """, unsafe_allow_html=True)
                    status_container.info("Agente 2: Insurance Authorization - Cruzando cobertura, deducibles, copagos y exclusiones de la póliza...")

                    # Step 3: Clinical Scribe
                    stepper_container.markdown("""
                    <div class="stepper">
                        <div class="step"><div class="step-icon step-done">✓</div><div class="step-text">Patient Intake</div></div>
                        <div class="step"><div class="step-icon step-done">✓</div><div class="step-text">Insurance Auth</div></div>
                        <div class="step"><div class="step-icon step-active">3</div><div class="step-text">Clinical Scribe</div></div>
                        <div class="step"><div class="step-icon step-pending">4</div><div class="step-text">Decision</div></div>
                    </div>
                    """, unsafe_allow_html=True)
                    status_container.info("Agente 3: Clinical Scribe - Convirtiendo datos clínicos no estructurados y validando códigos CPT/ICD-10...")

                    # Step 4: Decision Agent
                    stepper_container.markdown("""
                    <div class="stepper">
                        <div class="step"><div class="step-icon step-done">✓</div><div class="step-text">Patient Intake</div></div>
                        <div class="step"><div class="step-icon step-done">✓</div><div class="step-text">Insurance Auth</div></div>
                        <div class="step"><div class="step-icon step-done">✓</div><div class="step-text">Clinical Scribe</div></div>
                        <div class="step"><div class="step-icon step-active">4</div><div class="step-text">Decision</div></div>
                    </div>
                    """, unsafe_allow_html=True)
                    status_container.info("Agente 4: Decision - Evaluando más de 100 puntos y formulando la decisión final...")

                    try:
                        agent_system = MedAuthAgent(knowledge_files=saved_paths, insurer_name=insurer_name_input)

                        results_json = run_analysis_with_retry(agent_system, max_attempts=3, status_container=status_container)

                        if results_json is None:
                            status_container.empty()
                            stepper_container.empty()
                            st.error("No se pudo completar el análisis. Por favor intenta de nuevo o revisa los documentos cargados.")
                        else:
                            # Verify and auto-correct points missing evidence
                            if "evaluated_points" in results_json:
                                for item in results_json["evaluated_points"]:
                                    excerpt = item.get("source_excerpt", "No encontrado")
                                    status = item.get("status", "No Cumple")
                                    if excerpt == "No encontrado" and status == "Cumple":
                                        item["status"] = "No Cumple"
                                        orig_exp = item.get("explanation", "")
                                        item["explanation"] = f"[Corregido automáticamente por falta de evidencia verificable]: {orig_exp}"

                            # Generate Appeal writing automatically if denied
                            if results_json.get("decision", "").upper() in ["DENEGADO", "DENIED"]:
                                status_container.info("Redactando carta de apelación formal de grado médico...")
                                try:
                                    appeal_letter_obj = agent_system.run_appeal_crew(results_json)
                                    results_json["appeal_letter"] = appeal_letter_obj.model_dump()
                                except Exception as appeal_e:
                                    logging.exception("Error en generación de carta de apelación")
                                    failed_pts = [p for p in results_json.get("evaluated_points", []) if p.get("status") == "No Cumple"]
                                    failed_pts_desc = "\n".join([f"- {pt.get('name')}: {pt.get('explanation')}" for pt in failed_pts])
                                    results_json["appeal_letter"] = {
                                        "subject": f"RE: Apelación de Autorización Previa - Paciente {results_json.get('patient_name', 'N/A')}",
                                        "body": f"Por medio de la presente, apelamos formalmente la decisión de denegación para el paciente {results_json.get('patient_name', 'N/A')} (Póliza {results_json.get('policy_number', 'N/A')}).\n\nCriterios no cumplidos evaluados:\n{failed_pts_desc}\n\nSolicitamos la reconsideración del caso adjuntando la evidencia faltante.",
                                        "cited_points": [pt.get('name') for pt in failed_pts]
                                    }

                            # Save learned patterns
                            if insurer_name_input and "observed_patterns" in results_json and results_json["observed_patterns"]:
                                from med_auth_agent.history_db import save_or_update_pattern
                                for pat in results_json["observed_patterns"]:
                                    if pat and pat.strip():
                                        save_or_update_pattern(insurer_name_input, pat, institution)

                            # Create downloadable bundle ZIP (with credentials)
                            zip_out = os.path.join(temp_dir, "MedAuth_Completo.zip")
                            orig_file = saved_paths[0] if saved_paths else ""
                            create_downloadable_zip(orig_file, results_json, zip_out, temp_dir, user_name, institution)

                            with open(zip_out, "rb") as zip_f:
                                zip_bytes = zip_f.read()

                            # Persist with Multi-tenant isolation credentials
                            save_request(results_json, user_id=user_id, user_name=user_name, institution_name=institution)
                            increment_case_count(institution)
                            log_activity(user_id, user_name, institution, "case_created", f"Nuevo análisis creado para paciente: {results_json.get('patient_name')}")

                            status_container.empty()
                            stepper_container.markdown("""
                            <div class="stepper">
                                <div class="step"><div class="step-icon step-done">✓</div><div class="step-text">Patient Intake</div></div>
                                <div class="step"><div class="step-icon step-done">✓</div><div class="step-text">Insurance Auth</div></div>
                                <div class="step"><div class="step-icon step-done">✓</div><div class="step-text">Clinical Scribe</div></div>
                                <div class="step"><div class="step-icon step-done">✓</div><div class="step-text">Decision</div></div>
                            </div>
                            """, unsafe_allow_html=True)
                            st.success("¡Análisis de autorización completado con total éxito!")

                            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                st.write(f"### Paciente: **{results_json.get('patient_name')}**")
                                st.write(f"Póliza: **{results_json.get('policy_number')}**")

                                if results_json.get("decision", "").upper() == "APROBADO":
                                    st.markdown('Decisión Final: <span class="badge-approved">APROBADO</span>', unsafe_allow_html=True)
                                else:
                                    st.markdown('Decisión Final: <span class="badge-denied">DENEGADO</span>', unsafe_allow_html=True)
                                st.write(f"Puntuación de Confianza: **{results_json.get('confidence')}**")

                            with col2:
                                st.write("### 📥 Descargar Paquete de Entrega")
                                st.write("Obtén el archivo ZIP comprimido listo para el cliente, que contiene el PDF formal, archivos Markdown, y reportes CSV completos.")
                                st.download_button(
                                    label="Descargar Informe Completo ZIP",
                                    data=zip_bytes,
                                    file_name=f"MedAuth_{results_json.get('patient_name').replace(' ', '_')}.zip",
                                    mime="application/zip",
                                    use_container_width=True
                                )
                            st.markdown('</div>', unsafe_allow_html=True)

                            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                            st.subheader("Resumen de Explicación y Evidencia")
                            st.write(results_json.get("explanation_summary"))
                            st.write("#### Evidencia Resaltada:")
                            st.info(results_json.get("evidence"))
                            st.write("#### Recomendaciones de Acción:")
                            st.success(results_json.get("recommendations"))
                            st.markdown('</div>', unsafe_allow_html=True)

                        if results_json and "appeal_letter" in results_json and results_json["appeal_letter"]:
                            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                            st.subheader("✉️ Carta de Apelación Generada")
                            st.write(f"**Asunto:** {results_json['appeal_letter'].get('subject')}")
                            st.text_area("Cuerpo de la Carta", value=results_json['appeal_letter'].get('body'), height=300)
                            with tempfile.TemporaryDirectory() as appeal_td:
                                indiv_appeal_pdf = os.path.join(appeal_td, "Carta_Apelacion.pdf")
                                from med_auth_agent.packager import generate_appeal_pdf
                                generate_appeal_pdf(results_json["appeal_letter"], indiv_appeal_pdf)
                                with open(indiv_appeal_pdf, "rb") as ind_f:
                                    indiv_bytes = ind_f.read()
                            st.download_button(
                                label="Descargar Carta de Apelación (PDF)",
                                data=indiv_bytes,
                                file_name=f"Carta_Apelacion_{results_json.get('patient_name').replace(' ', '_')}.pdf",
                                mime="application/pdf"
                            )
                            st.markdown('</div>', unsafe_allow_html=True)

                        if results_json:
                            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                            st.subheader("Inspección de Criterios (100+ Puntos Evaluados)")
                            st.write("Desglose total asíncrono cruzado contra la base vectorial ChromaDB:")
                            pts = results_json.get("evaluated_points", [])
                            df_pts = pd.DataFrame(pts)
                            cols = ["name", "value", "status", "explanation", "source_document", "source_excerpt"]
                            existing_cols = [c for c in cols if c in df_pts.columns]
                            if existing_cols:
                                df_pts = df_pts[existing_cols]

                            def highlight_no_evidence(row):
                                excerpt = row.get("source_excerpt", "No encontrado")
                                if excerpt == "No encontrado" or pd.isna(excerpt):
                                    return ["background-color: rgba(255, 59, 48, 0.15); color: #FF3B30; font-weight: bold;"] * len(row)
                                return [""] * len(row)

                            if not df_pts.empty:
                                styled_df = df_pts.style.apply(highlight_no_evidence, axis=1)
                                st.dataframe(styled_df, use_container_width=True)
                            else:
                                st.dataframe(df_pts, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                    except Exception as e:
                        logging.exception("Error en pipeline asíncrono de prior auth")
                        status_container.empty()
                        stepper_container.empty()
                        st.error(f"Error procesando la solicitud: {e}")

elif menu == "Simulador Pre-Envío":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Simulador Pre-Envío (Análisis de Probabilidad)")
    st.write("Sube expedientes parciales o borradores para calcular la probabilidad de aprobación antes de realizar el envío definitivo.")

    if not is_limit_exceeded_block():
        insurer_name_input_sim = st.text_input("Nombre de la Aseguradora (Ej: Cigna, Medicare, Blue Cross) - Opcional", key="insurer_name_sim")

        sim_uploaded = st.file_uploader(
            "Sube tus borradores o documentos médicos aquí",
            type=["pdf", "txt", "docx", "csv", "json"],
            accept_multiple_files=True,
            key="sim_uploader"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if sim_uploaded:
            if st.button("Calcular Probabilidad de Aprobación", use_container_width=True):
                status_container = st.empty()
                stepper_container = st.empty()

                stepper_container.markdown("""
                <div class="stepper">
                    <div class="step"><div class="step-icon step-active">1</div><div class="step-text">Ingesta Parcial</div></div>
                    <div class="step"><div class="step-icon step-pending">2</div><div class="step-text">Reglas Cobertura</div></div>
                    <div class="step"><div class="step-icon step-pending">3</div><div class="step-text">Pre-Chequeo</div></div>
                </div>
                """, unsafe_allow_html=True)
                status_container.info("Ejecutando simulación de priorización previa...")

                with tempfile.TemporaryDirectory() as temp_dir:
                    saved_paths = []
                    for f in sim_uploaded:
                        fpath = os.path.join(temp_dir, f.name)
                        with open(fpath, "wb") as out_f:
                            out_f.write(f.getbuffer())
                        saved_paths.append(fpath)

                    try:
                        agent_system = MedAuthAgent(knowledge_files=saved_paths, insurer_name=insurer_name_input_sim)
                        precheck_report = agent_system.run_precheck_crew()

                        status_container.empty()
                        stepper_container.empty()
                        st.success("¡Simulación completada con éxito!")

                        prob_str = precheck_report.approval_probability.replace("%", "").strip()
                        try:
                            prob_val = int(prob_str)
                        except ValueError:
                            prob_val = 50

                        if prob_val >= 80:
                            prog_color = "#34C759"
                        elif prob_val >= 50:
                            prog_color = "#007AFF"
                        else:
                            prog_color = "#FF3B30"

                        st.markdown(f"""
                        <div class="glass-card">
                            <h3>Probabilidad de Aprobación</h3>
                            <div style="font-size: 48px; font-weight: 800; color: {prog_color}; margin-bottom: 10px;">{precheck_report.approval_probability}</div>
                            <div style="background-color: rgba(255,255,255,0.08); border-radius: 10px; height: 16px; width: 100%; overflow: hidden; margin-bottom: 15px;">
                                <div style="background: {prog_color}; height: 100%; width: {prob_val}%; border-radius: 10px;"></div>
                            </div>
                            <p style="font-size: 14px; color: #94A3B8;">Este score es un pre-check estimativo basado únicamente en los documentos proporcionados en esta simulación.</p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        st.subheader("💡 Recomendaciones para Mejorar tu Probabilidad")
                        st.success(precheck_report.recommendations_to_improve)
                        st.markdown('</div>', unsafe_allow_html=True)

                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        st.subheader("⚠️ Checklist de Datos/Documentos Faltantes (Ordenado por Impacto)")

                        missing_items = precheck_report.missing_critical_items
                        if not missing_items:
                            st.info("No se detectaron elementos críticos faltantes importantes. ¡Tu caso parece muy completo!")
                        else:
                            for idx, item in enumerate(missing_items):
                                st.markdown(f"""
                                <div style="background-color: rgba(255, 59, 48, 0.05); border: 1px solid rgba(255, 59, 48, 0.2); border-radius: 16px; padding: 15px; margin-bottom: 15px;">
                                    <h4 style="margin: 5px 0 3px 0; color: #FF3B30;">{item.name}</h4>
                                    <p style="margin: 0; font-size: 14px; color: #E2E8F0;"><b>Impacto:</b> Crítico. {item.explanation}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    except Exception as e:
                        logging.exception("Error en simulador pre-envío")
                        status_container.empty()
                        stepper_container.empty()
                        st.error(f"Error procesando la simulación pre-envío: {e}")

elif menu == "Historial de Solicitudes":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Historial de Solicitudes de Autorización")
    st.write("Consulta y filtra todas las decisiones guardadas de forma persistente.")

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search_q = st.text_input("Buscar por nombre del paciente o póliza")
    with col_f2:
        filter_st = st.selectbox("Estado de Decisión", ["Todos", "Aprobado", "Denegado"])

    # Fetch records based on Role and Institution
    records = get_history(
        institution_name=institution,
        user_id=user_id,
        search_query=search_q,
        filter_status=filter_st,
        role=role
    )

    if not records:
        st.write("No se encontraron registros en tu historial para esta institución.")
    else:
        for r in records:
            title_header = f"📅 {r['timestamp']} - Paciente: {r['patient_name']} ({r['decision']})"
            if role == "administrador":
                title_header += f" | Creado por: {r.get('created_by_name', 'N/A')}"

            with st.expander(title_header):
                st.write(f"**Póliza:** {r['policy_number']}")
                st.write(f"**Puntuación de Confianza:** {r['confidence']}")
                st.write(f"**Ledger Record Hash (Huella de Integridad):** `{r.get('record_hash', 'N/A')}`")
                st.write(f"**Justificación:** {r['explanation_summary']}")
                st.write(f"**Evidencia:** {r['evidence']}")
                st.write(f"**Recomendaciones:** {r['recommendations']}")

                if "appeal_letter" in r["raw_report_json"] and r["raw_report_json"]["appeal_letter"]:
                    st.write("---")
                    st.write("### ✉️ Carta de Apelación")
                    st.write(f"**Asunto:** {r['raw_report_json']['appeal_letter'].get('subject')}")
                    st.text_area("Cuerpo de la Carta", value=r['raw_report_json']['appeal_letter'].get('body'), height=150, key=f"hist_appeal_{r['id']}")

                with tempfile.TemporaryDirectory() as t_dir:
                    zip_history_out = os.path.join(t_dir, "MedAuth_Recuperado.zip")
                    create_downloadable_zip("", r["raw_report_json"], zip_history_out, t_dir, r.get('created_by_name', 'N/A'), institution)
                    with open(zip_history_out, "rb") as z_h_f:
                        z_h_bytes = z_h_f.read()

                st.download_button(
                    label="Descargar ZIP de este Registro",
                    data=z_h_bytes,
                    file_name=f"MedAuth_Recuperado_{r['patient_name'].replace(' ', '_')}.zip",
                    mime="application/zip",
                    key=f"hist_dl_{r['id']}"
                )
    st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Panel Ejecutivo" and role == "administrador":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📊 Panel Ejecutivo y Analíticas de Consumo")
    st.write(f"Analíticas acumulativas de la plataforma MedAuthAgent para **{institution}**.")

    stats = get_stats_summary(institution)

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Casos Totales", stats["total_cases"])
    with col_s2:
        st.metric("Tasa de Aprobación Global", f"{stats['approved_rate']}%")
    with col_s3:
        st.metric("Horas de Trabajo Ahorradas", f"{round(stats['total_cases'] * 2.5, 1)} hrs")

    col_g1, col_g2 = st.columns([1, 1])
    with col_g1:
        st.write("### Casos por Aseguradora")
        insurer_data = get_stats_by_insurer(institution)
        if not insurer_data:
            st.info("No hay suficientes datos gráficos de aseguradoras.")
        else:
            df_ins = pd.DataFrame(insurer_data)
            df_ins.columns = ["Aseguradora", "Cantidad"]
            st.dataframe(df_ins, use_container_width=True)

    with col_g2:
        st.write("### Denegaciones Recientes y Justificaciones")
        denial_reasons = get_top_denial_reasons(institution)
        if not denial_reasons:
            st.info("No se registran denegaciones en tu historial.")
        else:
            df_denials = pd.DataFrame(denial_reasons)
            df_denials.columns = ["Explicación de Denegación", "Paciente"]
            st.dataframe(df_denials, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Gestión de Usuarios" and role == "administrador":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("👥 Gestión de Usuarios e Integridad")
    st.write(f"Administra el acceso, los roles y la seguridad de los usuarios de **{institution}**.")

    # 1. User Management List and Role Toggling
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
            # Let administrator modify other users, but don't let them self-lock / self-demote
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

    # 2. Activity logs
    st.markdown("---")
    st.write("### 📜 Registro de Actividad Reciente (Auditoría)")
    recent_logs = get_recent_activity(institution, limit=50)
    if not recent_logs:
        st.info("No hay registros de actividad todavía.")
    else:
        df_logs = pd.DataFrame(recent_logs)
        df_logs.columns = ["Fecha/Hora", "Usuario", "Acción", "Detalles"]
        st.dataframe(df_logs, use_container_width=True)

    # 3. Monthly Limits and Consumption Setting
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

elif menu == "Configuración y LLM":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Configuración de Proveedor de LLM")
    st.write("Configure las credenciales de OpenRouter y gestione la persistencia del sistema.")

    op_key = st.text_input("OpenRouter API Key", type="password", value=os.getenv("OPENROUTER_API_KEY", ""))
    op_model = st.selectbox("OpenRouter Model", [
        "meta-llama/llama-3.3-70b-instruct",
        "grok-2-1212",
        "gpt-4o-mini"
    ], index=0)
    op_provider = st.selectbox("Proveedor", ["OpenRouter", "Grok", "OpenAI", "Gemini"])

    if op_key:
        st.success("🟢 Conexión de API Key Detectada")
    else:
        st.error("🔴 API Key Faltante o No Configurada")

    st.markdown("---")
    st.subheader("🧠 Perfil de Aprendizaje de Aseguradoras")
    st.write(f"Patrones no escritos e inconsistencias recordadas automáticamente por el sistema para **{institution}**:")

    # Isolated insurer pattern listing
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
            clear_all_history()
            log_activity(user_id, user_name, institution, "user_role_changed", "Borrados todos los registros de historial clínico de la institución")
            st.success("¡Historial local borrado de manera exitosa!")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
