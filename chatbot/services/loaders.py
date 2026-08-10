from langchain_community.document_loaders import (
    PyPDFLoader,
    CSVLoader,
    TextLoader,
    Docx2txtLoader,
)
from pathlib import Path
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger




class LoaderService:
    def load_document(self, file_path: str):
        try:
            extension = Path(file_path).suffix.lower()
            if extension == ".pdf":
                loader = PyPDFLoader(file_path)
            elif extension == ".csv":
                loader = CSVLoader(file_path)
            elif extension == ".txt":
                loader = TextLoader(file_path)
            elif extension == ".docx":
                loader = Docx2txtLoader(file_path)
            else:
                return False, "Unsupported file type", None
            
            documents = loader.load()
            return True, "Document loaded successfully", documents
        except Exception as e:
            logger.error(f"Error loading document: {e}")
            return False, "Error loading document", None
