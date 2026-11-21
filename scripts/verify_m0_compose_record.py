#!/usr/bin/env python3
"""Verify immutable M0 Compose evidence without freezing later WP states.

--require-evidence: fail if a historical local M0 evidence directory is absent.
This verifier MUST NOT require WP1 to remain NOT_RUN after WP1 research begins.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys


def verify(root: Path, require_evidence: bool = False) -> None:
    record = json.loads((root / "qualification/m0-compose-local.json").read_text())
    status = json.loads((root / "qualification/status.json").read_text())
    if record.get("schema") != "ai-enterprise-m0-compose-local-v1":
        raise ValueError("M0 record schema mismatch")
    if record.get("overall") != "PASS" or record.get("production_authorized") is not False:
        raise ValueError("M0 record not accepted locally or production boundary changed")
    # Preserve historical facts. This is the WP1 state AT the M0 execution, not NOW.
    if record.get("wp1_status") != "NOT_RUN":
        raise ValueError("historical WP1 state in M0 record was changed")
    if status.get("production_authorized") is not False:
        raise ValueError("production authorization must remain denied")
    packages = [p for p in status.get("work_packages", []) if p.get("id") == "WP1"]
    if len(packages) != 1 or packages[0].get("status") not in ("planned", "in_progress", "accepted"):
        raise ValueError("WP1 current status malformed")
    runs = record.get("runs", [])
    if not runs or not isinstance(runs, list):
        raise ValueError("missing M0 runs")
    missing = []
    for e in runs:
        if e.get("result") != "PASS":
            raise ValueError("historical M0 run not PASS")
        rel = Path(e["evidence_bundle_local_path"])
        if rel.is_absolute() or ".." in rel.parts or rel.parts[:2] != ("reports", "validation"):
            raise ValueError("invalid M0 local evidence path")
        directory = root / rel
        if not directory.is_dir():
            missing.append(e["id"])
            print(f"Evidence {e['id']}: NOT_PRESENT (not a PASS)")
            continue
        manifest = directory / "SHA256SUMS"
        if not manifest.is_file():
            raise ValueError(f"missing SHA256SUMS for {e['id']}")
        actual_digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        if actual_digest != e["evidence_manifest_sha256"]:
            raise ValueError(f"M0 manifest digest mismatch: {e['id']}")
        proc = subprocess.run(["sha256sum", "--check", "--status", "SHA256SUMS"], cwd=directory)
        if proc.returncode != 0:
            raise ValueError(f"M0 evidence checksum failure: {e['id']}")
        print(f"Evidence {e['id']}: PASS (SHA256 verified)")
    if missing and require_evidence:
        raise ValueError("required M0 evidence missing: " + ", ".join(missing))
    print("M0 Compose record: PASS; evidence: " + ("NOT_PRESENT" if missing else "PASS") +
          "; historical WP1=NOT_RUN; current WP1=" + packages[0]["status"] +
          "; production denied")


if __name__ == "__main__":
    try:
        verify(Path(__file__).resolve().parents[1], "--require-evidence" in sys.argv)
    except (ValueError, KeyError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
