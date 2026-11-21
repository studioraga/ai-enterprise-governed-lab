"""Regression: historical M0 record must survive WP1 progress, fail closed on acceptance."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m0_verifier", ROOT / "scripts/verify_m0_compose_record.py")
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def write_state(tmp_path, status_transform=None, history_transform=None):
    q = tmp_path / "qualification"
    q.mkdir()
    current = json.loads((ROOT / "qualification/status.json").read_text())
    historic = json.loads((ROOT / "qualification/m0-compose-local.json").read_text())
    if status_transform:
        status_transform(current)
    if history_transform:
        history_transform(historic)
    (q / "status.json").write_text(json.dumps(current))
    (q / "m0-compose-local.json").write_text(json.dumps(historic))


def test_m0_verifier_permits_wp1_in_progress(tmp_path):
    write_state(tmp_path)
    verifier.verify(tmp_path)


def test_m0_verifier_does_not_freeze_future_wp1_acceptance(tmp_path):
    write_state(tmp_path, lambda s: s["work_packages"][0].update(status="accepted"))
    verifier.verify(tmp_path)


def test_m0_verifier_rejects_invalid_wp1_status(tmp_path):
    write_state(tmp_path, lambda s: s["work_packages"][0].update(status="unrecognized"))
    with pytest.raises(ValueError, match="malformed"):
        verifier.verify(tmp_path)


def test_m0_verifier_rejects_production_authorized(tmp_path):
    write_state(tmp_path, lambda s: s.update(production_authorized=True))
    with pytest.raises(ValueError, match="denied"):
        verifier.verify(tmp_path)


def test_m0_verifier_protects_historical_state(tmp_path):
    write_state(tmp_path, history_transform=lambda s: s.update(wp1_status="in_progress"))
    with pytest.raises(ValueError, match="historical"):
        verifier.verify(tmp_path)


def test_m0_verifier_requires_local_evidence_when_requested(tmp_path):
    write_state(tmp_path)
    with pytest.raises(ValueError, match="required M0 evidence missing"):
        verifier.verify(tmp_path, require_evidence=True)
