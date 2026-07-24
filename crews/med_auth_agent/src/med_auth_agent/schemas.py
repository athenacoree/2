from pydantic import BaseModel, Field
from typing import List

class EvaluationItem(BaseModel):
    name: str = Field(description="Name of the evaluated medical criteria point (e.g. ID_01, POL_05, etc.)")
    value: str = Field(description="The parsed value or evidence from document or 'No encontrado'")
    status: str = Field(description="Compliance status: 'Cumple' or 'No Cumple'")
    explanation: str = Field(description="Detailed reasons of why it meets or fails the policy or clinical requirements")
    source_excerpt: str = Field(default="No encontrado", description="Fragmento textual exacto (máx. ~300 caracteres) del documento de origen que sustenta el value y status.")
    source_document: str = Field(default="No encontrado", description="Nombre del archivo de donde se extrajo esa evidencia (o 'No encontrado' si no hay evidencia real).")

class DecisionReport(BaseModel):
    patient_name: str = Field(description="Full name of the patient")
    policy_number: str = Field(description="Insurance policy identifier")
    decision: str = Field(description="Decision: 'Aprobado' or 'Denegado'")
    confidence: str = Field(description="Confidence score percentage (0-100%)")
    explanation_summary: str = Field(description="Consolidated explanation of why the decision was taken")
    evidence: str = Field(description="Primary clinical evidence backing the final decision")
    recommendations: str = Field(description="Actionable guidance recommendations for the clinician/user")
    evaluated_points: List[EvaluationItem] = Field(description="List of at least 105 distinct medical criteria points matching the 7 categories")
    observed_patterns: List[str] = Field(default=[], description="Unwritten patterns, extra demands, or requirements observed for this specific insurer that differ or are in addition to the standard policy rules")

class AppealLetter(BaseModel):
    subject: str = Field(description="The formal subject line of the appeal letter (e.g., RE: Prior Authorization Appeal for [Patient Name])")
    body: str = Field(description="The full, formal, and persuasive text of the appeal letter including date, headers, body, and signature block")
    cited_points: List[str] = Field(description="List of specific policy or medical criteria points that failed and are being appealed in this letter")

class PrecheckReport(BaseModel):
    approval_probability: str = Field(description="Approval probability percentage (0-100%) as a string, e.g., '45%'")
    missing_critical_items: List[EvaluationItem] = Field(description="List of critical items with status 'No encontrado' or missing, sorted by impact on approval probability (highest impact first)")
    recommendations_to_improve: str = Field(description="Concrete actionable guidance on what documents or clinical records should be uploaded to increase approval probability")
