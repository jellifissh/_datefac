"""Input adapters for supported structured document outputs."""

from .excel import load_excel_records
from .mineru import expand_html_table, extract_mineru_records

__all__ = ["expand_html_table", "extract_mineru_records", "load_excel_records"]
