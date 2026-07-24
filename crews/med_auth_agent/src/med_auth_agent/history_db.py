import sqlite3
import json
import os

DB_PATH = os.getenv("DATABASE_URL", "med_auth_history.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
            raw_report_json TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insurer_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insurer_name TEXT,
            pattern_description TEXT,
            times_observed INTEGER DEFAULT 1,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            confidence_level TEXT DEFAULT 'Alto'
        )
    """)
    conn.commit()
    conn.close()

def save_or_update_pattern(insurer_name: str, pattern_description: str, confidence_level: str = "Alto"):
    if not insurer_name or not pattern_description:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, times_observed FROM insurer_patterns WHERE LOWER(insurer_name) = ? AND LOWER(pattern_description) = ?",
        (insurer_name.lower().strip(), pattern_description.lower().strip())
    )
    row = cursor.fetchone()
    if row:
        pattern_id, times = row
        cursor.execute(
            "UPDATE insurer_patterns SET times_observed = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?",
            (times + 1, pattern_id)
        )
    else:
        cursor.execute(
            "INSERT INTO insurer_patterns (insurer_name, pattern_description, times_observed, confidence_level) VALUES (?, ?, 1, ?)",
            (insurer_name.strip(), pattern_description.strip(), confidence_level)
        )
    conn.commit()
    conn.close()

def get_patterns_for_insurer(insurer_name: str):
    if not insurer_name:
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT pattern_description, times_observed, last_seen, confidence_level FROM insurer_patterns WHERE LOWER(insurer_name) = ? ORDER BY times_observed DESC",
        (insurer_name.lower().strip(),)
    )
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "pattern_description": r[0],
            "times_observed": r[1],
            "last_seen": r[2],
            "confidence_level": r[3]
        })
    return results

def get_all_patterns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT insurer_name, pattern_description, times_observed, last_seen, confidence_level FROM insurer_patterns ORDER BY times_observed DESC")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "insurer_name": r[0],
            "pattern_description": r[1],
            "times_observed": r[2],
            "last_seen": r[3],
            "confidence_level": r[4]
        })
    return results

def save_request(report_data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO authorization_requests (
            patient_name, policy_number, decision, confidence,
            explanation_summary, evidence, recommendations, raw_report_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_data.get("patient_name", "N/A"),
        report_data.get("policy_number", "N/A"),
        report_data.get("decision", "N/A"),
        report_data.get("confidence", "N/A"),
        report_data.get("explanation_summary", "N/A"),
        report_data.get("evidence", "N/A"),
        report_data.get("recommendations", "N/A"),
        json.dumps(report_data, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()

def get_history(search_query: str = None, filter_status: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT timestamp, patient_name, policy_number, decision, confidence, explanation_summary, evidence, recommendations, raw_report_json, id FROM authorization_requests WHERE 1=1"
    params = []

    if search_query:
        query += " AND (patient_name LIKE ? OR policy_number LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if filter_status and filter_status != "Todos":
        query += " AND decision = ?"
        params.append(filter_status)

    query += " ORDER BY timestamp DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "timestamp": r[0],
            "patient_name": r[1],
            "policy_number": r[2],
            "decision": r[3],
            "confidence": r[4],
            "explanation_summary": r[5],
            "evidence": r[6],
            "recommendations": r[7],
            "raw_report_json": json.loads(r[8]) if r[8] else {},
            "id": r[9]
        })
    return results

def clear_all_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM authorization_requests")
    cursor.execute("DELETE FROM insurer_patterns")
    conn.commit()
    conn.close()
