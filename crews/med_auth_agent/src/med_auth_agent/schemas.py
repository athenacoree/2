from pydantic import BaseModel, Field
from typing import List

class EvaluationItem(BaseModel):
    name: str = Field(description="Name of the evaluated medical criteria point (e.g. ID_01, POL_05, etc.)")
    value: str = Field(description="The parsed value or evidence from document or 'No encontrado'")
    status: str = Field(description="Compliance status: 'Cumple' or 'No Cumple'")
    explanation: str = Field(description="Detailed reasons of why it meets or fails the policy or clinical requirements")

class DecisionReport(BaseModel):
    patient_name: str = Field(description="Full name of the patient")
    policy_number: str = Field(description="Insurance policy identifier")
    decision: str = Field(description="Decision: 'Aprobado' or 'Denegado'")
    confidence: str = Field(description="Confidence score percentage (0-100%)")
    explanation_summary: str = Field(description="Consolidated explanation of why the decision was taken")
    evidence: str = Field(description="Primary clinical evidence backing the final decision")
    recommendations: str = Field(description="Actionable guidance recommendations for the clinician/user")
    evaluated_points: List[EvaluationItem] = Field(description="List of at least 105 distinct medical criteria points matching the 7 categories")
