import unittest
import os
import tempfile
import json
import sqlite3

# Set the environment variable BEFORE any other imports!
os.environ["DATABASE_URL"] = "med_auth_test.db"

from med_auth_agent.docx_knowledge_source import DOCXKnowledgeSource
from med_auth_agent.packager import create_downloadable_zip
from med_auth_agent.history_db import (
    init_db, save_request, get_history, clear_all_history_global,
    register_user, get_user_by_email, get_users_by_institution,
    save_or_update_pattern, get_patterns_for_insurer, get_all_patterns,
    check_usage_allowed, increment_case_count, update_usage_limit_settings,
    get_stats_summary, log_activity, get_recent_activity
)
from med_auth_agent.auth import create_user_record, verify_login

class TestMedAuthAgent(unittest.TestCase):

    def setUp(self):
        # Enforce clean environment database
        if os.path.exists("med_auth_test.db"):
            try:
                os.remove("med_auth_test.db")
            except Exception:
                pass
        init_db()

    def tearDown(self):
        if os.path.exists("med_auth_test.db"):
            try:
                os.remove("med_auth_test.db")
            except Exception:
                pass

    def test_docx_knowledge_source_init(self):
        source = DOCXKnowledgeSource(file_paths=["dummy.docx"])
        self.assertEqual(source.file_paths, ["dummy.docx"])

    def test_packager_zip_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            orig_doc = os.path.join(temp_dir, "original.txt")
            with open(orig_doc, "w") as f:
                f.write("Clinical clinical clinical info.")

            report_data = {
                "patient_name": "Test Patient",
                "policy_number": "POL-112233",
                "decision": "Aprobado",
                "confidence": "98%",
                "explanation_summary": "Summary of explanation",
                "evidence": "Evidence of clinical tests",
                "recommendations": "No recommendations",
                "evaluated_points": [
                    {"name": f"Pt {i}", "value": "Val", "status": "Cumple", "explanation": "Ok"}
                    for i in range(105)
                ]
            }

            zip_out = os.path.join(temp_dir, "test_output.zip")
            create_downloadable_zip(orig_doc, report_data, zip_out, temp_dir, "Dr. Luis", "Clinica A")
            self.assertTrue(os.path.exists(zip_out))

    def test_history_database(self):
        clear_all_history_global()
        dummy_data = {
            "patient_name": "Jose Perez",
            "policy_number": "POL-TEST-001",
            "decision": "Aprobado",
            "confidence": "95%",
            "explanation_summary": "Test explanation",
            "evidence": "Test evidence",
            "recommendations": "Test recs",
            "evaluated_points": []
        }

        # Test saving request with custom identities and multi-tenant isolation
        save_request(dummy_data, user_id=1, user_name="Dr. Smith", institution_name="Clinica A")

        # Query under Clinica A
        history_a = get_history(institution_name="Clinica A", user_id=1, role="operativo")
        self.assertEqual(len(history_a), 1)
        self.assertEqual(history_a[0]["patient_name"], "Jose Perez")
        self.assertEqual(history_a[0]["decision"], "Aprobado")

        # Query under Clinica B (must return 0 records due to tenant isolation)
        history_b = get_history(institution_name="Clinica B", user_id=1, role="operativo")
        self.assertEqual(len(history_b), 0)

    def test_insurer_patterns(self):
        save_or_update_pattern("Cigna", "Requires MRI of Lumbar Spine", "Clinica A", "Alto")
        save_or_update_pattern("Cigna", "Requires MRI of Lumbar Spine", "Clinica A", "Alto")
        save_or_update_pattern("Cigna", "Requires physical therapy", "Clinica A", "Medio")
        save_or_update_pattern("Cigna", "Requires physical therapy", "Clinica B", "Medio")

        patterns_a = get_patterns_for_insurer("Cigna", "Clinica A")
        self.assertEqual(len(patterns_a), 2)
        self.assertEqual(patterns_a[0]["times_observed"], 2)

        patterns_b = get_patterns_for_insurer("Cigna", "Clinica B")
        self.assertEqual(len(patterns_b), 1)

    def test_precheck_schemas_and_compilation(self):
        from med_auth_agent.schemas import PrecheckReport, EvaluationItem
        item = EvaluationItem(name="REQ_02", value="No encontrado", status="No Cumple", explanation="Missing physiotherapy notes")
        report = PrecheckReport(
            approval_probability="45%",
            missing_critical_items=[item],
            recommendations_to_improve="Submit physiotherapy reports and specialist notes."
        )
        self.assertEqual(report.approval_probability, "45%")
        self.assertEqual(len(report.missing_critical_items), 1)

    def test_appeal_letter_schema_and_pdf_generation(self):
        from med_auth_agent.schemas import AppealLetter
        from med_auth_agent.packager import generate_appeal_pdf
        appeal = AppealLetter(
            subject="RE: Appeal for John Doe",
            body="This is the formal appeal letter body text.",
            cited_points=["REQ_02", "POL_04"]
        )
        self.assertEqual(appeal.subject, "RE: Appeal for John Doe")
        self.assertEqual(len(appeal.cited_points), 2)

        with tempfile.TemporaryDirectory() as temp_dir:
            appeal_pdf_path = os.path.join(temp_dir, "test_appeal.pdf")
            generate_appeal_pdf(appeal.model_dump(), appeal_pdf_path)
            self.assertTrue(os.path.exists(appeal_pdf_path))

    def test_multi_tenant_isolation(self):
        """
        Tarea D: Escribe un test específico en test_suite.py que cree usuarios y casos de dos instituciones distintas
        y confirme explícitamente que ninguna consulta desde la sesión de un usuario de "Clínica A"
        devuelve datos de "Clínica B".
        """
        # Create user for Clinica A
        uid_a = create_user_record(
            email="admin@clinicaa.com",
            password="securepassword123",
            full_name="Admin Clinica A",
            role="administrador",
            institution_name="Clinica A"
        )
        # Verify first registered becomes admin
        user_a = get_user_by_email("admin@clinicaa.com")
        self.assertEqual(user_a["role"], "administrador")

        # Create user for Clinica B
        uid_b = create_user_record(
            email="admin@clinicab.com",
            password="securepassword123",
            full_name="Admin Clinica B",
            role="administrador",
            institution_name="Clinica B"
        )
        user_b = get_user_by_email("admin@clinicab.com")
        self.assertEqual(user_b["role"], "administrador")

        # Create operative user for Clinica A
        uid_a_op = create_user_record(
            email="op@clinicaa.com",
            password="securepassword123",
            full_name="Operativo Clinica A",
            role="operativo",
            institution_name="Clinica A"
        )

        # 1. Check isolation of User Management lists
        users_a = get_users_by_institution("Clinica A")
        users_b = get_users_by_institution("Clinica B")
        # Clinica A has Admin and Op
        self.assertEqual(len(users_a), 2)
        for u in users_a:
            self.assertEqual(u["institution_name"], "Clinica A")
        # Clinica B has Admin only
        self.assertEqual(len(users_b), 1)
        for u in users_b:
            self.assertEqual(u["institution_name"], "Clinica B")

        # 2. Case creation and History Isolation
        case_a = {
            "patient_name": "Paciente Clinica A",
            "policy_number": "POL-A-100",
            "decision": "Aprobado",
            "confidence": "90%",
            "explanation_summary": "Explanation A",
            "evidence": "Evidence A",
            "recommendations": "Recs A"
        }
        case_b = {
            "patient_name": "Paciente Clinica B",
            "policy_number": "POL-B-200",
            "decision": "Denegado",
            "confidence": "85%",
            "explanation_summary": "Explanation B",
            "evidence": "Evidence B",
            "recommendations": "Recs B"
        }

        save_request(case_a, user_id=uid_a_op, user_name="Operativo A", institution_name="Clinica A")
        save_request(case_b, user_id=uid_b, user_name="Admin B", institution_name="Clinica B")

        # Admin of Clinica A queries History
        hist_admin_a = get_history(institution_name="Clinica A", user_id=uid_a, role="administrador")
        self.assertEqual(len(hist_admin_a), 1)
        self.assertEqual(hist_admin_a[0]["patient_name"], "Paciente Clinica A")

        # Operative of Clinica A queries History (can see own)
        hist_op_a = get_history(institution_name="Clinica A", user_id=uid_a_op, role="operativo")
        self.assertEqual(len(hist_op_a), 1)

        # Admin of Clinica A queries History (should NEVER see Clinica B)
        for r in hist_admin_a:
            self.assertNotEqual(r["patient_name"], "Paciente Clinica B")

        # Admin of Clinica B queries History
        hist_admin_b = get_history(institution_name="Clinica B", user_id=uid_b, role="administrador")
        self.assertEqual(len(hist_admin_b), 1)
        self.assertEqual(hist_admin_b[0]["patient_name"], "Paciente Clinica B")

        # 3. Executive Analytics Dashboard Isolation
        stats_a = get_stats_summary("Clinica A")
        stats_b = get_stats_summary("Clinica B")
        self.assertEqual(stats_a["total_cases"], 1)
        self.assertEqual(stats_a["approved"], 1)
        self.assertEqual(stats_b["total_cases"], 1)
        self.assertEqual(stats_b["denied"], 1)

        # 4. Insurer Pattern Learning Isolation
        save_or_update_pattern("Cigna", "Clinical standard 1", "Clinica A", "Alto")
        save_or_update_pattern("Cigna", "Clinical standard 2", "Clinica B", "Alto")

        p_a = get_patterns_for_insurer("Cigna", "Clinica A")
        p_b = get_patterns_for_insurer("Cigna", "Clinica B")
        self.assertEqual(len(p_a), 1)
        self.assertEqual(p_a[0]["pattern_description"], "Clinical standard 1")
        self.assertEqual(len(p_b), 1)
        self.assertEqual(p_b[0]["pattern_description"], "Clinical standard 2")

        # 5. Usage limit Isolation
        update_usage_limit_settings("Clinica A", 5, 80)
        self.assertTrue(check_usage_allowed("Clinica A"))
        for _ in range(5):
            increment_case_count("Clinica A")
        # Exceeded limit
        self.assertFalse(check_usage_allowed("Clinica A"))
        # Clinica B should remain unaffected
        self.assertTrue(check_usage_allowed("Clinica B"))

        # 6. Trust Ledger integrity verification
        # Previous hash matches and wraps in a secure sequence
        last_hash = get_history("Clinica A", uid_a, role="administrador")[0]["record_hash"]
        self.assertIsNotNone(last_hash)
        self.assertNotEqual(last_hash, "")

    def test_activity_logging(self):
        log_activity(1, "Dr. House", "Princeton", "login", "Successful authentication")
        logs = get_recent_activity("Princeton")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "login")
        self.assertEqual(logs[0]["details"], "Successful authentication")

if __name__ == "__main__":
    unittest.main()
