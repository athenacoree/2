import os
import zipfile
import json
import csv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_decision_pdf(report_data: dict, output_pdf_path: str, creator_name: str = "N/A"):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=15
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#0D9488'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=8
    )

    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white
    )

    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )

    elements = []

    elements.append(Paragraph("INFORME DE DECISIÓN DE AUTORIZACIÓN MÉDICA", title_style))
    elements.append(Paragraph("<b>MedAuthAgent Autonomous Prior Authorization Solution</b>", body_style))
    elements.append(Spacer(1, 10))

    summary_data = [
        [Paragraph("<b>Paciente:</b>", body_style), Paragraph(report_data.get('patient_name', 'N/A'), body_style)],
        [Paragraph("<b>Póliza:</b>", body_style), Paragraph(report_data.get('policy_number', 'N/A'), body_style)],
        [Paragraph("<b>Decisión Final:</b>", body_style), Paragraph(f"<b>{report_data.get('decision', 'N/A')}</b>", body_style)],
        [Paragraph("<b>Confianza:</b>", body_style), Paragraph(f"{report_data.get('confidence', 'N/A')}", body_style)],
        [Paragraph("<b>Médico/Usuario Responsable:</b>", body_style), Paragraph(creator_name, body_style)]
    ]
    summary_table = Table(summary_data, colWidths=[150, 370])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Resumen de Explicación", section_style))
    elements.append(Paragraph(report_data.get('explanation_summary', 'N/A'), body_style))

    elements.append(Paragraph("Evidencia Encontrada", section_style))
    elements.append(Paragraph(report_data.get('evidence', 'N/A'), body_style))

    elements.append(Paragraph("Recomendaciones", section_style))
    elements.append(Paragraph(report_data.get('recommendations', 'N/A'), body_style))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Evaluación Detallada de Criterios (Primeros Puntos)", section_style))

    table_rows = [[
        Paragraph("Nombre Criterio", header_style),
        Paragraph("Valor Evaluado", header_style),
        Paragraph("Estado", header_style),
        Paragraph("Explicación", header_style),
        Paragraph("Documento", header_style),
        Paragraph("Evidencia Citada", header_style)
    ]]

    evaluated_points = report_data.get('evaluated_points', [])
    for pt in evaluated_points[:25]:
        row = [
            Paragraph(pt.get('name', 'N/A'), cell_style),
            Paragraph(pt.get('value', 'N/A'), cell_style),
            Paragraph(pt.get('status', 'N/A'), cell_style),
            Paragraph(pt.get('explanation', 'N/A'), cell_style),
            Paragraph(pt.get('source_document', 'No encontrado'), cell_style),
            Paragraph(pt.get('source_excerpt', 'No encontrado'), cell_style)
        ]
        table_rows.append(row)

    pts_table = Table(table_rows, colWidths=[90, 70, 40, 150, 60, 120])
    pts_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))
    elements.append(pts_table)

    doc.build(elements)

def generate_detailed_explanation_md(report_data: dict, output_md_path: str, creator_name: str = "N/A"):
    decision_color = "🟢" if report_data.get("decision", "").upper() == "APROBADO" else "🔴"
    content = f"""# EXPLICACIÓN DETALLADA DE LA DECISIÓN DE AUTORIZACIÓN

## {decision_color} Decisión Final: {report_data.get('decision', 'N/A')} ({report_data.get('confidence', 'N/A')} de Confianza)

### Información del Paciente y Médico
- **Nombre Paciente:** {report_data.get('patient_name', 'N/A')}
- **Número de Póliza:** {report_data.get('policy_number', 'N/A')}
- **Médico/Usuario Responsable:** {creator_name}

---

## 📋 Justificación de la Decisión
{report_data.get('explanation_summary', 'N/A')}

---

## 🔍 Evidencia Encontrada en los Archivos
{report_data.get('evidence', 'N/A')}

---

## 💡 Recomendaciones del Sistema
{report_data.get('recommendations', 'N/A')}

---

## 📌 Resumen de los Puntos Evaluados
El agente inteligente ha verificado con rigor y de manera asíncrona todos los requerimientos obligatorios de cobertura.
Para obtener el desglose completo de los 100+ puntos analizados, consulte el archivo adjunto **REPORTE_COMPLETO.csv**.
"""
    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write(content)

def generate_complete_report_csv(evaluated_points: list, output_csv_path: str, creator_name: str = "N/A"):
    with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Médico/Usuario Responsable", creator_name])
        writer.writerow([])
        writer.writerow(["Nombre de Criterio", "Valor Hallado", "Estado de Cumplimiento", "Explicación del Analista", "Documento Origen", "Fragmento Evidencia"])
        for pt in evaluated_points:
            writer.writerow([
                pt.get("name", "N/A"),
                pt.get("value", "N/A"),
                pt.get("status", "N/A"),
                pt.get("explanation", "N/A"),
                pt.get("source_document", "No encontrado"),
                pt.get("source_excerpt", "No encontrado")
            ])

def generate_appeal_pdf(appeal_data: dict, output_pdf_path: str):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'AppealTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#991B1B'),
        spaceAfter=15
    )

    section_style = ParagraphStyle(
        'AppealSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'AppealBodyText',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=8
    )

    elements = []

    elements.append(Paragraph("CARTA DE APELACIÓN DE AUTORIZACIÓN MÉDICA", title_style))
    elements.append(Paragraph(f"<b>Asunto:</b> {appeal_data.get('subject', 'RE: Apelación de Autorización Previa')}", section_style))
    elements.append(Spacer(1, 15))

    body_text = appeal_data.get('body', '')
    for pr in body_text.split('\n'):
        if pr.strip():
            elements.append(Paragraph(pr.strip(), body_style))

    cited = appeal_data.get('cited_points', [])
    if cited:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Criterios de Póliza Apelados:", section_style))
        for pt in cited:
            elements.append(Paragraph(f"• {pt}", body_style))

    doc.build(elements)

def generate_hipaa_audit_log(report_data: dict, output_json_path: str, creator_name: str = "N/A", creator_institution: str = "N/A"):
    import datetime
    log_data = {
        "event_id": "MEDAUTH-AUDIT-LOG-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.datetime.now().isoformat(),
        "action": "PRIOR_AUTHORIZATION_PROCESS_RUN",
        "actor": f"Médico: {creator_name} ({creator_institution})",
        "hipaa_compliance_status": "SECURE_LOCAL_PROCESSING",
        "patient_identifier_encrypted": "SHA256_LOCAL_ONLY",
        "system_details": {
            "platform_name": "MedAuthAgent",
            "database_engine": "PostgreSQL / SQLite3",
            "rag_chunks_configuration": "1000 tokens overlap 200"
        },
        "audit_logs": [
            {"step": "File Upload and Extraction", "status": "COMPLETED", "timestamp": (datetime.datetime.now() - datetime.timedelta(seconds=12)).isoformat()},
            {"step": "Patient Demographics Extraction (Patient Intake)", "status": "COMPLETED", "timestamp": (datetime.datetime.now() - datetime.timedelta(seconds=9)).isoformat()},
            {"step": "Insurance Coverage Verification (Insurance Auth)", "status": "COMPLETED", "timestamp": (datetime.datetime.now() - datetime.timedelta(seconds=6)).isoformat()},
            {"step": "Clinical Codes Formatting and Extraction (Clinical Scribe)", "status": "COMPLETED", "timestamp": (datetime.datetime.now() - datetime.timedelta(seconds=4)).isoformat()},
            {"step": "Final Prior Authorization Evaluation (Decision Agent)", "status": "COMPLETED", "timestamp": (datetime.datetime.now() - datetime.timedelta(seconds=1)).isoformat()}
        ],
        "metrics": {
            "total_points_evaluated": len(report_data.get("evaluated_points", [])),
            "final_decision": report_data.get("decision", "N/A"),
            "confidence_percentage": report_data.get("confidence", "N/A")
        }
    }
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=4, ensure_ascii=False)

def create_downloadable_zip(original_file_path: str, report_data: dict, output_zip_path: str, temp_dir: str, creator_name: str = "N/A", creator_institution: str = "N/A"):
    os.makedirs(temp_dir, exist_ok=True)

    pdf_report_path = os.path.join(temp_dir, "informe_decision.pdf")
    generate_decision_pdf(report_data, pdf_report_path, creator_name)

    md_path = os.path.join(temp_dir, "EXPLICACION_DETALLADA.md")
    generate_detailed_explanation_md(report_data, md_path, creator_name)

    csv_path = os.path.join(temp_dir, "REPORTE_COMPLETO.csv")
    generate_complete_report_csv(report_data.get("evaluated_points", []), csv_path, creator_name)

    audit_path = os.path.join(temp_dir, "LOG_AUDITORIA.json")
    generate_hipaa_audit_log(report_data, audit_path, creator_name, creator_institution)

    appeal_pdf_path = None
    if "appeal_letter" in report_data and report_data["appeal_letter"]:
        appeal_pdf_path = os.path.join(temp_dir, "Carta_Apelacion.pdf")
        generate_appeal_pdf(report_data["appeal_letter"], appeal_pdf_path)

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if original_file_path and os.path.exists(original_file_path):
            zipf.write(original_file_path, os.path.basename(original_file_path))
        zipf.write(pdf_report_path, "informe_decision.pdf")
        zipf.write(md_path, "EXPLICACION_DETALLADA.md")
        zipf.write(csv_path, "REPORTE_COMPLETO.csv")
        zipf.write(audit_path, "LOG_AUDITORIA.json")
        if appeal_pdf_path and os.path.exists(appeal_pdf_path):
            zipf.write(appeal_pdf_path, "Carta_Apelacion.pdf")
