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
    conn.commit()
    conn.close()

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
    conn.commit()
    conn.close()
