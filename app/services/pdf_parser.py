"""
ScholarPilot EU — Document Resume Parser Wrapper (PDF & Word DOCX/DOC)
Re-exports document_parser.parse_resume_document for backwards compatibility.
"""

from app.services.document_parser import (
    parse_resume_document,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_doc,
    extract_text_from_document
)

def parse_pdf_resume(file_bytes: bytes, filename: str = ""):
    """Wrapper supporting PDF and Word documents."""
    return parse_resume_document(file_bytes, filename)
