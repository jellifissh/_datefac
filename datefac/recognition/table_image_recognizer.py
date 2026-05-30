from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from datefac.domain.extracted_table import ExtractedTable


@dataclass
class TableImageRecognizer:
    name: str
    version: str

    def is_available(self) -> bool:
        return False

    def recognize(self, image_path: str, table_asset_id: str, source_doc_name: str, table_role_guess: str) -> ExtractedTable:
        return ExtractedTable(
            extracted_table_id=f"{table_asset_id}__none",
            table_asset_id=table_asset_id,
            source_doc_name=source_doc_name,
            table_role_guess=table_role_guess,
            image_path=image_path,
            recognizer_name=self.name,
            recognizer_version=self.version,
            recognition_status="RECOGNIZER_UNAVAILABLE",
            row_count=0,
            col_count=0,
            cell_count=0,
            non_empty_cell_count=0,
            raw_text="",
            table_grid=[],
            cells=[],
            warnings=["recognizer unavailable"],
        )


class NoneRecognizer(TableImageRecognizer):
    def __init__(self) -> None:
        super().__init__(name="none", version="1.0")

    def is_available(self) -> bool:
        return True

    def recognize(self, image_path: str, table_asset_id: str, source_doc_name: str, table_role_guess: str) -> ExtractedTable:
        return ExtractedTable(
            extracted_table_id=f"{table_asset_id}__none",
            table_asset_id=table_asset_id,
            source_doc_name=source_doc_name,
            table_role_guess=table_role_guess,
            image_path=image_path,
            recognizer_name=self.name,
            recognizer_version=self.version,
            recognition_status="RECOGNIZER_UNAVAILABLE",
            row_count=0,
            col_count=0,
            cell_count=0,
            non_empty_cell_count=0,
            raw_text="",
            table_grid=[],
            cells=[],
            warnings=["mode=none; selection only"],
        )


class OCRTextOnlyRecognizer(TableImageRecognizer):
    def __init__(self) -> None:
        super().__init__(name="ocr_text_only", version="1.0")
        self._available = False
        self._engine = None
        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore

            self._available = True
            self._engine = (pytesseract, Image)
        except Exception:
            self._available = False
            self._engine = None

    def is_available(self) -> bool:
        return self._available

    def recognize(self, image_path: str, table_asset_id: str, source_doc_name: str, table_role_guess: str) -> ExtractedTable:
        if not self._available or self._engine is None:
            return ExtractedTable(
                extracted_table_id=f"{table_asset_id}__ocr_text_only",
                table_asset_id=table_asset_id,
                source_doc_name=source_doc_name,
                table_role_guess=table_role_guess,
                image_path=image_path,
                recognizer_name=self.name,
                recognizer_version=self.version,
                recognition_status="RECOGNIZER_UNAVAILABLE",
                row_count=0,
                col_count=0,
                cell_count=0,
                non_empty_cell_count=0,
                raw_text="",
                table_grid=[],
                cells=[],
                warnings=["ocr_text_only dependencies unavailable"],
            )

        if not Path(image_path).exists():
            return ExtractedTable(
                extracted_table_id=f"{table_asset_id}__ocr_text_only",
                table_asset_id=table_asset_id,
                source_doc_name=source_doc_name,
                table_role_guess=table_role_guess,
                image_path=image_path,
                recognizer_name=self.name,
                recognizer_version=self.version,
                recognition_status="IMAGE_MISSING",
                row_count=0,
                col_count=0,
                cell_count=0,
                non_empty_cell_count=0,
                raw_text="",
                table_grid=[],
                cells=[],
                warnings=["image missing"],
            )

        pytesseract, Image = self._engine
        try:
            txt = pytesseract.image_to_string(Image.open(image_path))
            txt = (txt or "").strip()
        except Exception as exc:
            return ExtractedTable(
                extracted_table_id=f"{table_asset_id}__ocr_text_only",
                table_asset_id=table_asset_id,
                source_doc_name=source_doc_name,
                table_role_guess=table_role_guess,
                image_path=image_path,
                recognizer_name=self.name,
                recognizer_version=self.version,
                recognition_status="FAILED",
                row_count=0,
                col_count=0,
                cell_count=0,
                non_empty_cell_count=0,
                raw_text="",
                table_grid=[],
                cells=[],
                warnings=[f"ocr failed: {exc}"],
            )

        lines = [x.strip() for x in txt.splitlines() if x.strip()]
        return ExtractedTable(
            extracted_table_id=f"{table_asset_id}__ocr_text_only",
            table_asset_id=table_asset_id,
            source_doc_name=source_doc_name,
            table_role_guess=table_role_guess,
            image_path=image_path,
            recognizer_name=self.name,
            recognizer_version=self.version,
            recognition_status="RECOGNIZED_TEXT_ONLY",
            row_count=len(lines),
            col_count=1 if lines else 0,
            cell_count=len(lines),
            non_empty_cell_count=len(lines),
            raw_text="\n".join(lines),
            table_grid=[[line] for line in lines],
            cells=[{"row": i, "col": 0, "text": line} for i, line in enumerate(lines)],
            warnings=[],
        )


class PaddleOCRRecognizer(TableImageRecognizer):
    def __init__(self) -> None:
        super().__init__(name="paddleocr", version="1.0")
        self._available = False
        self._engine = None
        try:
            from paddleocr import PaddleOCR  # type: ignore

            self._available = True
            self._engine = PaddleOCR
        except Exception:
            self._available = False
            self._engine = None

    def is_available(self) -> bool:
        return self._available

    def recognize(self, image_path: str, table_asset_id: str, source_doc_name: str, table_role_guess: str) -> ExtractedTable:
        # no model auto-download policy: do not instantiate engine automatically
        return ExtractedTable(
            extracted_table_id=f"{table_asset_id}__paddleocr",
            table_asset_id=table_asset_id,
            source_doc_name=source_doc_name,
            table_role_guess=table_role_guess,
            image_path=image_path,
            recognizer_name=self.name,
            recognizer_version=self.version,
            recognition_status="RECOGNIZER_UNAVAILABLE",
            row_count=0,
            col_count=0,
            cell_count=0,
            non_empty_cell_count=0,
            raw_text="",
            table_grid=[],
            cells=[],
            warnings=["BLOCKED_RECOGNIZER_MODEL_MISSING or init disabled by policy"],
        )


def build_recognizer(mode: str) -> TableImageRecognizer:
    m = (mode or "auto").strip().lower()
    if m == "none":
        return NoneRecognizer()
    if m == "ocr_text_only":
        return OCRTextOnlyRecognizer()
    if m == "paddleocr":
        return PaddleOCRRecognizer()

    # auto: prioritize ocr_text_only if already available, else paddle package presence, else none
    o = OCRTextOnlyRecognizer()
    if o.is_available():
        return o
    p = PaddleOCRRecognizer()
    if p.is_available():
        return p
    return NoneRecognizer()

