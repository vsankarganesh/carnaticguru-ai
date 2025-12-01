"""MCP Server for PDF-based Lesson Extraction.

Provides tools to read and search lesson content from carnatic_basics.pdf
using the Model Context Protocol.
"""

import logging
from pathlib import Path
from typing import Optional

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

# Path to PDF file - in root project directory
PDF_PATH = Path(__file__).parent.parent / "carnatic_basics.pdf"


class PDFLessonReader:
    """Reader for extracting lessons from PDF."""

    def __init__(self, pdf_path: str = str(PDF_PATH)):
        """Initialize PDF reader."""
        self.pdf_path = Path(pdf_path)
        self.content_cache = None

    def load_pdf(self) -> str:
        """Load and extract all text from PDF."""
        if self.content_cache:
            return self.content_cache

        try:
            if not self.pdf_path.exists():
                logger.error(f"PDF not found: {self.pdf_path}")
                return "PDF file not found."

            reader = PdfReader(str(self.pdf_path))
            pages_text = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(f"--- Page {page_num + 1} ---\n{text}")

            self.content_cache = "\n\n".join(pages_text)
            logger.info(f"Loaded PDF: {len(reader.pages)} pages")
            return self.content_cache

        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            return f"Error loading PDF: {str(e)}"

    def search_lesson(self, query: str) -> str:
        """Search for lesson content matching the query."""
        content = self.load_pdf()

        if "not found" in content.lower() or "error" in content.lower():
            return content

        query_lower = query.lower()
        
        # Split by page markers
        pages = content.split("--- Page")
        
        # First pass: look for pages with lesson structure (raagam + aarohana + exercise markers)
        for page_idx, page in enumerate(pages):
            if query_lower in page.lower():
                # Check if this page has rich lesson content
                # Must have raagam/aarohana (lesson metadata) AND exercise markers (||, numbered exercises)
                if ("raagam" in page.lower() and "aarohana" in page.lower() and 
                    ("||" in page)):
                    # Found a lesson page - this is it!
                    return page[:2000]
        
        # Second pass: look for pages with exercises if first pass didn't find it
        # This helps if the query just says "taatu" and there's variation in spelling
        for page_idx, page in enumerate(pages):
            if query_lower in page.lower():
                # Look for actual lesson structure (has exercises numbered or with || notation)
                # But exclude TOC (which says "Contents")
                if ("||" in page and "raagam" in page.lower()) and "Contents" not in page:
                    return page[:1500]
        
        return f"No detailed lesson found for '{query}'. Try: 'Sarali', 'Janta', 'Taatu', 'Alankar'"

    def get_lesson_summary(self) -> str:
        """Get a summary of available lessons."""
        content = self.load_pdf()

        if "not found" in content.lower() or "error" in content.lower():
            return content

        # Return first 500 chars as summary
        lines = content.split("\n")[:20]
        return "Available lessons:\n" + "\n".join(lines)


# Global reader instance
pdf_reader = PDFLessonReader()


# ============================================================================
# Tool Functions for MCP
# ============================================================================


def read_pdf_lesson(query: str) -> str:
    """Search and read lesson content from PDF.

    Args:
        query: Lesson topic to search for (e.g., "Sarali Varisai").

    Returns:
        Lesson content or error message.
    """
    return pdf_reader.search_lesson(query)


def get_available_lessons() -> str:
    """Get summary of available lessons in PDF."""
    return pdf_reader.get_lesson_summary()


def get_full_pdf_content() -> str:
    """Get full PDF content (for analysis)."""
    return pdf_reader.load_pdf()
