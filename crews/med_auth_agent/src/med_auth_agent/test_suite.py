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

if __name__ == "__main__":
    unittest.main()
