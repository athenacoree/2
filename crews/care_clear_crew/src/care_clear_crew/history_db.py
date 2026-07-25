import os
import sqlite3
import json
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL", "care_clear_history.db")

def is_postgres():
    return DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

def get_db_connection():
    if is_postgres():
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        return conn

def execute_write(query: str, params=tuple()):
    """Executes a write query. Swaps placeholder formatting for sqlite vs postgres if needed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if not is_postgres():
        # replace %s with ?
        query = query.replace("%s", "?")
    try:
        cursor.execute(query, params)
        conn.commit()
        # if insert, return last row id
        if is_postgres():
            try:
                # If we used RETURNING id, retrieve it
                last_id = cursor.fetchone()
                if last_id:
                    return last_id[0]
            except Exception:
                pass
        else:
            return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def execute_read(query: str, params=tuple()) -> list:
    """Executes a read query and returns a list of dictionaries."""
    conn = get_db_connection()
    if is_postgres():
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()
    if not is_postgres():
        query = query.replace("%s", "?")
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(dict(row))
        return results
    finally:
        cursor.close()
        conn.close()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    if is_postgres():
        # PostgreSQL syntax
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                institution_name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS authorization_requests (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                patient_name TEXT,
                policy_number TEXT,
                decision TEXT,
                confidence TEXT,
                explanation_summary TEXT,
                evidence TEXT,
                recommendations TEXT,
                raw_report_json TEXT,
                created_by_user_id INTEGER,
                created_by_name TEXT,
                created_by_institution TEXT,
                record_hash TEXT,
                previous_hash TEXT,
                institution_name TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insurer_patterns (
                id SERIAL PRIMARY KEY,
                insurer_name TEXT,
                pattern_description TEXT,
                times_observed INTEGER DEFAULT 1,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confidence_level TEXT DEFAULT 'Alto',
                institution_name TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                user_name TEXT,
                institution_name TEXT,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_limits (
                institution_name TEXT PRIMARY KEY,
                monthly_case_limit INTEGER,
                current_month_case_count INTEGER DEFAULT 0,
                alert_threshold_percent INTEGER DEFAULT 80,
                last_reset_month TEXT
            )
        """)
    else:
        # SQLite syntax
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                institution_name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS authorization_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                patient_name TEXT,
                policy_number TEXT,
                decision TEXT,
                confidence TEXT,
                explanation_summary TEXT,
                evidence TEXT,
                recommendations TEXT,
                raw_report_json TEXT,
                created_by_user_id INTEGER,
                created_by_name TEXT,
                created_by_institution TEXT,
                record_hash TEXT,
                previous_hash TEXT,
                institution_name TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insurer_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insurer_name TEXT,
                pattern_description TEXT,
                times_observed INTEGER DEFAULT 1,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence_level TEXT DEFAULT 'Alto',
                institution_name TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                institution_name TEXT,
                action TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_limits (
                institution_name TEXT PRIMARY KEY,
                monthly_case_limit INTEGER,
                current_month_case_count INTEGER DEFAULT 0,
                alert_threshold_percent INTEGER DEFAULT 80,
                last_reset_month TEXT
            )
        """)

    conn.commit()

    # Run dynamic ALTER TABLE for migrations of existing databases with safe rollback on Postgres
    # 1. insurer_patterns table -> institution_name
    try:
        cursor.execute("ALTER TABLE insurer_patterns ADD COLUMN institution_name TEXT")
        conn.commit()
    except Exception:
        if is_postgres():
            conn.rollback()

    # 2. authorization_requests columns
    cols_to_add = {
        "created_by_user_id": "INTEGER",
        "created_by_name": "TEXT",
        "created_by_institution": "TEXT",
        "record_hash": "TEXT",
        "previous_hash": "TEXT",
        "institution_name": "TEXT"
    }
    for col_name, col_type in cols_to_add.items():
        try:
            cursor.execute(f"ALTER TABLE authorization_requests ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except Exception:
            if is_postgres():
                conn.rollback()

    cursor.close()
    conn.close()

# Users Table queries
def register_user(email, password_hash, full_name, role, institution_name):
    # If postgres, we can use RETURNING id
    if is_postgres():
        query = """
            INSERT INTO users (email, password_hash, full_name, role, institution_name, is_active)
            VALUES (%s, %s, %s, %s, %s, 1) RETURNING id
        """
        return execute_write(query, (email, password_hash, full_name, role, institution_name))
    else:
        query = """
            INSERT INTO users (email, password_hash, full_name, role, institution_name, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
        """
        return execute_write(query, (email, password_hash, full_name, role, institution_name))

def get_user_by_email(email):
    query = "SELECT * FROM users WHERE LOWER(email) = LOWER(%s)"
    rows = execute_read(query, (email,))
    return rows[0] if rows else None

def get_users_by_institution(institution_name):
    query = "SELECT * FROM users WHERE LOWER(institution_name) = LOWER(%s) ORDER BY id ASC"
    return execute_read(query, (institution_name,))

def update_user_status_and_role(user_id, is_active, role, inst_name):
    query = "UPDATE users SET is_active = %s, role = %s WHERE id = %s AND LOWER(institution_name) = LOWER(%s)"
    execute_write(query, (is_active, role, user_id, inst_name))

# Insurer patterns (institution-isolated)
def save_or_update_pattern(insurer_name: str, pattern_description: str, institution_name: str, confidence_level: str = "Alto"):
    if not insurer_name or not pattern_description or not institution_name:
        return

    rows = execute_read(
        "SELECT id, times_observed FROM insurer_patterns WHERE LOWER(insurer_name) = LOWER(%s) AND LOWER(pattern_description) = LOWER(%s) AND LOWER(institution_name) = LOWER(%s)",
        (insurer_name.strip(), pattern_description.strip(), institution_name.strip())
    )
    if rows:
        pattern_id = rows[0]["id"]
        times = rows[0]["times_observed"]
        execute_write(
            "UPDATE insurer_patterns SET times_observed = %s, last_seen = CURRENT_TIMESTAMP WHERE id = %s",
            (times + 1, pattern_id)
        )
    else:
        execute_write(
            "INSERT INTO insurer_patterns (insurer_name, pattern_description, times_observed, confidence_level, institution_name) VALUES (%s, %s, 1, %s, %s)",
            (insurer_name.strip(), pattern_description.strip(), confidence_level, institution_name.strip())
        )

def get_patterns_for_insurer(insurer_name: str, institution_name: str):
    if not insurer_name or not institution_name:
        return []
    rows = execute_read(
        "SELECT pattern_description, times_observed, last_seen, confidence_level FROM insurer_patterns WHERE LOWER(insurer_name) = LOWER(%s) AND LOWER(institution_name) = LOWER(%s) ORDER BY times_observed DESC",
        (insurer_name.strip(), institution_name.strip())
    )
    return rows

def get_all_patterns(institution_name: str):
    if not institution_name:
        return []
    rows = execute_read(
        "SELECT insurer_name, pattern_description, times_observed, last_seen, confidence_level FROM insurer_patterns WHERE LOWER(institution_name) = LOWER(%s) ORDER BY times_observed DESC",
        (institution_name.strip(),)
    )
    return rows

# Trust Ledger and Authorization Requests
def compute_record_hash(prev_hash: str, patient_name: str, policy_number: str, decision: str, created_by_user_id: int) -> str:
    payload = f"{prev_hash or ''}|{patient_name or ''}|{policy_number or ''}|{decision or ''}|{created_by_user_id or 0}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def get_last_record_hash(institution_name: str) -> str:
    rows = execute_read(
        "SELECT record_hash FROM authorization_requests WHERE LOWER(institution_name) = LOWER(%s) ORDER BY id DESC LIMIT 1",
        (institution_name,)
    )
    return rows[0]["record_hash"] if rows else ""

def save_request(report_data: dict, user_id: int, user_name: str, institution_name: str):
    patient_name = report_data.get("patient_name", "N/A")
    policy_number = report_data.get("policy_number", "N/A")
    decision = report_data.get("decision", "N/A")
    confidence = report_data.get("confidence", "N/A")
    explanation_summary = report_data.get("explanation_summary", "N/A")
    evidence = report_data.get("evidence", "N/A")
    recommendations = report_data.get("recommendations", "N/A")

    # Calculate blockchain Trust Ledger hashes
    prev_hash = get_last_record_hash(institution_name)
    rec_hash = compute_record_hash(prev_hash, patient_name, policy_number, decision, user_id)

    # Save the request
    # Since sqlite and postgres syntax might differ on SERIAL, use execute_write
    query = """
        INSERT INTO authorization_requests (
            patient_name, policy_number, decision, confidence,
            explanation_summary, evidence, recommendations, raw_report_json,
            created_by_user_id, created_by_name, created_by_institution,
            record_hash, previous_hash, institution_name
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_write(query, (
        patient_name, policy_number, decision, confidence,
        explanation_summary, evidence, recommendations, json.dumps(report_data, ensure_ascii=False),
        user_id, user_name, institution_name, rec_hash, prev_hash, institution_name
    ))

def get_history(institution_name: str, user_id: int = None, search_query: str = None, filter_status: str = None, role: str = "operativo"):
    """
    Get history with role-based and multi-tenant isolation.
    - Operativo: can only see their own cases.
    - Administrador: can see all cases from their institution.
    """
    if not institution_name:
        return []

    query = """
        SELECT timestamp, patient_name, policy_number, decision, confidence, explanation_summary,
               evidence, recommendations, raw_report_json, id, created_by_name, record_hash
        FROM authorization_requests
        WHERE LOWER(institution_name) = LOWER(%s)
    """
    params = [institution_name]

    if role == "operativo" and user_id is not None:
        query += " AND created_by_user_id = %s"
        params.append(user_id)

    if search_query:
        query += " AND (LOWER(patient_name) LIKE LOWER(%s) OR LOWER(policy_number) LIKE LOWER(%s))"
        search_pattern = f"%{search_query.lower()}%"
        params.extend([search_pattern, search_pattern])

    if filter_status and filter_status != "Todos":
        query += " AND decision = %s"
        params.append(filter_status)

    query += " ORDER BY timestamp DESC"
    rows = execute_read(query, tuple(params))

    results = []
    for r in rows:
        results.append({
            "timestamp": str(r.get("timestamp")),
            "patient_name": r.get("patient_name"),
            "policy_number": r.get("policy_number"),
            "decision": r.get("decision"),
            "confidence": r.get("confidence"),
            "explanation_summary": r.get("explanation_summary"),
            "evidence": r.get("evidence"),
            "recommendations": r.get("recommendations"),
            "raw_report_json": json.loads(r.get("raw_report_json")) if r.get("raw_report_json") else {},
            "id": r.get("id"),
            "created_by_name": r.get("created_by_name"),
            "record_hash": r.get("record_hash")
        })
    return results

# Activity Log
def log_activity(user_id, user_name, institution_name, action, details=None):
    query = """
        INSERT INTO activity_log (user_id, user_name, institution_name, action, details)
        VALUES (%s, %s, %s, %s, %s)
    """
    execute_write(query, (user_id, user_name, institution_name, action, details))

def get_recent_activity(institution_name, limit=50):
    query = """
        SELECT timestamp, user_name, action, details FROM activity_log
        WHERE LOWER(institution_name) = LOWER(%s)
        ORDER BY timestamp DESC LIMIT %s
    """
    return execute_read(query, (institution_name, limit))

# Usage Limits and Control
def check_and_reset_limits_if_new_month(institution_name):
    import datetime
    now = datetime.datetime.utcnow()
    current_ym = now.strftime("%Y-%m")

    rows = execute_read("SELECT monthly_case_limit, current_month_case_count, last_reset_month FROM usage_limits WHERE LOWER(institution_name) = LOWER(%s)", (institution_name,))

    if not rows:
        # Create default unlimited row
        execute_write(
            "INSERT INTO usage_limits (institution_name, monthly_case_limit, current_month_case_count, alert_threshold_percent, last_reset_month) VALUES (%s, NULL, 0, 80, %s)",
            (institution_name, current_ym)
        )
        return {
            "monthly_case_limit": None,
            "current_month_case_count": 0,
            "alert_threshold_percent": 80
        }

    limit_info = rows[0]
    if limit_info.get("last_reset_month") != current_ym:
        # Reset counter for the new month
        execute_write(
            "UPDATE usage_limits SET current_month_case_count = 0, last_reset_month = %s WHERE LOWER(institution_name) = LOWER(%s)",
            (current_ym, institution_name)
        )
        limit_info["current_month_case_count"] = 0

    return limit_info

def check_usage_allowed(institution_name) -> bool:
    """Returns True if the institution has not exceeded its limit, False otherwise."""
    limit_info = check_and_reset_limits_if_new_month(institution_name)
    monthly_limit = limit_info.get("monthly_case_limit")
    current_count = limit_info.get("current_month_case_count", 0)

    if monthly_limit is None:
        return True
    return current_count < monthly_limit

def increment_case_count(institution_name):
    check_and_reset_limits_if_new_month(institution_name)
    execute_write(
        "UPDATE usage_limits SET current_month_case_count = current_month_case_count + 1 WHERE LOWER(institution_name) = LOWER(%s)",
        (institution_name,)
    )

def update_usage_limit_settings(institution_name, limit, alert_threshold=80):
    check_and_reset_limits_if_new_month(institution_name)
    execute_write(
        "UPDATE usage_limits SET monthly_case_limit = %s, alert_threshold_percent = %s WHERE LOWER(institution_name) = LOWER(%s)",
        (limit, alert_threshold, institution_name)
    )

# Executive Analytics Panel dashboard queries (institution-isolated)
def get_stats_summary(institution_name):
    if not institution_name:
        return {"total_cases": 0, "approved": 0, "denied": 0, "approved_rate": 0.0}

    total = execute_read("SELECT COUNT(*) as count FROM authorization_requests WHERE LOWER(institution_name) = LOWER(%s)", (institution_name,))
    approved = execute_read("SELECT COUNT(*) as count FROM authorization_requests WHERE LOWER(institution_name) = LOWER(%s) AND LOWER(decision) = 'aprobado'", (institution_name,))
    denied = execute_read("SELECT COUNT(*) as count FROM authorization_requests WHERE LOWER(institution_name) = LOWER(%s) AND LOWER(decision) = 'denegado'", (institution_name,))

    total_val = total[0]["count"] if total else 0
    approved_val = approved[0]["count"] if approved else 0
    denied_val = denied[0]["count"] if denied else 0

    rate = (approved_val / total_val * 100) if total_val > 0 else 0.0
    return {
        "total_cases": total_val,
        "approved": approved_val,
        "denied": denied_val,
        "approved_rate": round(rate, 1)
    }

def get_stats_by_insurer(institution_name):
    query = """
        SELECT COALESCE(raw_report_json::json->>'insurer_name', 'Desconocido') as insurer_name, COUNT(*) as count
        FROM authorization_requests
        WHERE LOWER(institution_name) = LOWER(%s)
        GROUP BY 1
    """
    if not is_postgres():
        # SQLite raw_report_json parsing
        query = """
            SELECT COALESCE(json_extract(raw_report_json, '$.insurer_name'), 'Desconocido') as insurer_name, COUNT(*) as count
            FROM authorization_requests
            WHERE LOWER(institution_name) = LOWER(%s)
            GROUP BY 1
        """
    return execute_read(query, (institution_name,))

def get_top_denial_reasons(institution_name):
    # Retrieve explanations for denied requests
    query = """
        SELECT explanation_summary, patient_name
        FROM authorization_requests
        WHERE LOWER(institution_name) = LOWER(%s) AND LOWER(decision) = 'denegado'
    """
    return execute_read(query, (institution_name,))

def clear_all_history(institution_name: str):
    """Wipes only historical data of the specified institution (Task D Security Fix)."""
    if not institution_name:
        return
    execute_write("DELETE FROM authorization_requests WHERE LOWER(institution_name) = LOWER(%s)", (institution_name,))
    execute_write("DELETE FROM insurer_patterns WHERE LOWER(institution_name) = LOWER(%s)", (institution_name,))
    execute_write("DELETE FROM activity_log WHERE LOWER(institution_name) = LOWER(%s)", (institution_name,))
    execute_write("DELETE FROM usage_limits WHERE LOWER(institution_name) = LOWER(%s)", (institution_name,))

def clear_all_history_global():
    """Wipes all historical data globally across all tenants."""
    execute_write("DELETE FROM authorization_requests")
    execute_write("DELETE FROM insurer_patterns")
    execute_write("DELETE FROM activity_log")
    execute_write("DELETE FROM usage_limits")
