import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai_tools import PDFSearchTool
from med_auth_agent.llm_provider import get_llm
from med_auth_agent.schemas import DecisionReport
from med_auth_agent.docx_knowledge_source import DOCXKnowledgeSource

@CrewBase
class MedAuthAgent():
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self, knowledge_files: list = None):
        super().__init__()
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

    @agent
    def med_auth_officer(self) -> Agent:
        return Agent(
            config=self.agents_config['med_auth_officer'],
            verbose=True,
            llm=get_llm(),
            tools=[PDFSearchTool()]
        )

    @task
    def analyze_medical_request_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_medical_request_task'],
            output_json=DecisionReport
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            knowledge_sources=self.knowledge_sources if self.knowledge_sources else None
        )
