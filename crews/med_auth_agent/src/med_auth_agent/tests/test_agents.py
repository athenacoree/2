import unittest
from med_auth_agent.tests import BaseTestCase
from med_auth_agent.docx_knowledge_source import DOCXKnowledgeSource
from med_auth_agent.schemas import EvaluationItem, DecisionReport, AppealLetter, PrecheckReport

class TestClinicalAgentsAndModels(BaseTestCase):
    """
    Unit tests for AI Crew components and modular Pydantic schemas.
    Validates custom DOCXKnowledgeSource initialization, proper schema validation,
    and backwards-compatibility field aliases/attributes.
    """

    def test_docx_knowledge_source_initialization(self):
        source = DOCXKnowledgeSource(file_paths=["dummy_policy.docx"])
        self.assertEqual(source.file_paths, ["dummy_policy.docx"])

    def test_evaluation_item_schema_and_aliases(self):
        # Validation using model aliases / legacy naming format
        item = EvaluationItem(
            name="CRIT_03",
            value="Examen de laboratorio positivo",
            status="Cumple",
            explanation="La muestra sanguinea presenta anticuerpos positivos.",
            source_document="poliza.pdf",
            source_excerpt="El paciente debe presentar positividad"
        )

        # Attribute and property overrides check
        self.assertEqual(item.criteria_id, "CRIT_03")
        self.assertEqual(item.extracted_value, "Examen de laboratorio positivo")
        self.assertEqual(item.compliance_status, "Cumple")
        self.assertEqual(item.reasoning_details, "La muestra sanguinea presenta anticuerpos positivos.")

        # Custom __getattr__ alias mappings validation
        self.assertEqual(item.name, "CRIT_03")
        self.assertEqual(item.value, "Examen de laboratorio positivo")
        self.assertEqual(item.status, "Cumple")
        self.assertEqual(item.explanation, "La muestra sanguinea presenta anticuerpos positivos.")

        # Invalid compliance value raised properly
        with self.assertRaises(ValueError):
            EvaluationItem(
                name="CRIT_03",
                value="Val",
                status="INCORRECT_STATUS",
                explanation="Explanation"
            )

    def test_decision_report_schema_and_aliases(self):
        item = EvaluationItem(
            name="REQ_10",
            value="No encontrado",
            status="No Cumple",
            explanation="Missing info",
            source_document="N/A",
            source_excerpt="N/A"
        )

        report = DecisionReport(
            patient_name="Ana Garcia",
            policy_number="POL-1122",
            decision="Denegado",
            confidence="85%",
            explanation_summary="No cumple con pre-requisitos.",
            evidence="No se adjunta evidencia.",
            recommendations="Someter nueva solicitud.",
            evaluated_points=[item],
            observed_patterns=["Pattern A"]
        )

        # Basic properties
        self.assertEqual(report.full_patient_name, "Ana Garcia")
        self.assertEqual(report.policy_id, "POL-1122")
        self.assertEqual(report.auth_decision, "Denegado")
        self.assertEqual(report.confidence_percentage, "85%")

        # Dynamic __getattr__ backward compatibility alias lookup
        self.assertEqual(report.patient_name, "Ana Garcia")
        self.assertEqual(report.policy_number, "POL-1122")
        self.assertEqual(report.decision, "Denegado")
        self.assertEqual(report.confidence, "85%")

        # Model validation checks (invalid decision raises error)
        with self.assertRaises(ValueError):
            DecisionReport(
                patient_name="Ana Garcia",
                policy_number="POL-1122",
                decision="INVALID_DECISION",
                confidence="85%",
                explanation_summary="No cumple",
                evidence="No evidence",
                recommendations="Recs",
                evaluated_points=[item]
            )

    def test_appeal_letter_schema(self):
        appeal = AppealLetter(
            subject="Apelacion Formal",
            body="Texto de la apelacion.",
            cited_points=["REQ_10"]
        )
        self.assertEqual(appeal.subject, "Apelacion Formal")
        self.assertEqual(appeal.body, "Texto de la apelacion.")
        self.assertEqual(appeal.cited_points, ["REQ_10"])

    def test_precheck_report_schema(self):
        item = EvaluationItem(
            name="REQ_20",
            value="Falta historial clinico",
            status="No encontrado",
            explanation="Se requiere historial de 6 semanas.",
            source_document="N/A",
            source_excerpt="N/A"
        )
        precheck = PrecheckReport(
            approval_probability="40%",
            missing_critical_items=[item],
            recommendations_to_improve="Adjuntar historial de fisioterapia."
        )
        self.assertEqual(precheck.approval_probability, "40%")
        self.assertEqual(len(precheck.missing_critical_items), 1)
        self.assertEqual(precheck.recommendations_to_improve, "Adjuntar historial de fisioterapia.")

if __name__ == "__main__":
    unittest.main()
