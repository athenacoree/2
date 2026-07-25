from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional

class ConfidenceScore(BaseModel):
    """Punto individual de evaluación de criterios clínicos y políticas."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    criteria_id: str = Field(..., validation_alias="name", serialization_alias="name")
    extracted_value: str = Field(..., validation_alias="value", serialization_alias="value")
    compliance_status: str = Field(..., validation_alias="status", serialization_alias="status")
    reasoning_details: str = Field(..., validation_alias="explanation", serialization_alias="explanation")
    evidence_excerpt: str = Field(default="No encontrado", validation_alias="source_excerpt", serialization_alias="source_excerpt")
    origin_document: str = Field(default="No encontrado", validation_alias="source_document", serialization_alias="source_document")

    @field_validator("compliance_status")
    @classmethod
    def validate_compliance(cls, val: str) -> str:
        clean = val.strip()
        if clean not in {"Cumple", "No Cumple", "No encontrado"}:
            raise ValueError("El estado de cumplimiento debe ser 'Cumple', 'No Cumple' o 'No encontrado'.")
        return clean

    def to_short_summary(self) -> str:
        """Retorna un resumen de la evaluación del criterio."""
        return f"{self.criteria_id}: {self.compliance_status} - {self.extracted_value}"

    def __getattr__(self, name: str):
        for f_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, f_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")


class DecisionResult(BaseModel):
    """Reporte de decisión consolidado que contiene la evaluación detallada."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    full_patient_name: str = Field(..., validation_alias="patient_name", serialization_alias="patient_name")
    policy_id: str = Field(..., validation_alias="policy_number", serialization_alias="policy_number")
    auth_decision: str = Field(..., validation_alias="decision", serialization_alias="decision")
    confidence_percentage: str = Field(..., validation_alias="confidence", serialization_alias="confidence")
    summary_justification: str = Field(..., validation_alias="explanation_summary", serialization_alias="explanation_summary")
    clinical_evidence: str = Field(..., validation_alias="evidence", serialization_alias="evidence")
    actionable_recommendations: str = Field(..., validation_alias="recommendations", serialization_alias="recommendations")
    evaluated_criteria: List[ConfidenceScore] = Field(..., validation_alias="evaluated_points", serialization_alias="evaluated_points")
    detected_insurer_patterns: List[str] = Field(default=[], validation_alias="observed_patterns", serialization_alias="observed_patterns")

    @field_validator("auth_decision")
    @classmethod
    def validate_decision(cls, val: str) -> str:
        clean = val.strip()
        if clean not in {"Aprobado", "Denegado"}:
            raise ValueError("La decisión debe ser 'Aprobado' o 'Denegado'.")
        return clean

    @field_validator("confidence_percentage")
    @classmethod
    def validate_confidence(cls, val: str) -> str:
        clean = val.strip()
        if "%" not in clean:
            clean = f"{clean}%"
        return clean

    def count_compliance_stats(self) -> dict:
        """Calcula estadísticas rápidas sobre los criterios evaluados."""
        total = len(self.evaluated_criteria)
        meets = sum(1 for item in self.evaluated_criteria if item.compliance_status == "Cumple")
        fails = sum(1 for item in self.evaluated_criteria if item.compliance_status == "No Cumple")
        return {"total": total, "meets": meets, "fails": fails}

    def get_failed_criteria(self) -> List[ConfidenceScore]:
        """Obtiene una lista de los puntos evaluados que no cumplieron."""
        return [c for c in self.evaluated_criteria if c.compliance_status == "No Cumple"]

    def get_meets_criteria(self) -> List[ConfidenceScore]:
        """Obtiene una lista de los puntos evaluados que sí cumplieron."""
        return [c for c in self.evaluated_criteria if c.compliance_status == "Cumple"]

    def __getattr__(self, name: str):
        for f_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, f_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
