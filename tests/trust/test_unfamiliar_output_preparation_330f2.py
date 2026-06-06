from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.unfamiliar_output_preparation_330f2 import (  # noqa: E402
    WAITING_FOR_PARSER_OUTPUTS,
    WAITING_FOR_UNFAMILIAR_INPUTS,
    discover_matching_cached_outputs,
    discover_unfamiliar_inputs,
)


def test_discover_matching_cached_outputs_returns_empty_without_matches(tmp_path: Path) -> None:
    input_df = pd.DataFrame(
        [
            {
                "pdf_name": "demo.pdf",
                "pdf_stem": "demo",
                "full_path": str(tmp_path / "demo.pdf"),
                "size_bytes": 10,
            }
        ]
    )
    output_root = tmp_path / "output"
    output_root.mkdir()

    result = discover_matching_cached_outputs(input_df, output_root)

    assert result.empty


def test_discover_unfamiliar_inputs_collects_pdf_files(tmp_path: Path) -> None:
    (tmp_path / "a.pdf").write_bytes(b"x")
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")

    result = discover_unfamiliar_inputs(tmp_path)

    assert list(result["pdf_name"]) == ["a.pdf"]


def test_waiting_status_selection_logic() -> None:
    assert WAITING_FOR_UNFAMILIAR_INPUTS == "WAITING_FOR_UNFAMILIAR_INPUTS"
    assert WAITING_FOR_PARSER_OUTPUTS == "WAITING_FOR_PARSER_OUTPUTS"
