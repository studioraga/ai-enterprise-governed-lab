"""The model's proposed action is never executable code or release authority."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('governance_executor',ROOT/'scripts/governance_executor.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_allowlisted_verify_only():
    cmd, reason=module.authorize({'milestone':'WP1','action':'verify_wp1_contract','requested_release':False})
    assert cmd[1:] == ['scripts/wp1_lab_gate.py','--root','.']
    assert reason is None


def test_arbitrary_shell_command_denied():
    _,reason=module.authorize({'milestone':'WP1','action':'kubectl delete pod all','requested_release':False})
    assert reason


def test_release_request_denied():
    _,reason=module.authorize({'milestone':'WP1','action':'verify_baseline','requested_release':True})
    assert reason


def test_extra_parameters_denied():
    _,reason=module.authorize({'milestone':'WP1','action':'verify_baseline','requested_release':False,'shell':'yes'})
    assert reason


def test_executor_reports_result_but_cannot_promote():
    got=module.execute({'milestone':'WP1','action':'verify_baseline','requested_release':False},
       runner=lambda *a,**k:SimpleNamespace(returncode=0,stdout='ok',stderr=''))
    assert got['decision']=='PASS' and got['production_authorized'] is False
