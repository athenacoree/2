from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime

class RequestStatus(BaseModel):
    """Representa el estado actual de una solicitud de autorización médica."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    status_code: str = Field(..., validation_alias="code", serialization_alias="code")
    status_label: str = Field(..., validation_alias="label", serialization_alias="label")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), validation_alias="updated_at", serialization_alias="updated_at")
    is_finalized: bool = Field(default=False, validation_alias="finalized", serialization_alias="finalized")

    @field_validator("status_code")
    @classmethod
    def validate_code(cls, val: str) -> str:
        allowed = {"pendiente", "aprobado", "denegado", "prechequeo"}
        val_clean = val.strip().lower()
        if val_clean not in allowed:
            raise ValueError(f"El estado debe ser uno de: {allowed}")
        return val_clean

    def mark_completed_status(self, finalized: bool, description: str):
        self.is_finalized = finalized
        self.status_label = description
        self.last_updated = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        """Exporta el estado en formato de diccionario estándar."""
        return self.model_dump()

    def __getattr__(self, name: str):
        for f_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, f_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")


class AuthRequest(BaseModel):
    """Estructura de datos para solicitudes de autorización de pacientes."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    request_id: str = Field(..., validation_alias="id", serialization_alias="id")
    patient_identifier: str = Field(..., validation_alias="patient_id", serialization_alias="patient_id")
    policy_id: str = Field(..., validation_alias="policy_number", serialization_alias="policy_number")
    requesting_physician: str = Field(..., validation_alias="physician_name", serialization_alias="physician_name")
    clinical_notes: str = Field(..., validation_alias="notes", serialization_alias="notes")
    attachment_paths: List[str] = Field(default=[], validation_alias="files", serialization_alias="files")
    current_status: RequestStatus = Field(..., validation_alias="status", serialization_alias="status")
    creation_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), validation_alias="created_at", serialization_alias="created_at")

    @field_validator("policy_id")
    @classmethod
    def validate_policy(cls, val: str) -> str:
        if not val or len(val.strip()) < 3:
            raise ValueError("El número de póliza debe tener al menos 3 caracteres.")
        return val.strip()

    @field_validator("patient_identifier")
    @classmethod
    def validate_patient(cls, val: str) -> str:
        if not val or len(val.strip()) < 2:
            raise ValueError("El identificador del paciente debe ser válido.")
        return val.strip()

    def add_attachment(self, file_path: str):
        if file_path and file_path not in self.attachment_paths:
            self.attachment_paths.append(file_path)

    def mark_as_completed(self, success: bool = True):
        self.current_status.is_finalized = True
        self.current_status.status_code = "aprobado" if success else "denegado"
        self.current_status.status_label = "Procesamiento finalizado"
        self.current_status.last_updated = datetime.utcnow().isoformat()

    def to_summary(self) -> str:
        """Retorna un resumen legible de la solicitud."""
        return f"Solicitud {self.request_id} - Paciente: {self.patient_identifier} - Estado: {self.current_status.status_code.upper()}"

    def __getattr__(self, name: str):
        for f_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, f_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
