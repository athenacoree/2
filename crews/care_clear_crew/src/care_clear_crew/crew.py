import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai_tools import PDFSearchTool
from care_clear_crew.llm_provider import get_llm
from care_clear_crew.schemas import DecisionReport, AppealLetter, PrecheckReport
from care_clear_crew.docx_knowledge_source import DOCXKnowledgeSource

@CrewBase
class CareClearCrew():
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self, knowledge_files: list = None, insurer_name: str = ""):
        self.insurer_name = insurer_name
        self.knowledge_sources = []
        if knowledge_files:
            for file_path in knowledge_files:
                if not os.path.exists(file_path):
                    continue
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.pdf':
                    self.knowledge_sources.append(PDFKnowledgeSource(file_paths=[file_path]))
                elif ext == '.txt':
                    self.knowledge_sources.append(TextFileKnowledgeSource(file_paths=[file_path]))
                elif ext in ['.docx', '.doc']:
                    self.knowledge_sources.append(DOCXKnowledgeSource(file_paths=[file_path]))

        if self.insurer_name:
            from care_clear_crew.history_db import get_patterns_for_insurer
            patterns = get_patterns_for_insurer(self.insurer_name)
            if patterns:
                temp_filename = "temp_insurer_patterns.txt"
                content = f"PREVIOUSLY LEARNED PATTERNS FOR INSURER {self.insurer_name}:\n"
                for p in patterns:
                    content += f"- {p['pattern_description']} (Observed {p['times_observed']} times, Confidence: {p['confidence_level']})\n"
                with open(temp_filename, "w", encoding="utf-8") as temp_f:
                    temp_f.write(content)
                self.knowledge_sources.append(TextFileKnowledgeSource(file_paths=[temp_filename]))

    @agent
    def patient_intake_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['patient_intake_agent'],
            verbose=True,
            llm=get_llm()
        )

    @agent
    def insurance_authorization_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['insurance_authorization_agent'],
            verbose=True,
            llm=get_llm()
        )

    @agent
    def clinical_scribing_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['clinical_scribing_agent'],
            verbose=True,
            llm=get_llm()
        )

    @agent
    def decision_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['decision_agent'],
            verbose=True,
            llm=get_llm(),
            tools=[PDFSearchTool()]
        )

    @agent
    def appeal_writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['appeal_writer_agent'],
            verbose=True,
            llm=get_llm()
        )

    @task
    def patient_intake_task(self) -> Task:
        return Task(
            config=self.tasks_config['patient_intake_task']
        )

    @task
    def insurance_authorization_task(self) -> Task:
        return Task(
            config=self.tasks_config['insurance_authorization_task']
        )

    @task
    def clinical_scribing_task(self) -> Task:
        return Task(
            config=self.tasks_config['clinical_scribing_task']
        )

    @task
    def decision_task(self) -> Task:
        return Task(
            config=self.tasks_config['decision_task'],
            output_json=DecisionReport
        )

    @task
    def appeal_writing_task(self) -> Task:
        return Task(
            config=self.tasks_config['appeal_writing_task'],
            output_json=AppealLetter
        )

    @task
    def precheck_task(self) -> Task:
        return Task(
            config=self.tasks_config['precheck_task'],
            output_json=PrecheckReport
        )

    def run_precheck_crew(self) -> PrecheckReport:
        p_intake = self.patient_intake_task()
        i_auth = self.insurance_authorization_task()
        c_scribe = self.clinical_scribing_task()
        p_check = self.precheck_task()

        precheck_crew = Crew(
            agents=self.agents,
            tasks=[p_intake, i_auth, c_scribe, p_check],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=self.knowledge_sources if self.knowledge_sources else None
        )

        result = precheck_crew.kickoff()
        import json
        try:
            parsed = json.loads(result.raw)
            return PrecheckReport(**parsed)
        except Exception:
            return PrecheckReport(
                approval_probability="50%",
                missing_critical_items=[],
                recommendations_to_improve="No se pudo procesar la simulación de manera óptima. Por favor intente cargando documentos clínicos legibles."
            )

    def run_appeal_crew(self, decision_report_data: dict) -> AppealLetter:
        writer_agent = self.appeal_writer_agent()

        failed_pts_desc = ""
        failed_pts = [p for p in decision_report_data.get("evaluated_points", []) if p.get("status") == "No Cumple"]
        for pt in failed_pts:
            failed_pts_desc += f"- {pt.get('name')}: {pt.get('explanation')}\n"

        task_desc = self.tasks_config['appeal_writing_task']['description'] + f"\n\nREPORT DATA:\nPatient: {decision_report_data.get('patient_name')}\nPolicy: {decision_report_data.get('policy_number')}\nDecision: Denegado\n\nFAILED POINTS:\n{failed_pts_desc}\n"

        writing_task = Task(
            description=task_desc,
            expected_output=self.tasks_config['appeal_writing_task']['expected_output'],
            agent=writer_agent,
            output_json=AppealLetter
        )

        appeal_crew = Crew(
            agents=[writer_agent],
            tasks=[writing_task],
            process=Process.sequential,
            verbose=True
        )

        result = appeal_crew.kickoff()
        import json
        try:
            parsed = json.loads(result.raw)
            return AppealLetter(**parsed)
        except Exception:
            return AppealLetter(
                subject=f"RE: Apelación de Autorización Previa - Paciente {decision_report_data.get('patient_name')}",
                body=f"Por medio de la presente, apelamos formalmente la decisión de denegación para el paciente {decision_report_data.get('patient_name')} (Póliza {decision_report_data.get('policy_number')}).\n\nCriterios no cumplidos evaluados:\n{failed_pts_desc}\n\nSolicitamos la reconsideración del caso adjuntando la evidencia faltante.",
                cited_points=[pt.get('name') for pt in failed_pts]
            )

    @crew
    def crew(self, feedback: str = "") -> Crew:
        decision_task_obj = self.decision_task()
        decision_task_obj.description = decision_task_obj.description.format(feedback=feedback)

        return Crew(
            agents=self.agents,
            tasks=[
                self.patient_intake_task(),
                self.insurance_authorization_task(),
                self.clinical_scribing_task(),
                decision_task_obj
            ],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=self.knowledge_sources if self.knowledge_sources else None
        )
