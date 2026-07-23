import docx2txt
from typing import Dict, Any
from pydantic import Field
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource

class DOCXKnowledgeSource(BaseKnowledgeSource):
    file_paths: list = Field(description="List of DOCX file paths")

    def load_content(self) -> Dict[Any, str]:
        content = {}
        for file_path in self.file_paths:
            try:
                text = docx2txt.process(file_path)
                content[file_path] = text
            except Exception as e:
                raise ValueError(f"Failed to read DOCX file {file_path}: {e}")
        return content

    def validate_content(self, content: Any) -> bool:
        return True

    def add(self) -> None:
        content = self.load_content()
        for _, text in content.items():
            chunks = self._chunk_text(text)
            self.chunks.extend(chunks)
        self._save_documents()
