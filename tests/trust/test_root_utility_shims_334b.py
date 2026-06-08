import importlib


def test_artifact_names_root_and_package_exports_match():
    root_mod = importlib.import_module("artifact_names")
    pkg_mod = importlib.import_module("datefac.utils.artifact_names")

    assert root_mod.ARTIFACT_MARKDOWN == pkg_mod.ARTIFACT_MARKDOWN
    assert root_mod.ARTIFACT_RAW_TABLES == pkg_mod.ARTIFACT_RAW_TABLES
    assert root_mod.ARTIFACT_BATCH_STATUS == pkg_mod.ARTIFACT_BATCH_STATUS


def test_logger_utils_root_and_package_exports_match():
    root_mod = importlib.import_module("logger_utils")
    pkg_mod = importlib.import_module("datefac.utils.logger_utils")

    assert callable(root_mod.setup_logging)
    assert callable(pkg_mod.setup_logging)
    assert root_mod.setup_logging is pkg_mod.setup_logging


def test_run_state_root_and_package_exports_match():
    root_mod = importlib.import_module("run_state")
    pkg_mod = importlib.import_module("datefac.utils.run_state")

    assert root_mod.DocumentRunState is pkg_mod.DocumentRunState

    instance = root_mod.DocumentRunState(
        doc_name="demo.pdf",
        pdf_path="D:/demo.pdf",
        asset_package_path="D:/pkg",
        markdown_cache_path="D:/cache/demo.txt",
    )
    assert instance.status == "PENDING"
    assert instance.table_count == 0


def test_from_import_compatibility():
    from artifact_names import ARTIFACT_SEGMENT_MAP
    from logger_utils import setup_logging
    from run_state import DocumentRunState

    from datefac.utils.artifact_names import ARTIFACT_SEGMENT_MAP as pkg_segment_map
    from datefac.utils.logger_utils import setup_logging as pkg_setup_logging
    from datefac.utils.run_state import DocumentRunState as pkg_run_state

    assert ARTIFACT_SEGMENT_MAP == pkg_segment_map
    assert setup_logging is pkg_setup_logging
    assert DocumentRunState is pkg_run_state
