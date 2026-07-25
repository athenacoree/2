from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime

class HIPAACompliance(BaseModel):
    """Métricas y verificaciones de cumplimiento de la ley HIPAA."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    has_pii_redacted: bool = Field(default=True, validation_alias="pii_redacted", serialization_alias="pii_redacted")
    consent_verified: bool = Field(default=True, validation_alias="consent_verified", serialization_alias="consent_verified")
    encryption_used: str = Field(default="AES-256", validation_alias="encryption", serialization_alias="encryption")
    audit_comments: str = Field(default="Satisfecho", validation_alias="comments", serialization_alias="comments")

    @field_validator("encryption_used")
    @classmethod
    def validate_encryption(cls, val: str) -> str:
        clean = val.strip().upper()
        if clean not in {"AES-256", "TLS-1.3", "AES-128"}:
            raise ValueError("Cifrado no aprobado por HIPAA.")
        return clean

    @property
    def pii_redacted(self) -> bool:
        return self.has_pii_redacted

    @property
    def comments(self) -> str:
        return self.audit_comments

    def check_compliant_status(self) -> bool:
        """Verifica si todos los requerimientos básicos de HIPAA se cumplen."""
        return self.has_pii_redacted and self.consent_verified and self.encryption_used in {"AES-256", "TLS-1.3"}

    def __getattr__(self, name: str):
        for f_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, f_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")


class AuditLog(BaseModel):
    """Registro de auditoría inmutable para operaciones en el sistema."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    log_id: str = Field(..., validation_alias="id", serialization_alias="id")
    access_timestamp: str = Field(..., validation_alias="timestamp", serialization_alias="timestamp")
    operator_user_id: int = Field(..., validation_alias="user_id", serialization_alias="user_id")
    operator_full_name: str = Field(..., validation_alias="user_name", serialization_alias="user_name")
    action_performed: str = Field(..., validation_alias="action", serialization_alias="action")
    system_component: str = Field(..., validation_alias="component", serialization_alias="component")
    compliance_metric: HIPAACompliance = Field(..., validation_alias="compliance", serialization_alias="compliance")

    @field_validator("action_performed")
    @classmethod
    def validate_action(cls, val: str) -> str:
        allowed_actions = {"case_created", "login", "export_zip", "update_settings", "view_history", "precheck_run"}
        if val.strip() not in allowed_actions:
            raise ValueError(f"Acción de auditoría '{val}' no reconocida.")
        return val.strip()

    @property
    def id(self) -> str:
        return self.log_id

    @property
    def timestamp(self) -> str:
        return self.access_timestamp

    @property
    def user_id(self) -> int:
        return self.operator_user_id

    @property
    def user_name(self) -> str:
        return self.operator_full_name

    @property
    def action(self) -> str:
        return self.action_performed

    @property
    def component(self) -> str:
        return self.system_component

    @property
    def compliance(self) -> HIPAACompliance:
        return self.compliance_metric

    def print_formatted_log(self) -> str:
        """Genera un registro formateado y legible de la actividad de auditoría."""
        return f"[{self.access_timestamp}] Usuario: {self.operator_full_name} realizó {self.action_performed} en {self.system_component}"

    def __getattr__(self, name: str):
        for f_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, f_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
