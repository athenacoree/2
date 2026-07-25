#!/usr/bin/env python
import os
import sqlite3
import psycopg2
import json

SQLITE_PATH = "care_clear_history.db"
POSTGRES_URL = os.getenv("DATABASE_URL")

def migrate():
    if not POSTGRES_URL:
        print("DATABASE_URL no configurada. No se puede migrar a Postgres.")
        return

    if not os.path.exists(SQLITE_PATH):
        print(f"No se encontró base SQLite previa en {SQLITE_PATH} para migrar.")
        return

    print("Iniciando migración de SQLite a PostgreSQL...")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    pg_conn = psycopg2.connect(POSTGRES_URL)
    pg_cursor = pg_conn.cursor()

    # Migrate users
    try:
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        for u in users:
            pg_cursor.execute("""
                INSERT INTO users (id, email, password_hash, full_name, role, institution_name, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, (
                u['id'], u['email'], u['password_hash'], u['full_name'], u['role'],
                u['institution_name'], u['is_active'], u['created_at']
            ))
        print(f"Migrados {len(users)} usuarios.")
    except Exception as e:
        print(f"Nota/Error migrando usuarios: {e}")
        pg_conn.rollback()

    # Migrate authorization_requests
    try:
        sqlite_cursor.execute("SELECT * FROM authorization_requests")
        reqs = sqlite_cursor.fetchall()
        for r in reqs:
            # Map row keys dynamically in case of missing columns in older SQLite
            keys = r.keys()
            pg_cursor.execute("""
                INSERT INTO authorization_requests (
                    id, timestamp, patient_name, policy_number, decision, confidence,
                    explanation_summary, evidence, recommendations, raw_report_json,
                    created_by_user_id, created_by_name, created_by_institution,
                    record_hash, previous_hash, institution_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                r['id'], r['timestamp'], r['patient_name'], r['policy_number'], r['decision'],
                r['confidence'], r['explanation_summary'], r['evidence'], r['recommendations'],
                r['raw_report_json'],
                r['created_by_user_id'] if 'created_by_user_id' in keys else None,
                r['created_by_name'] if 'created_by_name' in keys else None,
                r['created_by_institution'] if 'created_by_institution' in keys else None,
                r['record_hash'] if 'record_hash' in keys else None,
                r['previous_hash'] if 'previous_hash' in keys else None,
                r['institution_name'] if 'institution_name' in keys else None
            ))
        print(f"Migrados {len(reqs)} análisis históricos.")
    except Exception as e:
        print(f"Nota/Error migrando solicitudes: {e}")
        pg_conn.rollback()

    # Migrate insurer_patterns
    try:
        sqlite_cursor.execute("SELECT * FROM insurer_patterns")
        patterns = sqlite_cursor.fetchall()
        for p in patterns:
            keys = p.keys()
            pg_cursor.execute("""
                INSERT INTO insurer_patterns (id, insurer_name, pattern_description, times_observed, last_seen, confidence_level, institution_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                p['id'], p['insurer_name'], p['pattern_description'], p['times_observed'], p['last_seen'],
                p['confidence_level'], p['institution_name'] if 'institution_name' in keys else 'Default'
            ))
        print(f"Migrados {len(patterns)} patrones aprendidos de aseguradoras.")
    except Exception as e:
        print(f"Nota/Error migrando patrones: {e}")
        pg_conn.rollback()

    # Migrate activity_log
    try:
        sqlite_cursor.execute("SELECT * FROM activity_log")
        logs = sqlite_cursor.fetchall()
        for l in logs:
            pg_cursor.execute("""
                INSERT INTO activity_log (id, user_id, user_name, institution_name, action, timestamp, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                l['id'], l['user_id'], l['user_name'], l['institution_name'], l['action'], l['timestamp'], l['details']
            ))
        print(f"Migrados {len(logs)} registros de actividad.")
    except Exception as e:
        print(f"Nota/Error migrando activity_log: {e}")
        pg_conn.rollback()

    # Migrate usage_limits
    try:
        sqlite_cursor.execute("SELECT * FROM usage_limits")
        limits = sqlite_cursor.fetchall()
        for lim in limits:
            pg_cursor.execute("""
                INSERT INTO usage_limits (institution_name, monthly_case_limit, current_month_case_count, alert_threshold_percent, last_reset_month)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (institution_name) DO NOTHING
            """, (
                lim['institution_name'], lim['monthly_case_limit'], lim['current_month_case_count'], lim['alert_threshold_percent'], lim['last_reset_month']
            ))
        print(f"Migrados {len(limits)} límites de consumo mensual.")
    except Exception as e:
        print(f"Nota/Error migrando límites de consumo: {e}")
        pg_conn.rollback()

    pg_conn.commit()
    pg_cursor.close()
    pg_conn.close()
    sqlite_conn.close()
    print("Migración completada de manera exitosa!")

if __name__ == "__main__":
    migrate()
