import logging

import pandas as pd

from pdfplumber_table_extractor import (
    build_table_index_dataframe,
    extract_tables_from_pdf,
    table_blocks_to_dfs,
)


def test_table_blocks_to_dfs_returns_dataframes():
    block1 = {
        "backend": "pdfplumber",
        "page": 1,
        "table_index": 1,
        "df": pd.DataFrame([["a", "1"], ["b", "2"]], columns=["item", "v"]),
        "rows": 2,
        "cols": 2,
        "preview": "a | 1",
        "confidence": 0.8,
    }
    block2 = {
        "backend": "pdfplumber",
        "page": 2,
        "table_index": 1,
        "df": pd.DataFrame([["x"]], columns=["k"]),
        "rows": 1,
        "cols": 1,
        "preview": "x",
        "confidence": 0.8,
    }
    dfs = table_blocks_to_dfs([block1, block2])
    assert len(dfs) == 2
    assert isinstance(dfs[0], pd.DataFrame)
    assert dfs[0].shape == (2, 2)


def test_build_table_index_dataframe_fields():
    blocks = [
        {
            "backend": "pdfplumber",
            "page": 1,
            "table_index": 1,
            "rows": 10,
            "cols": 5,
            "preview": "row1",
            "confidence": 0.8,
        }
    ]
    index_df = build_table_index_dataframe(blocks, ["p1_t1"])
    expected_cols = ["sheet_name", "backend", "page", "table_index", "rows", "cols", "preview", "confidence"]
    assert list(index_df.columns) == expected_cols
    assert index_df.iloc[0]["sheet_name"] == "p1_t1"
    assert index_df.iloc[0]["backend"] == "pdfplumber"


def test_extract_tables_pdfplumber_unavailable_or_invalid_pdf_no_hard_exception():
    logger = logging.getLogger("test_pdfplumber_table_extractor")
    result = extract_tables_from_pdf("D:/_datefac/input/not_exists.pdf", pages="all", logger=logger, config={})
    assert isinstance(result, list)


def test_extract_tables_filters_empty_tables_with_stub_pdfplumber(monkeypatch):
    class FakePage:
        def __init__(self, tables):
            self._tables = tables

        def extract_tables(self):
            return self._tables

    class FakePdfCtx:
        def __init__(self, pages):
            self.pages = pages

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakePdfPlumber:
        @staticmethod
        def open(_path):
            # first table all empty -> filtered, second keeps one row
            pages = [
                FakePage(
                    [
                        [["", ""], ["", ""]],
                        [["item", "v"], ["rev", "100"]],
                    ]
                )
            ]
            return FakePdfCtx(pages)

    import sys

    monkeypatch.setitem(sys.modules, "pdfplumber", FakePdfPlumber)
    rows = extract_tables_from_pdf("fake.pdf", pages="all", logger=None, config={})
    assert len(rows) == 1
    assert rows[0]["rows"] >= 1
    assert rows[0]["cols"] >= 1
