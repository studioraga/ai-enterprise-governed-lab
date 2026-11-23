# WP1 local laboratory evidence index

## Source

Research baseline:
d9c80c264a9b6ce7e4767fed58b009f56b0d91e7

Network probe SHA256:
3666263ae78d52f41bb7392eeb188d53b54f1d29054fdfb66ebfbd28a229fb68

## Original differential-test evidence

Local directory:
reports/validation/wp1-network-v5.3-20261121T052723Z/

SHA256SUMS digest:
5a779eff4429a056855621b7946d797fdad09719da099c8fffd041b21a23695c

Five tested paths:
3 allowed HTTP controls; 2 expected timeouts.

## Operational results

- Initial kind deployment: verified
- Missing-image failure: verified
- Reboot recovery: verified
- Helm rollback: verified
- Synthetic HTTP 200/200/403/200: verified
- RBAC secret listing and Deployment creation: denied

## Explicit limitations

- Raw local reports are not committed.
- Historical kubeconfig material is excluded.
- No enterprise authentication or managed Secret lifecycle.
- Single-node laboratory only.
- Independent acceptance pending.
- Production authorization denied.
