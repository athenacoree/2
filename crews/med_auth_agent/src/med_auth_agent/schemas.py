import os
from pydantic import BaseModel, Field
from typing import List

class EvaluationItem(BaseModel):
    name: str = Field(description="Name or description of the evaluated criteria point")
    value: str = Field(description="Evaluated value or evidence found in the document")
    status: str = Field(description="Status of compliance: 'Cumple' or 'No Cumple'")
    explanation: str = Field(description="Detailed explanation of why it meets or fails the criteria")

class DecisionReport(BaseModel):
    patient_name: str = Field(description="Name of the patient")
    policy_number: str = Field(description="Insurance policy number")
    decision: str = Field(description="Decision: 'Aprobado' or 'Denegado'")
    confidence: str = Field(description="Confidence percentage (0-100%)")
    explanation_summary: str = Field(description="Clear and detailed explanation of why the decision was taken")
    evidence: str = Field(description="Key evidence found in the files supporting this decision")
    recommendations: str = Field(description="User action-oriented recommendations")
    evaluated_points: List[EvaluationItem] = Field(description="Full list of evaluated criteria points (at least 100+ points)")
