import os, tempfile, logging, streamlit as st, pandas as pd
from med_auth_agent.crew import MedAuthAgent
from med_auth_agent.packager import create_downloadable_zip, generate_appeal_pdf
from med_auth_agent.history_db import save_request, increment_case_count, log_activity, check_usage_allowed, save_or_update_pattern
from med_auth_agent.analysis_runner import run_analysis_with_retry
from med_auth_agent.ui.components import get_stepper, display_analysis, display_precheck

def check_limit(inst: str) -> bool:
    if not check_usage_allowed(inst):
        st.error(f"🚫 **Límite mensual alcanzado.**\n\nSe ha alcanzado el límite para ({inst}).")
        return True
    return False

def render_new_analysis(user: dict):
    inst, uid, uname = user["institution_name"], user["id"], user["full_name"]
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Subir Documentos Clínicos y Reglas de Póliza")
    if check_limit(inst):
        st.markdown('</div>', unsafe_allow_html=True); return

    ins_name = st.text_input("Aseguradora (Cigna, Medicare...) - Opcional", key="ins_analysis")
    up_files = st.file_uploader("Arrastra tus documentos médicos aquí", type=["pdf", "txt", "docx", "csv", "json"], accept_multiple_files=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if up_files and st.button("Iniciar Pipeline de Análisis Autónomo", use_container_width=True):
        status, stepper = st.empty(), st.empty()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for f in up_files:
                p = os.path.join(temp_dir, f.name)
                with open(p, "wb") as out: out.write(f.getbuffer())
                paths.append(p)

            try:
                agent = MedAuthAgent(knowledge_files=paths, insurer_name=ins_name)
                stepper.markdown(get_stepper(1), unsafe_allow_html=True)
                status.info("Agente 1: Patient Intake - Procesando...")

                stepper.markdown(get_stepper(2), unsafe_allow_html=True)
                status.info("Agente 2: Insurance Auth - Evaluando...")

                stepper.markdown(get_stepper(3), unsafe_allow_html=True)
                status.info("Agente 3: Clinical Scribe - Validando...")

                stepper.markdown(get_stepper(4), unsafe_allow_html=True)
                status.info("Agente 4: Decision - Generando reporte...")

                res = run_analysis_with_retry(agent, max_attempts=3, status_container=status)
                if not res:
                    status.empty(); stepper.empty(); st.error("No se pudo completar el análisis."); return

                if "evaluated_points" in res:
                    for item in res["evaluated_points"]:
                        if item.get("source_excerpt") == "No encontrado" and item.get("status") == "Cumple":
                            item["status"] = "No Cumple"
                            item["explanation"] = f"[Corregido]: {item.get('explanation')}"

                if res.get("decision", "").upper() in ["DENEGADO", "DENIED"]:
                    try:
                        res["appeal_letter"] = agent.run_appeal_crew(res).model_dump()
                    except Exception:
                        failed = [p for p in res.get("evaluated_points", []) if p.get("status") == "No Cumple"]
                        res["appeal_letter"] = {
                            "subject": f"RE: Apelación - Paciente {res.get('patient_name')}",
                            "body": f"Apelamos formalmente la decisión.\n\nCriterios:\n" + "\n".join([f"- {x.get('name')}" for x in failed]),
                            "cited_points": [x.get('name') for x in failed]
                        }

                if ins_name and res.get("observed_patterns"):
                    for pat in res["observed_patterns"]:
                        if pat and pat.strip(): save_or_update_pattern(ins_name, pat, inst)

                zip_out = os.path.join(temp_dir, "MedAuth_Completo.zip")
                create_downloadable_zip(paths[0] if paths else "", res, zip_out, temp_dir, uname, inst)
                with open(zip_out, "rb") as zf: z_bytes = zf.read()

                save_request(res, user_id=uid, user_name=uname, institution_name=inst)
                increment_case_count(inst)
                log_activity(uid, uname, inst, "case_created", f"Nuevo análisis creado: {res.get('patient_name')}")

                status.empty()
                stepper.markdown(get_stepper(5), unsafe_allow_html=True)
                st.success("¡Análisis completado con éxito!")
                display_analysis(res, z_bytes)
            except Exception as e:
                logging.exception("Error en pipeline asíncrono")
                status.empty(); stepper.empty(); st.error(f"Error: {e}")

def render_precheck_simulator(user: dict):
    inst = user["institution_name"]
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Simulador Pre-Envío (Análisis de Probabilidad)")
    if check_limit(inst):
        st.markdown('</div>', unsafe_allow_html=True); return

    ins_name = st.text_input("Nombre de la Aseguradora - Opcional", key="insurer_name_sim")
    uploaded = st.file_uploader("Sube tus borradores o documentos aquí", type=["pdf", "txt", "docx", "csv", "json"], accept_multiple_files=True, key="sim_uploader")
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded and st.button("Calcular Probabilidad de Aprobación", use_container_width=True):
        status, stepper = st.empty(), st.empty()
        stepper.markdown("""
        <div class="stepper">
            <div class="step"><div class="step-icon step-active">1</div><div class="step-text">Ingesta Parcial</div></div>
            <div class="step"><div class="step-icon step-pending">2</div><div class="step-text">Reglas Cobertura</div></div>
            <div class="step"><div class="step-icon step-pending">3</div><div class="step-text">Pre-Chequeo</div></div>
        </div>""", unsafe_allow_html=True)
        status.info("Ejecutando simulación...")

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for f in uploaded:
                p = os.path.join(temp_dir, f.name)
                with open(p, "wb") as out: out.write(f.getbuffer())
                paths.append(p)

            try:
                agent = MedAuthAgent(knowledge_files=paths, insurer_name=ins_name)
                rep = agent.run_precheck_crew()
                status.empty(); stepper.empty()
                st.success("¡Simulación completada con éxito!")
                display_precheck(rep)
            except Exception as e:
                logging.exception("Error en simulador")
                status.empty(); stepper.empty(); st.error(f"Error: {e}")
