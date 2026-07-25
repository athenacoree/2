from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional

class UserCreate(BaseModel):
    """Modelo para la creación de un nuevo usuario en la plataforma."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    user_email: str = Field(..., validation_alias="email", serialization_alias="email")
    plain_password: str = Field(..., validation_alias="password", serialization_alias="password")
    full_name_text: str = Field(..., validation_alias="full_name", serialization_alias="full_name")
    assigned_role: str = Field(..., validation_alias="role", serialization_alias="role")
    organization_name: str = Field(..., validation_alias="institution_name", serialization_alias="institution_name")

    @field_validator("user_email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        clean_email = value.strip().lower()
        if "@" not in clean_email:
            raise ValueError("El formato del correo electrónico es inválido.")
        return clean_email

    @field_validator("plain_password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        return value

    @field_validator("assigned_role")
    @classmethod
    def validate_role_type(cls, value: str) -> str:
        allowed = {"operativo", "administrador"}
        clean_role = value.strip().lower()
        if clean_role not in allowed:
            raise ValueError("El rol debe ser 'operativo' o 'administrador'.")
        return clean_role

    def __getattr__(self, name: str):
        for field_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, field_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")


class User(BaseModel):
    """Representa la entidad pública de un usuario registrado."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    user_id: int = Field(..., validation_alias="id", serialization_alias="id")
    user_email: str = Field(..., validation_alias="email", serialization_alias="email")
    full_name_text: str = Field(..., validation_alias="full_name", serialization_alias="full_name")
    assigned_role: str = Field(..., validation_alias="role", serialization_alias="role")
    organization_name: str = Field(..., validation_alias="institution_name", serialization_alias="institution_name")
    account_active: int = Field(default=1, validation_alias="is_active", serialization_alias="is_active")
    registration_date: str = Field(..., validation_alias="created_at", serialization_alias="created_at")

    def __getattr__(self, name: str):
        for field_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, field_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")


class UserInDB(BaseModel):
    """Representa la estructura interna del usuario con hash de contraseña."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    user_id: int = Field(..., validation_alias="id", serialization_alias="id")
    user_email: str = Field(..., validation_alias="email", serialization_alias="email")
    password_hash_val: str = Field(..., validation_alias="password_hash", serialization_alias="password_hash")
    full_name_text: str = Field(..., validation_alias="full_name", serialization_alias="full_name")
    assigned_role: str = Field(..., validation_alias="role", serialization_alias="role")
    organization_name: str = Field(..., validation_alias="institution_name", serialization_alias="institution_name")
    account_active: int = Field(default=1, validation_alias="is_active", serialization_alias="is_active")
    registration_date: str = Field(..., validation_alias="created_at", serialization_alias="created_at")

    def to_public_user(self) -> User:
        return User(
            id=self.user_id,
            email=self.user_email,
            full_name=self.full_name_text,
            role=self.assigned_role,
            institution_name=self.organization_name,
            is_active=self.account_active,
            created_at=self.registration_date
        )

    def __getattr__(self, name: str):
        for field_name, field in self.__class__.model_fields.items():
            if field.serialization_alias == name or getattr(field, "validation_alias", None) == name:
                return getattr(self, field_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
