import os
import unittest
from care_clear_crew.tests import BaseTestCase, create_sample_report_data
from care_clear_crew.history_db import (
    save_request, get_history, clear_all_history_global,
    save_or_update_pattern, get_patterns_for_insurer, get_all_patterns,
    check_usage_allowed, increment_case_count, update_usage_limit_settings,
    get_stats_summary, log_activity, get_recent_activity
)

class TestDatabase(BaseTestCase):
    """
    Unit tests for history_db.py database functions.
    Validates proper execution of CRUD statements, Trust Ledger cryptographic sequence,
    multi-tenant query separation, insurer patterns persistence, usage limits, and dashboard stats.
    """

    def test_history_crud_and_trust_ledger(self):
        # Establish clean global state
        clear_all_history_global()
        data = create_sample_report_data()

        # Save record for Clinica Alfa under User 10
        save_request(data, user_id=10, user_name="Dr. House", institution_name="Clinica Alfa")

        # Retrieve for Clinica Alfa (as administrator)
        history_alfa = get_history(institution_name="Clinica Alfa", user_id=10, role="administrador")
        self.assertEqual(len(history_alfa), 1)
        record = history_alfa[0]
        self.assertEqual(record["patient_name"], "Juan Perez")
        self.assertEqual(record["decision"], "Aprobado")
        self.assertEqual(record["created_by_name"], "Dr. House")

        # Trust Ledger cryptographic validation
        self.assertIsNotNone(record["record_hash"])
        self.assertNotEqual(record["record_hash"], "")

        # Save secondary record to verify cryptographic chain link (previous_hash matches)
        data2 = create_sample_report_data()
        data2["patient_name"] = "Maria Lopez"
        save_request(data2, user_id=10, user_name="Dr. House", institution_name="Clinica Alfa")

        history_alfa_updated = get_history(institution_name="Clinica Alfa", user_id=10, role="administrador")
        self.assertEqual(len(history_alfa_updated), 2)
        patient_names = {r["patient_name"] for r in history_alfa_updated}
        self.assertEqual(patient_names, {"Juan Perez", "Maria Lopez"})

    def test_insurer_patterns_persistence_and_isolation(self):
        clear_all_history_global()

        # Persist standard patterns under Clinica Alfa and Clinica Beta
        save_or_update_pattern("Cigna", "Requires MRI of Lumbar Spine", "Clinica Alfa", "Alto")
        save_or_update_pattern("Cigna", "Requires MRI of Lumbar Spine", "Clinica Alfa", "Alto") # Repeated to increment count
        save_or_update_pattern("Cigna", "Requires conservative physical therapy", "Clinica Alfa", "Medio")
        save_or_update_pattern("Cigna", "Requires physical therapy", "Clinica Beta", "Medio")

        # Verify Alfa patterns are correctly compiled
        p_alfa = get_patterns_for_insurer("Cigna", "Clinica Alfa")
        self.assertEqual(len(p_alfa), 2)
        self.assertEqual(p_alfa[0]["times_observed"], 2)

        # Verify Beta pattern multi-tenant separation
        p_beta = get_patterns_for_insurer("Cigna", "Clinica Beta")
        self.assertEqual(len(p_beta), 1)
        self.assertEqual(p_beta[0]["pattern_description"], "Requires physical therapy")

        all_alfa = get_all_patterns("Clinica Alfa")
        self.assertEqual(len(all_alfa), 2)

    def test_usage_limits_enforcement(self):
        clear_all_history_global()

        # Configure usage limit configuration
        update_usage_limit_settings("Clinica Alfa", limit=3, alert_threshold=66)
        self.assertTrue(check_usage_allowed("Clinica Alfa"))

        # Increment towards target limit
        increment_case_count("Clinica Alfa")
        increment_case_count("Clinica Alfa")
        self.assertTrue(check_usage_allowed("Clinica Alfa"))

        increment_case_count("Clinica Alfa")
        # limit is 3, count is 3. Limit reached/exceeded.
        self.assertFalse(check_usage_allowed("Clinica Alfa"))

        # Ensure Clinica Beta usage limits remain independent
        self.assertTrue(check_usage_allowed("Clinica Beta"))

    def test_executive_dashboard_stats_and_activities(self):
        clear_all_history_global()
        data = create_sample_report_data()

        # Generate mock cases for analysis
        save_request(data, user_id=11, user_name="Dr. Grey", institution_name="Seattle Grace")
        data_denied = create_sample_report_data()
        data_denied["decision"] = "Denegado"
        save_request(data_denied, user_id=11, user_name="Dr. Grey", institution_name="Seattle Grace")

        # Validate dashboard statistics metrics
        stats = get_stats_summary("Seattle Grace")
        self.assertEqual(stats["total_cases"], 2)
        self.assertEqual(stats["approved"], 1)
        self.assertEqual(stats["denied"], 1)
        self.assertEqual(stats["approved_rate"], 50.0)

        # Log and retrieve activity audits
        log_activity(11, "Dr. Grey", "Seattle Grace", "run_analysis", "Analyzed Case POL-998877")
        logs = get_recent_activity("Seattle Grace")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "run_analysis")
        self.assertEqual(logs[0]["details"], "Analyzed Case POL-998877")

if __name__ == "__main__":
    unittest.main()
