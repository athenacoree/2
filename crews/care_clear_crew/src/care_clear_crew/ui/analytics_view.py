import streamlit as st
import pandas as pd
from care_clear_crew.history_db import get_stats_summary, get_stats_by_insurer, get_top_denial_reasons

def render_analytics_view(current_user: dict):
    """Renders the Executive Analytics Dashboard (Panel Ejecutivo)."""
    institution = current_user["institution_name"]
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📊 Panel Ejecutivo y Analíticas de Consumo")
    st.write(f"Analíticas acumulativas de la plataforma CareClearCrew para **{institution}**.")

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
