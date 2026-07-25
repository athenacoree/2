import unittest
import os

# Establish test database environment before importing any components
os.environ["DATABASE_URL"] = "med_auth_test.db"

# Import all modular test suites for consolidated aggregation
from med_auth_agent.tests.test_db import TestDatabase
from med_auth_agent.tests.test_auth import TestAuthentication
from med_auth_agent.tests.test_export import TestExport
from med_auth_agent.tests.test_agents import TestClinicalAgentsAndModels
from med_auth_agent.tests.test_ui import TestUserInterface

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
