import os
from datetime import datetime
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path(r"D:\_datefac\output")
REPORT_PATH = OUTPUT_DIR / "14_invalid_output_paths_report.xlsx"
WINDOWS_ILLEGAL_CHARS = set('<>:"/\\|?*')
MOJIBAKE_TOKENS = ["鎶", "缁", "鏂", "鍒", "涓", "绮", "惧", "崕", "璧", "產", "�"]


def has_control_chars(text: str) -> bool:
    return any(ord(ch) < 32 for ch in text)


def has_windows_illegal_chars(text: str) -> bool:
    return any(ch in WINDOWS_ILLEGAL_CHARS for ch in text)


def suspicious_mojibake(text: str) -> bool:
    return any(token in text for token in MOJIBAKE_TOKENS)


def recommendation(row: dict) -> str:
    if row["has_control_chars"]:
        return "remove_control_chars"
    if row["has_windows_illegal_chars"]:
        return "sanitize_windows_filename"
    if row["suspicious_mojibake"]:
        return "check_artifact_name_encoding"
    return "ok"


def safe_report_path(path: Path) -> Path:
    final = path
    if final.exists():
        try:
            with open(final, "a"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%H%M%S")
            final = final.with_name(f"{final.stem}_副本_{ts}{final.suffix}")
    return final


def main():
    rows = []
    if not OUTPUT_DIR.exists():
        print(f"output_dir_not_found={OUTPUT_DIR}")
        return

    for root, _, files in os.walk(OUTPUT_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            row = {
                "path": full_path,
                "filename": f,
                "has_control_chars": has_control_chars(f),
                "has_windows_illegal_chars": has_windows_illegal_chars(f),
                "suspicious_mojibake": suspicious_mojibake(f),
                "length": len(f),
            }
            row["recommendation"] = recommendation(row)
            rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(
            columns=[
                "path",
                "filename",
                "has_control_chars",
                "has_windows_illegal_chars",
                "suspicious_mojibake",
                "length",
                "recommendation",
            ]
        )
    else:
        df = df.sort_values(
            by=["suspicious_mojibake", "has_windows_illegal_chars", "has_control_chars", "path"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)

    report = safe_report_path(REPORT_PATH)
    with pd.ExcelWriter(report, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="summary", index=False)
    print(f"report_path={report}")
    print(f"row_count={len(df)}")
    flagged = df[
        (df["has_control_chars"] == True)
        | (df["has_windows_illegal_chars"] == True)
        | (df["suspicious_mojibake"] == True)
    ]
    print(f"flagged_count={len(flagged)}")


if __name__ == "__main__":
    main()
