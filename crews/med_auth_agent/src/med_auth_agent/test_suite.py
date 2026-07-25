import unittest
import os
import tempfile
import json
import sqlite3
from med_auth_agent.docx_knowledge_source import DOCXKnowledgeSource
from med_auth_agent.packager import create_downloadable_zip
from med_auth_agent.history_db import init_db, save_request, get_history, clear_all_history

class TestMedAuthAgent(unittest.TestCase):

    def setUp(self):
        init_db()

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
            create_downloadable_zip(orig_doc, report_data, zip_out, temp_dir)
            self.assertTrue(os.path.exists(zip_out))

    def test_history_database(self):
        clear_all_history()
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
        save_request(dummy_data)
        history = get_history()
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["patient_name"], "Jose Perez")
        self.assertEqual(history[0]["decision"], "Aprobado")

        filtered = get_history(search_query="Jose")
        self.assertGreaterEqual(len(filtered), 1)

        clear_all_history()
        self.assertEqual(len(get_history()), 0)

    def test_insurer_patterns(self):
        from med_auth_agent.history_db import save_or_update_pattern, get_patterns_for_insurer, get_all_patterns
        save_or_update_pattern("Cigna", "Requires MRI of Lumbar Spine less than 6 months old", "Alto")
        save_or_update_pattern("Cigna", "Requires MRI of Lumbar Spine less than 6 months old", "Alto")
        save_or_update_pattern("Cigna", "Requires 6 weeks physical therapy conservative treatment", "Medio")

        patterns = get_patterns_for_insurer("Cigna")
        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0]["times_observed"], 2)
        self.assertIn("MRI", patterns[0]["pattern_description"])

        all_patterns = get_all_patterns()
        self.assertGreaterEqual(len(all_patterns), 2)

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

    def test_fallback_on_parse_error_prevention(self):
        from unittest.mock import MagicMock
        import logging
        from med_auth_agent.analysis_runner import run_analysis_with_retry
        from med_auth_agent.crew import MedAuthAgent

        log_file = "med_auth_errors.log"
        if os.path.exists(log_file):
            os.remove(log_file)

        # Mock the crew and kickoff calls to return invalid JSON
        mock_crew = MagicMock()
        mock_kickoff_result = MagicMock()
        mock_kickoff_result.raw = "This is definitely not valid JSON at all."
        mock_crew.kickoff.return_value = mock_kickoff_result

        old_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "mock-openai-key"

        try:
            agent_system = MedAuthAgent()
        finally:
            if old_key is None:
                del os.environ["OPENAI_API_KEY"]
            else:
                os.environ["OPENAI_API_KEY"] = old_key
        agent_system.crew = MagicMock(return_value=mock_crew)

        # Capture logging of exception
        with self.assertLogs(level="ERROR") as log_context:
            result = run_analysis_with_retry(agent_system, max_attempts=3)

        # 1. Verify it re-tried the expected number of times (3)
        self.assertEqual(agent_system.crew.call_count, 3)

        # 2. Verify result is None (no fake data or partial save)
        self.assertIsNone(result)

        # 3. Verify logging.exception captured the parsing error
        log_messages = "".join(log_context.output)
        self.assertIn("Error en intento de parseo de JSON en pipeline asíncrono", log_messages)

        # 4. Verify the failure is logged to med_auth_errors.log
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn("This is definitely not valid JSON at all.", log_content)
            self.assertIn("Expecting value", log_content)

if __name__ == "__main__":
    unittest.main()
