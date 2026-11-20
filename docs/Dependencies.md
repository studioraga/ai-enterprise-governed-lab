# Dependency and environment qualification

## Baseline dependencies

| Item | Reason | M0 required | Qualification |
|---|---|---|---|
| Python >=3.10 | API and policy demo | yes | `python --version`; `compileall` |
| FastAPI >=0.115,<1 and Uvicorn >=0.30,<1 | API fixture | yes, after pip install | `pytest` and HTTP smoke |
| pytest >=8,<10, httpx >=0.27,<1 | unit and API negative tests | yes, for verification | `pytest -q` |
| Git | new history and provenance | for commit/push | `git --version` |
| Docker Engine + Compose v2 | container drill | WP1 | daemon/version/compose config + startup |
| Kubernetes kind/k3s + kubectl | deployment qualification | WP1 | real cluster rollout, clean teardown |
| Helm 3+ | manifests and release/rollback | WP1 | `helm lint`, `helm template`, live rollback |
| OTel SDK/Collector, Prometheus, Grafana | traces and SLO | WP2 | exported correlated spans and metrics |
| OIDC/Keycloak or enterprise IdP | verified principal | WP3 | JWKS, hostile-token test matrix |
| Terraform with provider pins and backend | approved cloud IaC | WP4 | fmt/validate/plan/review/apply/destroy |
| AWS CLI or Azure CLI | provider-scoped lab | WP4 | authorized account and least privilege |
| PostgreSQL, Redis, Qdrant pinned versions | protected data plane | WP5 | tenant/replay/integration tests |
| Image scanner, SBOM, artifact signer | supply-chain gates | WP6 | scans, attestations, digest validation |

Use **exact, reviewed version locks** for later accepted build artifacts; the M0 Python ranges are convenience constraints, not a supply-chain lock or reproducibility guarantee. Capture `python -m pip freeze`, `docker version`, `kubectl version --client`, `helm version`, Terraform and cloud provider versions into sanitized evidence.

## Node1 / Node2 constraints

Primary development may run on Ubuntu 24.04 x86_64 (Node1). If the Jetson Orin Nano arm64 is used as a separate verification/edge target, explicitly build and test a compatible arm64 image; an x86_64-only image or local success cannot certify the Jetson target. Treat source versions as ground truth, not assumptions about what is installed on any host.

## Resource/cost controls

Estimate CPU, RAM, disk, persistent volumes and GPU requirements before cluster install. Default deployment consumes CPU only and has no GPU dependency; adding model serving requires a separate CUDA/driver/device-plugin support matrix. Cloud work is blocked until the user has confirmed account ownership, cost cap, allowed region, IAM scope and teardown authority.
