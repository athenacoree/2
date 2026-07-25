import os, tempfile, streamlit as st, pandas as pd
from care_clear_crew.packager import generate_appeal_pdf

def inject_styles():
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600;700;800&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% 50%, #15102a 0%, #080511 100%) !important; color: #F5F5F7 !important; font-family: 'SF Pro Display', sans-serif !important; }
    [data-testid="stSidebar"] { background-color: #0d0a1a !important; background-image: linear-gradient(180deg, #120e25 0%, #06040d 100%) !important; border-right: 2px solid rgba(255, 255, 255, 0.08) !important; box-shadow: 4px 0 20px rgba(0, 0, 0, 0.5); }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; font-weight: 500 !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #007AFF !important; font-weight: 800 !important; }
    .main-header { display: flex; align-items: center; justify-content: space-between; padding: 15px 30px; background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.08); border-radius: 0 0 24px 24px; margin-bottom: 30px; }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-logo { width: 44px; height: 44px; background: linear-gradient(135deg, #007AFF 0%, #8E2DE2 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 8px 16px rgba(0, 122, 255, 0.3); }
    .brand-name { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; background: linear-gradient(135deg, #007AFF 0%, #34C759 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .glass-card { background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 24px; padding: 24px; margin-bottom: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
    .stepper { display: flex; justify-content: space-between; align-items: center; margin: 20px 0; background: rgba(255, 255, 255, 0.02); padding: 16px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05); }
    .step { display: flex; flex-direction: column; align-items: center; text-align: center; flex: 1; }
    .step-icon { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-bottom: 8px; font-size: 14px; }
    .step-active { background: #007AFF; color: white; box-shadow: 0 0 15px rgba(0, 122, 255, 0.6); }
    .step-done { background: #34C759; color: white; }
    .step-pending { background: rgba(255, 255, 255, 0.1); color: rgba(255, 255, 255, 0.4); }
    .step-text { font-size: 11px; font-weight: 500; color: #94A3B8; }
    .badge-approved { background: linear-gradient(135deg, rgba(52, 199, 89, 0.2) 0%, rgba(52, 199, 89, 0.05) 100%); color: #34C759; border: 1px solid rgba(52, 199, 89, 0.3); padding: 8px 18px; border-radius: 30px; font-weight: 700; display: inline-block; font-size: 16px; box-shadow: 0 4px 12px rgba(52, 199, 89, 0.2); }
    .badge-denied { background: linear-gradient(135deg, rgba(255, 59, 48, 0.2) 0%, rgba(255, 59, 48, 0.05) 100%); color: #FF3B30; border: 1px solid rgba(255, 59, 48, 0.3); padding: 8px 18px; border-radius: 30px; font-weight: 700; display: inline-block; font-size: 16px; box-shadow: 0 4px 12px rgba(255, 59, 48, 0.2); }
    html, body, [data-testid="stAppViewContainer"], p, li, span, h1, h2, h3, h4, h5, h6, .glass-card, .glass-card h3, .glass-card h4 { color: #F5F5F7 !important; }
    small, .step-text, .secondary-text, p[data-testid="stMarkdownContainer"] em, [data-testid="stForm"] p, div[data-testid="stMarkdownContainer"] p, .glass-card small, .glass-card .secondary-text { color: #C7C7CC !important; }
    label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] { color: #FFFFFF !important; font-weight: 600 !important; font-size: 14px !important; }
    [data-testid="stFileUploader"] section { background-color: rgba(255, 255, 255, 0.03) !important; border: 1px dashed rgba(255, 255, 255, 0.2) !important; }
    [data-testid="stFileUploaderDropzoneInstructions"] { color: #FFFFFF !important; }
    [data-testid="stFileUploader"] p, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] div { color: #C7C7CC !important; }
    table, th, td, [data-testid="stTable"] td, [data-testid="stTable"] th, .dataframe td, .dataframe th { color: #FFFFFF !important; background-color: rgba(255, 255, 255, 0.02) !important; }
    th { font-weight: bold !important; background-color: rgba(255, 255, 255, 0.08) !important; }
    [data-testid="stExpander"] { background-color: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; }
    [data-testid="stExpander"] summary p { color: #FFFFFF !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

def render_header():
    st.markdown('<div class="main-header"><div class="brand"><div class="brand-logo">🩺</div><div><div class="brand-name">CareClearCrew</div></div></div></div>', unsafe_allow_html=True)

def get_stepper(step: int) -> str:
    s = ["step-pending"] * 4
    i = ["1", "2", "3", "4"]
    for idx in range(4):
        if step > idx + 1: s[idx], i[idx] = "step-done", "✓"
        elif step == idx + 1: s[idx] = "step-active"
    return f"""
    <div class="stepper">
        <div class="step"><div class="step-icon {s[0]}">{i[0]}</div><div class="step-text">Patient Intake</div></div>
        <div class="step"><div class="step-icon {s[1]}">{i[1]}</div><div class="step-text">Insurance Auth</div></div>
        <div class="step"><div class="step-icon {s[2]}">{i[2]}</div><div class="step-text">Clinical Scribe</div></div>
        <div class="step"><div class="step-icon {s[3]}">{i[3]}</div><div class="step-text">Decision</div></div>
    </div>"""

def display_analysis(res: dict, zip_bytes: bytes):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.write(f"### Paciente: **{res.get('patient_name')}**")
        st.write(f"Póliza: **{res.get('policy_number')}**")
        badge = "badge-approved" if res.get("decision", "").upper() == "APROBADO" else "badge-denied"
        st.markdown(f'Decisión Final: <span class="{badge}">{res.get("decision")}</span>', unsafe_allow_html=True)
        st.write(f"Confianza: **{res.get('confidence')}**")
    with col2:
        st.write("### 📥 Descargar Paquete")
        st.download_button("Descargar Informe Completo ZIP", zip_bytes, f"MedAuth_{res.get('patient_name').replace(' ', '_')}.zip", "application/zip", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Resumen de Explicación y Evidencia")
    st.write(res.get("explanation_summary"))
    st.write("#### Evidencia Resaltada:")
    st.info(res.get("evidence"))
    st.write("#### Recomendaciones de Acción:")
    st.success(res.get("recommendations"))
    st.markdown('</div>', unsafe_allow_html=True)

    if "appeal_letter" in res and res["appeal_letter"]:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("✉️ Carta de Apelación Generada")
        st.write(f"**Asunto:** {res['appeal_letter'].get('subject')}")
        st.text_area("Cuerpo", value=res['appeal_letter'].get('body'), height=200)
        with tempfile.TemporaryDirectory() as appeal_td:
            p = os.path.join(appeal_td, "Appeal.pdf")
            generate_appeal_pdf(res["appeal_letter"], p)
            with open(p, "rb") as ind: i_bytes = ind.read()
        st.download_button("Descargar Carta de Apelación (PDF)", i_bytes, f"Carta_Apelacion_{res.get('patient_name').replace(' ', '_')}.pdf", "application/pdf")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Inspección de Criterios (100+ Puntos Evaluados)")
    pts = res.get("evaluated_points", [])
    df = pd.DataFrame(pts)
    cols = [c for c in ["name", "value", "status", "explanation", "source_document", "source_excerpt"] if c in df.columns]
    if cols: df = df[cols]
    if not df.empty:
        st.dataframe(df.style.apply(lambda r: ["background-color: rgba(255, 59, 48, 0.15); color: #FF3B30; font-weight: bold;"] * len(r) if r.get("source_excerpt") == "No encontrado" else [""] * len(r), axis=1), use_container_width=True)
    else: st.dataframe(df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def display_precheck(rep):
    prob_str = rep.approval_probability.replace("%", "").strip()
    try: p_val = int(prob_str)
    except ValueError: p_val = 50
    color = "#34C759" if p_val >= 80 else ("#007AFF" if p_val >= 50 else "#FF3B30")
    st.markdown(f"""
    <div class="glass-card">
        <h3>Probabilidad de Aprobación</h3>
        <div style="font-size: 48px; font-weight: 800; color: {color}; margin-bottom: 10px;">{rep.approval_probability}</div>
        <div style="background-color: rgba(255,255,255,0.08); border-radius: 10px; height: 16px; width: 100%; overflow: hidden; margin-bottom: 15px;">
            <div style="background: {color}; height: 100%; width: {p_val}%; border-radius: 10px;"></div>
        </div>
        <p style="font-size: 14px; color: #94A3B8;">Este score es un pre-check estimativo.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("💡 Recomendaciones")
    st.success(rep.recommendations_to_improve)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("⚠️ Checklist de Datos Faltantes (Ordenado por Impacto)")
    if not rep.missing_critical_items: st.info("No se detectaron elementos críticos faltantes.")
    else:
        for item in rep.missing_critical_items:
            st.markdown(f"""
            <div style="background-color: rgba(255, 59, 48, 0.05); border: 1px solid rgba(255, 59, 48, 0.2); border-radius: 16px; padding: 15px; margin-bottom: 15px;">
                <h4 style="margin: 5px 0 3px 0; color: #FF3B30;">{item.name}</h4>
                <p style="margin: 0; font-size: 14px; color: #E2E8F0;"><b>Impacto:</b> Crítico. {item.explanation}</p>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
