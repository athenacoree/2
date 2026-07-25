import os
import tempfile
import streamlit as st
from med_auth_agent.history_db import get_history
from med_auth_agent.packager import create_downloadable_zip

def render_history_view(current_user: dict):
    """Renders the request history with search, filters, expanders, and downloaders."""
    institution = current_user["institution_name"]
    role = current_user["role"]
    user_id = current_user["id"]

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
