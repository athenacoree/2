import json
import logging
import pandas as pd
from care_clear_crew.crew import CareClearCrew

def run_analysis_with_retry(agent_system: CareClearCrew, max_attempts: int = 3, status_container = None) -> dict:
    feedback = ""
    results_json = None
    last_exception = None
    raw_response = None

    for attempt in range(max_attempts):
        if attempt > 0 and status_container is not None:
            try:
                status_container.warning(f"Reintentando análisis (Intento {attempt + 1}/{max_attempts}) debido a error de formato JSON...")
            except Exception:
                pass

        try:
            crew_run = agent_system.crew(feedback=feedback).kickoff()
            raw_response = crew_run.raw
            results_json = json.loads(raw_response)
            break
        except Exception as inner_e:
            logging.exception("Error en intento de parseo de JSON en pipeline asíncrono")
            last_exception = inner_e
            feedback = (
                f"\n\nCRITICAL ERROR from previous attempt: The previous response could not be parsed as valid JSON. "
                f"Error: {str(inner_e)}. "
                f"You MUST return ONLY a strictly valid JSON object matching the schema. No markdown formatting outside the JSON, "
                f"no extra explanations before or after the JSON."
            )

    if results_json is None:
        try:
            with open("care_clear_errors.log", "a", encoding="utf-8") as log_f:
                log_f.write(f"--- ERROR AT {pd.Timestamp.now()} ---\n")
                log_f.write(f"Exception: {str(last_exception)}\n")
                log_f.write(f"Raw LLM Response: {str(raw_response)}\n\n")
        except Exception:
            pass

    return results_json
