import bcrypt
from datetime import datetime

class User:
    def __init__(self, id, email, password_hash, full_name, role, institution_name, is_active=1, created_at=None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.role = role  # 'operativo' or 'administrador'
        self.institution_name = institution_name
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow().isoformat()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password_str: str) -> bool:
    """Verify a password against a hash."""
    if not hashed_password_str:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password_str.encode('utf-8'))
    except Exception:
        return False

def create_user_record(email, password, full_name, role, institution_name):
    """
    Validates and creates a new user.
    Note: Database-level registration/checks are done in history_db.py.
    """
    from care_clear_crew.history_db import register_user, get_user_by_email, get_users_by_institution

    email_clean = email.strip().lower()
    if get_user_by_email(email_clean):
        raise ValueError("El correo electrónico ya está registrado.")

    pwd_hash = hash_password(password)

    # Rule Tarea C: El primer usuario que se registre para una institución nueva debe asignarse automáticamente como administrador
    existing_inst_users = get_users_by_institution(institution_name)
    if not existing_inst_users:
        role = "administrador"

    user_id = register_user(email_clean, pwd_hash, full_name.strip(), role, institution_name.strip())
    return user_id

def verify_login(email, password):
    """
    Verifies credentials and returns user details as a dict (or None).
    """
    from care_clear_crew.history_db import get_user_by_email
    email_clean = email.strip().lower()
    user_data = get_user_by_email(email_clean)
    if not user_data:
        return None

    if not verify_password(password, user_data.get("password_hash")):
        return None

    if not user_data.get("is_active"):
        raise PermissionError("Tu cuenta está desactivada. Por favor contacta a tu administrador.")

    return user_data

def require_role(session_user, allowed_roles):
    """
    Validates if the current user has one of the allowed roles.
    """
    if not session_user:
        return False
    return session_user.get("role") in allowed_roles
