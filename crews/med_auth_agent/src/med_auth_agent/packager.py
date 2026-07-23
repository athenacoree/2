import os
import zipfile
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_decision_pdf(report_data: dict, output_pdf_path: str):
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
        [Paragraph("<b>Confianza:</b>", body_style), Paragraph(f"{report_data.get('confidence', 'N/A')}", body_style)]
    ]
    summary_table = Table(summary_data, colWidths=[120, 400])
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

    elements.append(Paragraph("Evaluación Detallada de Criterios (Muestra de Puntos)", section_style))

    table_rows = [[Paragraph("Nombre Criterio", header_style), Paragraph("Valor Evaluado", header_style), Paragraph("Estado", header_style), Paragraph("Explicación", header_style)]]

    evaluated_points = report_data.get('evaluated_points', [])
    for pt in evaluated_points[:35]:
        row = [
            Paragraph(pt.get('name', 'N/A'), cell_style),
            Paragraph(pt.get('value', 'N/A'), cell_style),
            Paragraph(pt.get('status', 'N/A'), cell_style),
            Paragraph(pt.get('explanation', 'N/A'), cell_style)
        ]
        table_rows.append(row)

    pts_table = Table(table_rows, colWidths=[130, 100, 60, 240])
    pts_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))
    elements.append(pts_table)

    doc.build(elements)

def generate_project_explanation(output_md_path: str):
    explanation_content = """# EXPLICACIÓN DEL PROYECTO - MEDAUTHAGENT

MedAuthAgent es un producto avanzado de autorización médica prioritaria totalmente autónomo. Utiliza agentes inteligentes potenciados por CrewAI para contrastar documentos clínicos contra políticas y normativas de aseguradoras de manera transparente y eficiente.

## Arquitectura del Sistema
El sistema consta de:
1. **Motor de Agentes de CrewAI**: Un Medical Prior Authorization Officer que evalúa de forma detallada toda la documentación utilizando RAG (Retrieval-Augmented Generation).
2. **Knowledge Sources de CrewAI**: Permite la integración directa y automatizada de PDFs (`PDFKnowledgeSource`), textos planos (`TXTKnowledgeSource`) y archivos Word (`DOCXKnowledgeSource`).
3. **Búsqueda Semántica**: Se integra la herramienta `PDFSearchTool` para realizar búsquedas específicas sobre los documentos médicos.
4. **Almacenamiento de Vectores**: El sistema utiliza **ChromaDB** de manera interna para persistir e indexar los documentos vectorizados.
5. **Capa de Abstracción de LLM**: Configurable para OpenRouter, optimizando costos y calidad utilizando modelos líderes del mercado (como Llama 3.3 70B).
6. **Reportes Avanzados**: Generación automática de informes PDF usando la biblioteca ReportLab y exportación estructurada en JSON.
7. **Interfaz Streamlit**: Diseñada con una estética moderna de iPhone, Glassmorphism, efectos de desenfoque y temática médica profesional (azul, verde y blanco).

## Flujo de Trabajo
1. El usuario carga la documentación médica (historial, exámenes, cartas de justificación) y la póliza correspondiente.
2. Los documentos se indexan de manera automática mediante los Knowledge Sources.
3. El agente de autorización médica analiza meticulosamente el caso evaluando más de 100 puntos de control divididos en 7 categorías críticas.
4. Se emite la decisión estructurada (Aprobado o Denegado), junto con una puntuación de confianza, evidencias encontradas y recomendaciones detalladas.
5. Se empaquetan todos los entregables en un archivo comprimido `.ZIP` disponible de inmediato para su descarga.

## Lista de Categorías de Evaluación (105+ Puntos Totales)
1. **Datos del paciente (15+ puntos)**: Identificación de nombre completo, fecha de nacimiento, ID de afiliado, género, dirección, etc.
2. **Coberura de la póliza (15+ puntos)**: Estado activo, deducible, copago, exclusión de pre-existencias, etc.
3. **Documentación presentada (15+ puntos)**: Presencia de notas médicas, firmas legibles, consistencia de fechas, derivaciones clínicas.
4. **Requisitos de la aseguradora (15+ puntos)**: Evidencia de tratamientos conservadores fallidos, pruebas de diagnóstico por imagen realizadas.
5. **Cumplimiento y regulaciones (15+ puntos)**: Cumplimiento HIPAA, firmas de médicos calificados, plazos estatales.
6. **Análisis de riesgos (15+ puntos)**: Contraindicaciones del procedimiento, condiciones crónicas del paciente, riesgos de retraso.
7. **Factores de decisión (15+ puntos)**: Alineación diagnóstica con guías médicas estándar, CPT/ICD códigos correctos.
"""
    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write(explanation_content)

def create_downloadable_zip(original_file_path: str, report_data: dict, output_zip_path: str, temp_dir: str):
    os.makedirs(temp_dir, exist_ok=True)

    pdf_report_path = os.path.join(temp_dir, "informe_decision.pdf")
    generate_decision_pdf(report_data, pdf_report_path)

    md_path = os.path.join(temp_dir, "EXPLICACION_PROYECTO.md")
    generate_project_explanation(md_path)

    json_path = os.path.join(temp_dir, "analisis_puntos.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if original_file_path and os.path.exists(original_file_path):
            zipf.write(original_file_path, os.path.basename(original_file_path))
        zipf.write(pdf_report_path, "informe_decision.pdf")
        zipf.write(md_path, "EXPLICACION_PROYECTO.md")
        zipf.write(json_path, "analisis_puntos.json")
