from dataclasses import dataclass


@dataclass
class DocumentRunState:
    doc_name: str
    pdf_path: str
    asset_package_path: str
    markdown_cache_path: str
    markdown_available: bool = False
    vision_attempted: bool = False
    vision_success: bool = False
    vision_error: str = ""
    pdfplumber_attempted: bool = False
    pdfplumber_success: bool = False
    marker_attempted: bool = False
    table_count: int = 0
    ai_summary_success: bool = False
    status: str = "PENDING"
    error_message: str = ""
