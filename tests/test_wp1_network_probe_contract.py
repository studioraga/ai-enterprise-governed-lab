"""Static fail-closed expectations for differential WP1 NetworkPolicy probe."""
from pathlib import Path


def test_probe_contains_positive_controls_and_specific_timeouts():
    src = (Path(__file__).resolve().parents[1] / 'scripts/wp1_networkpolicy_probe.sh').read_text()
    assert "other namespace to unprotected control receiver" in src
    assert "same namespace to protected Pod" in src
    assert "same namespace to unprotected control receiver" in src
    assert "[[ \"$rc\" != 28 ]]" in src
    assert 'except socket.timeout:' in src
    assert 'UNEXPECTED_ERROR:' in src
    assert 'UNEXPECTED_CONNECTION_SUCCEEDED' in src
    assert 'kubectl --context' in src
    assert 'delete namespace' in src
    assert 'kind delete cluster' not in src
    assert 'docker system prune' not in src


def test_receiver_has_explicit_readiness_and_no_privileged_token():
    src = (Path(__file__).resolve().parents[1] / 'scripts/wp1_networkpolicy_probe.sh').read_text()
    assert 'name: wp1-control-receiver' in src
    assert 'readinessProbe:' in src
    assert 'startupProbe:' in src
    assert 'automountServiceAccountToken: false' in src
    assert 'app: wp1-control-receiver' in src
    assert 'http://127.0.0.1:8000/livez' in src
    assert 'imagePullPolicy: IfNotPresent' in src
    assert 'readOnlyRootFilesystem: true' in src
    assert 'drop: [ALL]' in src
