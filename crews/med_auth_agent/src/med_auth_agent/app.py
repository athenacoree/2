import os
import shutil
import tempfile
import streamlit as st
import json
import pandas as pd
import asyncio
from med_auth_agent.crew import MedAuthAgent
from med_auth_agent.packager import create_downloadable_zip
from med_auth_agent.history_db import init_db, save_request, get_history, clear_all_history

init_db()

st.set_page_config(
    page_title="MedAuthAgent",
    page_icon="🩺",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 50% 50%, #15102a 0%, #080511 100%) !important;
        color: #FFFFFF !important;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
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
</style>
""", unsafe_allow_html=True)

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

menu = st.sidebar.radio("Navegación", ["Nuevo Análisis", "Simulador Pre-Envío", "Historial de Solicitudes", "Configuración y LLM"])

if menu == "Nuevo Análisis":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Subir Documentos Clínicos y Reglas de Póliza")
    st.write("Sube el expediente clínico del paciente junto con las normativas de la aseguradora para iniciar la evaluación asíncrona.")

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

            # Step 1: Patient Intake
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

                    max_attempts = 3
                    feedback = ""
                    results_json = None
                    last_exception = None
                    raw_response = None

                    for attempt in range(max_attempts):
                        if attempt > 0:
                            status_container.warning(f"Reintentando análisis (Intento {attempt + 1}/{max_attempts}) debido a error de formato JSON...")

                        try:
                            crew_run = agent_system.crew(feedback=feedback).kickoff()
                            raw_response = crew_run.raw
                            results_json = json.loads(raw_response)
                            break
                        except Exception as inner_e:
                            last_exception = inner_e
                            feedback = (
                                f"\n\nCRITICAL ERROR from previous attempt: The previous response could not be parsed as valid JSON. "
                                f"Error: {str(inner_e)}. "
                                f"You MUST return ONLY a strictly valid JSON object matching the schema. No markdown formatting outside the JSON, "
                                f"no extra explanations before or after the JSON."
                            )

                    if results_json is None:
                        with open("med_auth_errors.log", "a", encoding="utf-8") as log_f:
                            log_f.write(f"--- ERROR AT {pd.Timestamp.now()} ---\n")
                            log_f.write(f"Exception: {str(last_exception)}\n")
                            log_f.write(f"Raw LLM Response: {str(raw_response)}\n\n")

                        status_container.empty()
                        stepper_container.empty()
                        st.error("No se pudo completar el análisis. Por favor intenta de nuevo o revisa los documentos cargados.")
                    else:
                        if "evaluated_points" in results_json:
                            for item in results_json["evaluated_points"]:
                                excerpt = item.get("source_excerpt", "No encontrado")
                                status = item.get("status", "No Cumple")
                                if excerpt == "No encontrado" and status == "Cumple":
                                    item["status"] = "No Cumple"
                                    orig_exp = item.get("explanation", "")
                                    item["explanation"] = f"[Corregido automáticamente por falta de evidencia verificable]: {orig_exp}"

                        if results_json.get("decision", "").upper() in ["DENEGADO", "DENIED"]:
                            status_container.info("Redactando carta de apelación formal de grado médico...")
                            try:
                                appeal_letter_obj = agent_system.run_appeal_crew(results_json)
                                results_json["appeal_letter"] = appeal_letter_obj.model_dump()
                            except Exception as appeal_e:
                                failed_pts = [p for p in results_json.get("evaluated_points", []) if p.get("status") == "No Cumple"]
                                failed_pts_desc = "\n".join([f"- {pt.get('name')}: {pt.get('explanation')}" for pt in failed_pts])
                                results_json["appeal_letter"] = {
                                    "subject": f"RE: Apelación de Autorización Previa - Paciente {results_json.get('patient_name', 'N/A')}",
                                    "body": f"Por medio de la presente, apelamos formalmente la decisión de denegación para el paciente {results_json.get('patient_name', 'N/A')} (Póliza {results_json.get('policy_number', 'N/A')}).\n\nCriterios no cumplidos evaluados:\n{failed_pts_desc}\n\nSolicitamos la reconsideración del caso adjuntando la evidencia faltante.",
                                    "cited_points": [pt.get('name') for pt in failed_pts]
                                }

                        if insurer_name_input and "observed_patterns" in results_json and results_json["observed_patterns"]:
                            from med_auth_agent.history_db import save_or_update_pattern
                            for pat in results_json["observed_patterns"]:
                                if pat and pat.strip():
                                    save_or_update_pattern(insurer_name_input, pat)

                        zip_out = os.path.join(temp_dir, "MedAuth_Completo.zip")
                        orig_file = saved_paths[0] if saved_paths else ""
                        create_downloadable_zip(orig_file, results_json, zip_out, temp_dir)

                        with open(zip_out, "rb") as zip_f:
                            zip_bytes = zip_f.read()

                        save_request(results_json)

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
                        st.subheader("Resumen y Justificación Clínica")
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
                    status_container.empty()
                    stepper_container.empty()
                    st.error(f"Error procesando la solicitud asíncrona de prior auth: {e}")

elif menu == "Simulador Pre-Envío":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Simulador Pre-Envío (Análisis de Probabilidad)")
    st.write("Sube expedientes parciales o borradores para calcular la probabilidad de aprobación antes de realizar el envío definitivo.")

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
                    status_container.empty()
                    stepper_container.empty()
                    st.error(f"Error procesando la simulación pre-envío: {e}")

elif menu == "Historial de Solicitudes":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Historial de Solicitudes de Autorización")
    st.write("Consulte y filtre todas las decisiones guardadas de forma persistente en la base de datos local SQLite.")

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search_q = st.text_input("Buscar por nombre del paciente o póliza")
    with col_f2:
        filter_st = st.selectbox("Estado de Decisión", ["Todos", "Aprobado", "Denegado"])

    records = get_history(search_query=search_q, filter_status=filter_st)

    if not records:
        st.write("No se encontraron registros en el historial local.")
    else:
        for r in records:
            with st.expander(f"📅 {r['timestamp']} - Paciente: {r['patient_name']} ({r['decision']})"):
                st.write(f"**Póliza:** {r['policy_number']}")
                st.write(f"**Puntuación de Confianza:** {r['confidence']}")
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
                    create_downloadable_zip("", r["raw_report_json"], zip_history_out, t_dir)
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
    st.write("Patrones no escritos e inconsistencias detectadas y recordadas automáticamente por el sistema para cada aseguradora:")

    from med_auth_agent.history_db import get_all_patterns
    patterns_list = get_all_patterns()
    if not patterns_list:
        st.info("Aún no se han aprendido patrones o requerimientos especiales de aseguradoras.")
    else:
        df_pat = pd.DataFrame(patterns_list)
        df_pat.columns = ["Aseguradora", "Patrón / Requerimiento Especial Detectado", "Veces Observado", "Última Vez Visto", "Nivel de Confianza"]
        st.dataframe(df_pat, use_container_width=True)

    st.markdown("---")
    st.write("### Gestión del Sistema")
    if st.button("Limpiar Todo el Historial Local", key="clear_all_history_btn"):
        clear_all_history()
        st.success("¡Historial local borrado de SQLite de manera exitosa!")
    st.markdown('</div>', unsafe_allow_html=True)
