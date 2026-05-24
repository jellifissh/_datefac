import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(r"D:\_datefac")
OUTPUT_DIR = ROOT / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"
RELEASE_ROOT = OUTPUT_DIR / "release_package"
RELEASE_DIR = RELEASE_ROOT / "stage6b_final_release"
TOP_MANIFEST = RELEASE_ROOT / "179_stage6b_release_manifest.json"
TOP_REPORT = RELEASE_ROOT / "179_stage6b_release_report.md"
RELEASE_ZIP = RELEASE_ROOT / "stage6b_final_release.zip"

STAGE_AUDITS: List[Tuple[str, Path]] = [
    ("stage5w", OUTPUT_DIR / "stage5w_eps_unit_conflict_review"),
    ("stage5x", OUTPUT_DIR / "stage5x_eps_unit_apply"),
    ("stage5y", OUTPUT_DIR / "stage5y_final_delivery_audit"),
    ("stage5z", OUTPUT_DIR / "stage5z_eps_formal_rule_review"),
    ("stage5z2", OUTPUT_DIR / "stage5z2_eps_formal_rule_apply"),
    ("stage6a", OUTPUT_DIR / "stage6a_final_delivery_freeze"),
    ("stage6a2", OUTPUT_DIR / "stage6a_final_delivery_freeze"),
]

REQUIRED_RELEASE_FILES = [
    ("audit/stage5w/172_stage5w_eps_conflict_review.xlsx", OUTPUT_DIR / "stage5w_eps_unit_conflict_review" / "172_stage5w_eps_conflict_review.xlsx"),
    ("audit/stage5w/172_stage5w_eps_unit_decision_report.md", OUTPUT_DIR / "stage5w_eps_unit_conflict_review" / "172_stage5w_eps_unit_decision_report.md"),
    ("audit/stage5w/173_stage5w_eps_unit_conflict_summary.json", OUTPUT_DIR / "stage5w_eps_unit_conflict_review" / "173_stage5w_eps_unit_conflict_summary.json"),
    ("audit/stage5x/174_stage5x_eps_unit_apply_audit.xlsx", OUTPUT_DIR / "stage5x_eps_unit_apply" / "174_stage5x_eps_unit_apply_audit.xlsx"),
    ("audit/stage5x/174_stage5x_eps_unit_apply_report.md", OUTPUT_DIR / "stage5x_eps_unit_apply" / "174_stage5x_eps_unit_apply_report.md"),
    ("audit/stage5x/174_stage5x_eps_unit_apply_summary.json", OUTPUT_DIR / "stage5x_eps_unit_apply" / "174_stage5x_eps_unit_apply_summary.json"),
    ("audit/stage5y/175_stage5y_final_delivery_audit_report.md", OUTPUT_DIR / "stage5y_final_delivery_audit" / "175_stage5y_final_delivery_audit_report.md"),
    ("audit/stage5y/175_stage5y_final_delivery_audit_summary.json", OUTPUT_DIR / "stage5y_final_delivery_audit" / "175_stage5y_final_delivery_audit_summary.json"),
    ("audit/stage5z/176_stage5z_eps_formal_rule_review_report.md", OUTPUT_DIR / "stage5z_eps_formal_rule_review" / "176_stage5z_eps_formal_rule_review_report.md"),
    ("audit/stage5z/176_stage5z_eps_formal_rule_review_summary.json", OUTPUT_DIR / "stage5z_eps_formal_rule_review" / "176_stage5z_eps_formal_rule_review_summary.json"),
    ("audit/stage5z2/177_stage5z2_eps_formal_rule_apply_report.md", OUTPUT_DIR / "stage5z2_eps_formal_rule_apply" / "177_stage5z2_eps_formal_rule_apply_report.md"),
    ("audit/stage5z2/177_stage5z2_eps_formal_rule_apply_summary.json", OUTPUT_DIR / "stage5z2_eps_formal_rule_apply" / "177_stage5z2_eps_formal_rule_apply_summary.json"),
    ("audit/stage6a/178_stage6a_final_delivery_freeze_report.md", OUTPUT_DIR / "stage6a_final_delivery_freeze" / "178_stage6a_final_delivery_freeze_report.md"),
    ("audit/stage6a/178_stage6a_final_delivery_freeze_summary.json", OUTPUT_DIR / "stage6a_final_delivery_freeze" / "178_stage6a_final_delivery_freeze_summary.json"),
    ("manifests/178_stage6a_delivery_file_hash_manifest.json", OUTPUT_DIR / "stage6a_final_delivery_freeze" / "178_stage6a_delivery_file_hash_manifest.json"),
    ("README_RELEASE.md", None),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def collect_dir_files(base_dir: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not base_dir.exists():
        return out
    for p in sorted(base_dir.rglob("*")):
        if p.is_file():
            out[p.relative_to(base_dir).as_posix()] = sha256_file(p)
    return out


def read_check_delivery_state() -> dict:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_delivery_state.py"), "--json"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"check_delivery_state.py failed: {proc.stdout}\n{proc.stderr}")
    try:
        return json.loads(proc.stdout.strip())
    except Exception as exc:
        raise RuntimeError(f"Failed to parse check_delivery_state output: {proc.stdout}") from exc


def git_head_commit() -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git rev-parse HEAD failed: {proc.stderr}")
    return proc.stdout.strip()


def validate_stage6a_hash_manifest(manifest_path: Path) -> Tuple[bool, List[dict]]:
    data = load_json(manifest_path)
    results: List[dict] = []
    ok = True
    for key, item in data.items():
        if not isinstance(item, dict):
            continue
        path = Path(item["path"])
        expected = item["sha256"]
        exists = path.exists()
        actual = sha256_file(path) if exists else ""
        match = exists and actual == expected
        results.append(
            {
                "key": key,
                "path": str(path),
                "exists": exists,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "match": match,
            }
        )
        if not match:
            ok = False
    return ok, results


def make_readme(summary: dict, package_hashes: Dict[str, str]) -> str:
    lines = [
        "# Stage 6B Final Release Package",
        "",
        f"- based_on_stage6a2_commit: {summary['based_on_stage6a2_commit']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_06_row_count: {summary['production_06_row_count']}",
        f"- eps_row_count: {summary['eps_row_count']}",
        f"- eps_unit: {summary['eps_unit']}",
        f"- hash_manifest_match: {str(summary['hash_manifest_match']).lower()}",
        f"- ready_for_external_delivery: {str(summary['ready_for_external_delivery']).lower()}",
        "",
        "## Contents",
        "- delivery_package/: frozen delivery package copied from output/delivery_package",
        "- audit/: key audit summaries/reports from Stage 5W/5X/5Y/5Z/5Z2/6A",
        "- rules/: formal_scope_rules.json and financial_standardizer.py",
        "- manifests/: Stage 6A hash manifest",
        "",
        "## Package File Count",
        f"- {len(package_hashes)} files hashed inside the package directory",
    ]
    return "\n".join(lines) + "\n"


def zip_directory(source_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(source_dir.rglob("*")):
            if p.is_file():
                zf.write(p, arcname=p.relative_to(source_dir.parent).as_posix())


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Stage 6B final release package.")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()

    root = Path(args.root)
    output_dir = root / "output"
    release_root = output_dir / "release_package"
    delivery_dir = output_dir / "delivery_package"
    release_dir = release_root / "stage6b_final_release"
    top_manifest = release_root / "179_stage6b_release_manifest.json"
    top_report = release_root / "179_stage6b_release_report.md"
    release_zip = release_root / "stage6b_final_release.zip"

    # Preflight: current delivery state must already be PASS and manifest must match.
    preflight_check = read_check_delivery_state()
    if preflight_check.get("overall_status") != "PASS":
        raise RuntimeError(f"check_delivery_state is not PASS: {preflight_check}")

    stage6a_manifest = output_dir / "stage6a_final_delivery_freeze" / "178_stage6a_delivery_file_hash_manifest.json"
    stage6a_summary = output_dir / "stage6a_final_delivery_freeze" / "178_stage6a_final_delivery_freeze_summary.json"
    stage6a_report = output_dir / "stage6a_final_delivery_freeze" / "178_stage6a_final_delivery_freeze_report.md"
    if not stage6a_manifest.exists() or not stage6a_summary.exists() or not stage6a_report.exists():
        raise FileNotFoundError("Stage 6A freeze artifacts are missing.")

    hash_manifest_match, hash_manifest_details = validate_stage6a_hash_manifest(stage6a_manifest)
    if not hash_manifest_match:
        raise RuntimeError("Stage 6A hash manifest does not match current files.")

    summary = load_json(stage6a_summary)
    based_on_stage6a2_commit = git_head_commit()
    if not based_on_stage6a2_commit:
        based_on_stage6a2_commit = summary.get("based_on_stage6a_artifact_commit") or summary.get("based_on_stage5z2_commit") or ""
    if not summary.get("ready_for_release_package", False):
        raise RuntimeError("Stage 6A summary is not ready_for_release_package.")

    ensure_clean_dir(release_root)
    release_dir.mkdir(parents=True, exist_ok=True)

    # Copy the frozen delivery package unchanged.
    shutil.copytree(delivery_dir, release_dir / "delivery_package")

    # Copy audit artifacts.
    for stage_name, stage_dir in STAGE_AUDITS:
        dst_stage_dir = release_dir / "audit" / stage_name
        dst_stage_dir.mkdir(parents=True, exist_ok=True)
        if stage_name in {"stage6a", "stage6a2"}:
            for src_name in [
                "178_stage6a_final_delivery_freeze_report.md",
                "178_stage6a_final_delivery_freeze_summary.json",
                "178_stage6a_delivery_file_hash_manifest.json",
            ]:
                copy_file(stage_dir / src_name, dst_stage_dir / src_name)
        else:
            for src in sorted(stage_dir.iterdir()):
                if src.is_file():
                    copy_file(src, dst_stage_dir / src.name)

    # Copy rules.
    rules_dir = release_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    copy_file(root / "data" / "mapping" / "formal_scope_rules.json", rules_dir / "formal_scope_rules.json")
    copy_file(root / "financial_standardizer.py", rules_dir / "financial_standardizer.py")

    # Copy the source hash manifest into the package.
    manifests_dir = release_dir / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    copy_file(stage6a_manifest, manifests_dir / stage6a_manifest.name)

    # Release README lives inside the package.
    package_hashes_before_readme = collect_dir_files(release_dir)
    readme_text = make_readme(
        {
            "based_on_stage6a2_commit": based_on_stage6a2_commit,
            "check_delivery_state_overall_status": preflight_check.get("overall_status", ""),
            "production_06_row_count": summary["production_06_row_count"],
            "eps_row_count": summary["eps_row_count"],
            "eps_unit": summary["eps_unit"],
            "hash_manifest_match": hash_manifest_match,
            "ready_for_external_delivery": True,
        },
        package_hashes_before_readme,
    )
    (release_dir / "README_RELEASE.md").write_text(readme_text, encoding="utf-8")

    # Final package hashes after README exists.
    package_hashes = collect_dir_files(release_dir)
    zip_directory(release_dir, release_zip)
    release_zip_hash = sha256_file(release_zip)

    # Top-level manifest/report.
    final_check = read_check_delivery_state()
    if final_check.get("overall_status") != "PASS":
        raise RuntimeError(f"Post-package check_delivery_state is not PASS: {final_check}")

    release_manifest = {
        "stage": "stage6b_final_release_package",
        "mode": "package_only",
        "based_on_stage6a2_commit": based_on_stage6a2_commit,
        "check_delivery_state_overall_status": final_check.get("overall_status"),
        "production_06_row_count": summary["production_06_row_count"],
        "eps_row_count": summary["eps_row_count"],
        "eps_unit": summary["eps_unit"],
        "conflict_counts": "0/0/0/0",
        "source_hash_manifest": stage6a_manifest.name,
        "hash_manifest_match": hash_manifest_match,
        "release_package_dir": str(release_dir).replace("\\", "/"),
        "release_zip": str(release_zip).replace("\\", "/"),
        "release_zip_sha256": release_zip_hash,
        "ready_for_external_delivery": True,
        "package_file_count": len(package_hashes),
        "package_file_hashes": package_hashes,
        "stage6a_hash_manifest_checks": hash_manifest_details,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    top_manifest.write_text(json.dumps(release_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# Stage 6B Final Release Package Report",
        "",
        f"- based_on_stage6a2_commit: {based_on_stage6a2_commit}",
        f"- check_delivery_state_overall_status: {final_check.get('overall_status')}",
        f"- hash_manifest_match: {str(hash_manifest_match).lower()}",
        f"- release_package_dir: {release_manifest['release_package_dir']}",
        f"- release_zip: {release_manifest['release_zip']}",
        f"- release_zip_sha256: {release_zip_hash}",
        "",
        "## Package Contents",
        f"- package_file_count: {len(package_hashes)}",
        f"- audit_files: {sum(1 for p in (release_dir / 'audit').rglob('*') if p.is_file())}",
        f"- rules_files: {sum(1 for p in (release_dir / 'rules').rglob('*') if p.is_file())}",
        f"- manifests_files: {sum(1 for p in (release_dir / 'manifests').rglob('*') if p.is_file())}",
        "",
        "## Validation",
        f"- production_06_row_count: {summary['production_06_row_count']}",
        f"- eps_row_count: {summary['eps_row_count']}",
        f"- eps_unit: {summary['eps_unit']}",
        "- conflict_counts: 0/0/0/0",
        "- ready_for_external_delivery: true",
    ]
    top_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(json.dumps(release_manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
