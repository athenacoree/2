import os
import unittest
import tempfile
import json
import csv
from med_auth_agent.tests import BaseTestCase, create_sample_report_data, create_sample_appeal_data
from med_auth_agent.packager import (
    generate_decision_pdf, generate_detailed_explanation_md,
    generate_complete_report_csv, generate_appeal_pdf,
    generate_hipaa_audit_log, create_downloadable_zip
)

class TestExport(BaseTestCase):
    """
    Unit tests for packager.py export capabilities.
    Verifies clean Generation of PDF Reports, Appeal Letters, Markdown summaries,
    CSV worksheets (with 100+ items format), HIPAA JSON Audit Logs, and modular ZIP compilations.
    """

    def test_pdf_report_and_appeal_generation(self):
        report_data = create_sample_report_data()
        appeal_data = create_sample_appeal_data()

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, "test_report.pdf")
            appeal_pdf_path = os.path.join(temp_dir, "test_appeal.pdf")

            # Generate primary Decision PDF
            generate_decision_pdf(report_data, pdf_path, creator_name="Dr. House")
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 0)

            # Generate secondary Appeal PDF
            generate_appeal_pdf(appeal_data, appeal_pdf_path)
            self.assertTrue(os.path.exists(appeal_pdf_path))
            self.assertGreater(os.path.getsize(appeal_pdf_path), 0)

    def test_markdown_and_csv_generation(self):
        report_data = create_sample_report_data()

        with tempfile.TemporaryDirectory() as temp_dir:
            md_path = os.path.join(temp_dir, "EXPLICACION_DETALLADA.md")
            csv_path = os.path.join(temp_dir, "REPORTE_COMPLETO.csv")

            # Generate markdown explanation
            generate_detailed_explanation_md(report_data, md_path, creator_name="Dr. Gray")
            self.assertTrue(os.path.exists(md_path))
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("Juan Perez", content)
                self.assertIn("Aprobado", content)

            # Generate complete CSV report worksheet
            generate_complete_report_csv(report_data["evaluated_points"], csv_path, creator_name="Dr. Gray")
            self.assertTrue(os.path.exists(csv_path))
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                # Row 0 contains "Médico/Usuario Responsable", "Dr. Gray"
                self.assertEqual(rows[0][0], "Médico/Usuario Responsable")
                self.assertEqual(rows[0][1], "Dr. Gray")

    def test_hipaa_audit_log_json(self):
        report_data = create_sample_report_data()

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = os.path.join(temp_dir, "LOG_AUDITORIA.json")

            # Generate JSON audit logs
            generate_hipaa_audit_log(
                report_data, json_path, creator_name="Dr. Gray", creator_institution="Clinica Alfa"
            )
            self.assertTrue(os.path.exists(json_path))

            # Validate schema and fields of HIPAA audit
            with open(json_path, "r", encoding="utf-8") as f:
                audit = json.load(f)
                self.assertEqual(audit["action"], "PRIOR_AUTHORIZATION_PROCESS_RUN")
                self.assertIn("Dr. Gray", audit["actor"])
                self.assertIn("Clinica Alfa", audit["actor"])
                self.assertEqual(audit["metrics"]["final_decision"], "Aprobado")

    def test_complete_downloadable_zip_bundling(self):
        report_data = create_sample_report_data()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock original document uploaded by user
            orig_doc = os.path.join(temp_dir, "paciente_intake.txt")
            with open(orig_doc, "w", encoding="utf-8") as f:
                f.write("Informacion del Paciente Juan Perez")

            zip_output = os.path.join(temp_dir, "case_bundle.zip")

            # Create download ZIP with all artifacts
            create_downloadable_zip(
                orig_doc, report_data, zip_output, temp_dir,
                creator_name="Dr. Gray", creator_institution="Clinica Alfa"
            )

            self.assertTrue(os.path.exists(zip_output))
            self.assertGreater(os.path.getsize(zip_output), 0)

            # Confirm file contains all expected components inside
            import zipfile
            with zipfile.ZipFile(zip_output, 'r') as zf:
                filenames = zf.namelist()
                self.assertIn("paciente_intake.txt", filenames)
                self.assertIn("informe_decision.pdf", filenames)
                self.assertIn("EXPLICACION_DETALLADA.md", filenames)
                self.assertIn("REPORTE_COMPLETO.csv", filenames)
                self.assertIn("LOG_AUDITORIA.json", filenames)

if __name__ == "__main__":
    unittest.main()
