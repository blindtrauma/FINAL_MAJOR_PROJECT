# app/services/document_parser.py - Service for parsing document files

import os
import sys
from typing import Dict, Any
from app.core.exceptions import DocumentProcessingError # Import custom exception

# Import parsing libraries (make sure they are in requirements.txt)
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    print("Warning: PyMuPDF not installed. PDF parsing disabled.")

try:
    from docx import Document # python-docx
except ImportError:
    Document = None
    print("Warning: python-docx not installed. DOCX parsing disabled.")

class DocumentParser:
    """
    Handles parsing text content from various document types (PDF, DOCX).
    """

    def parse_document(self, file_path: str) -> str:
        """
        Parses the text content from a given file path based on its extension.
        """
        if not os.path.exists(file_path):
            raise DocumentProcessingError(file_path, detail="File not found.")

        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()

        text_content = ""
        if file_extension == ".pdf":
            text_content = self._parse_pdf(file_path)
        elif file_extension == ".docx":
            text_content = self._parse_docx(file_path)
        elif file_extension == ".txt":
             with open(file_path, 'r', encoding='utf-8') as f:
                 text_content = f.read()
        else:
            # For unsupported types, try basic text read or raise error
            # raise DocumentProcessingError(file_path, detail=f"Unsupported file type: {file_extension}")
             print(f"Warning: Unsupported file type '{file_extension}'. Attempting basic text read.")
             try:
                 with open(file_path, 'r', encoding='utf-8') as f:
                     text_content = f.read()
             except Exception as e:
                  raise DocumentProcessingError(file_path, detail=f"Unsupported file type or basic read failed: {file_extension}, {e}")


        if not text_content.strip():
             print(f"Warning: No text content extracted from {file_path}")
             # Decide if this should raise an error or return empty
             # raise DocumentProcessingError(file_path, detail="No text content extracted.")

        return text_content.strip()

    def _parse_pdf(self, file_path: str) -> str:
        """Parses text from a PDF file using PyMuPDF."""
        if not fitz:
            raise DocumentProcessingError(file_path, detail="PyMuPDF not installed to parse PDF.")
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise DocumentProcessingError(file_path, detail=f"Failed to parse PDF: {e}")

    def _parse_docx(self, file_path: str) -> str:
        """Parses text from a DOCX file using python-docx."""
        if not Document:
            raise DocumentProcessingError(file_path, detail="python-docx not installed to parse DOCX.")
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise DocumentProcessingError(file_path, detail=f"Failed to parse DOCX: {e}")