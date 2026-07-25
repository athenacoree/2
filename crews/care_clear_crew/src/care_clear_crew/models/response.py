from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from care_clear_crew.models.decision import ConfidenceScore

class AuthResponse(BaseModel):
    """Respuesta de pre-chequeo que calcula probabilidad de aprobación y faltantes."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    probability_score: str = Field(..., validation_alias="approval_probability", serialization_alias="approval_probability")
    critical_absent_items: List[ConfidenceScore] = Field(..., validation_alias="missing_critical_items", serialization_alias="missing_critical_items")
    improvement_guidelines: str = Field(..., validation_alias="recommendations_to_improve", serialization_alias="recommendations_to_improve")

    @field_validator("probability_score")
    @classmethod
    def validate_probability(cls, val: str) -> str:
        clean = val.strip()
        if "%" not in clean:
            clean = f"{clean}%"
        return clean

    @property
    def approval_probability(self) -> str:
        return self.probability_score

    @property
    def missing_critical_items(self) -> List[ConfidenceScore]:
        return self.critical_absent_items

    @property
    def recommendations_to_improve(self) -> str:
        return self.improvement_guidelines

    def has_high_probability(self) -> bool:
        """Determina si la probabilidad de aprobación estimada es alta (>70%)."""
        try:
            numeric_val = int(self.probability_score.replace("%", "").strip())
            return numeric_val >= 70
        except Exception:
            return False

    def get_missing_criteria_names(self) -> List[str]:
        """Obtiene la lista de identificadores de criterios que hacen falta."""
        return [item.criteria_id for item in self.critical_absent_items]

    def __getattr__(self, name: str):
        for f_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, f_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")


class Decision(BaseModel):
    """Carta de apelación formal estructurada para casos denegados."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    appeal_subject: str = Field(..., validation_alias="subject", serialization_alias="subject")
    appeal_body: str = Field(..., validation_alias="body", serialization_alias="body")
    challenged_points: List[str] = Field(..., validation_alias="cited_points", serialization_alias="cited_points")

    @field_validator("appeal_subject")
    @classmethod
    def validate_subject(cls, val: str) -> str:
        clean = val.strip()
        if len(clean) < 5:
            raise ValueError("El asunto de la apelación debe ser más descriptivo.")
        return clean

    @property
    def subject(self) -> str:
        return self.appeal_subject

    @property
    def body(self) -> str:
        return self.appeal_body

    @property
    def cited_points(self) -> List[str]:
        return self.challenged_points

    def count_challenged_criteria(self) -> int:
        """Retorna el número de criterios en apelación."""
        return len(self.challenged_points)

    def get_appeal_preview(self) -> str:
        """Retorna una vista previa corta de la carta de apelación."""
        return f"Asunto: {self.appeal_subject}\nCriterios apelados: {', '.join(self.challenged_points)}"

    def __getattr__(self, name: str):
        for f_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, f_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
