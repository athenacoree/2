import unittest
import os
import tempfile
import json
from med_auth_agent.docx_knowledge_source import DOCXKnowledgeSource
from med_auth_agent.packager import create_downloadable_zip

class TestMedAuthAgent(unittest.TestCase):

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

if __name__ == "__main__":
    unittest.main()
