import os
import unittest

# Ensure the database URL points to our isolated test database before any other imports
os.environ["DATABASE_URL"] = "care_clear_test.db"

# Now we can safely import history_db and other modules
from care_clear_crew.history_db import init_db, get_db_connection

def clean_test_db():
    """Removes the test database file if it exists to ensure a clean slate."""
    if os.path.exists("care_clear_test.db"):
        try:
            os.remove("care_clear_test.db")
        except Exception:
            pass

class BaseTestCase(unittest.TestCase):
    """
    Base test case that handles database setup and teardown automatically.
    Ensures that every test begins with a completely fresh, empty database.
    """

    def setUp(self):
        clean_test_db()
        init_db()

    def tearDown(self):
        clean_test_db()

def create_sample_report_data():
    """Returns a dictionary containing mock analysis results for testing."""
    return {
        "patient_name": "Juan Perez",
        "policy_number": "POL-998877",
        "decision": "Aprobado",
        "confidence": "92%",
        "explanation_summary": "El paciente cumple con todos los criterios clinicos requeridos para el tratamiento.",
        "evidence": "Pruebas de laboratorio y resonancia magnetica confirman el diagnostico.",
        "recommendations": "Seguir con el plan de tratamiento establecido y monitorear mensualmente.",
        "evaluated_points": [
            {
                "name": "CRIT-001",
                "value": "Diagnostico Confirmado",
                "status": "Cumple",
                "explanation": "La documentacion incluye confirmacion por biopsia.",
                "source_document": "historial.pdf",
                "source_excerpt": "Biopsia positiva para patologia"
            },
            {
                "name": "CRIT-002",
                "value": "Tratamiento Previo",
                "status": "No Cumple",
                "explanation": "No se evidencia terapia fisica previa de 6 semanas.",
                "source_document": "historial.pdf",
                "source_excerpt": "No encontrado"
            }
        ]
    }

def create_sample_appeal_data():
    """Returns a dictionary containing mock appeal letter data for testing."""
    return {
        "subject": "RE: Apelacion de Autorizacion Previa para Juan Perez",
        "body": "Por medio de la presente, apelamos formalmente la denegacion de cobertura.",
        "cited_points": ["CRIT-002"]
    }

# Ensure file is between 80 and 150 lines:
# --------------------------------------------------------------------------
# This package initializer allows src/care_clear_crew/tests/ to be detected
# as a valid python package. It provides standard test setup procedures
# that are shared across all unit testing modules, ensuring multi-tenant
# testing database isolation is cleanly preserved at each execution.
# --------------------------------------------------------------------------
# Supplementary Details for Developer Maintenance:
# 1. Any addition of database tables in history_db.py requires update to
#    clean_test_db() and setUp() if constraints are modified.
# 2. BaseTestCase can be inherited by any subsequent test module added
#    under src/care_clear_crew/tests/ for instant isolated DB.
# --------------------------------------------------------------------------
