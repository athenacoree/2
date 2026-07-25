import unittest
import os

# Establish test database environment before importing any components
os.environ["DATABASE_URL"] = "care_clear_test.db"

# Import all modular test suites for consolidated aggregation
from care_clear_crew.tests.test_db import TestDatabase
from care_clear_crew.tests.test_auth import TestAuthentication
from care_clear_crew.tests.test_export import TestExport
from care_clear_crew.tests.test_agents import TestClinicalAgentsAndModels
from care_clear_crew.tests.test_ui import TestUserInterface

def suite():
    """Aggregates all modular test cases into a unified TestSuite."""
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    test_suite.addTests(loader.loadTestsFromTestCase(TestAuthentication))
    test_suite.addTests(loader.loadTestsFromTestCase(TestExport))
    test_suite.addTests(loader.loadTestsFromTestCase(TestClinicalAgentsAndModels))
    test_suite.addTests(loader.loadTestsFromTestCase(TestUserInterface))

    return test_suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
