# AI Enterprise Labs interview narrative and demonstration checklist

## Interview pitch (90 seconds)

> I specialize in establishing whether technically difficult integrations can run inside constrained customer platforms. My embedded Linux, Qualcomm, automotive, IoT and AI development experience makes me comfortable debugging across firmware, OS, networking, APIs and accelerated inference. In two research repositories I developed API-contract analysis, agent authorization controls, tenant-isolation experiments and evidence-based governance. This new project is a separate integration baseline to demonstrate the missing operational pieces: Kubernetes, observability, authenticated enterprise identity, controlled cloud, end-to-end data governance and CI/CD. I distinguish prototype tests from production approval and make failed security gates visible rather than bypassing them.

## Ten-minute scenario demo (planned, not completed)

1. **00:00–01:00:** Client asks whether an AI diagnostic service can run in a restricted Kubernetes environment; state constraints and success criteria.
2. **01:00–02:30:** Show Git source locks, ADRs, dependency inventory, deployment chart and OpenAPI compatibility evidence.
3. **02:30–04:00:** Deploy container, demonstrate readiness, traces and a successful request with trusted IdP token.
4. **04:00–06:00:** Attempt forged-tenant request / unauthorized tool action; prove no side effect, audit denial and unchanged data.
5. **06:00–07:30:** Break Redis/Qdrant or deploy bad image; isolate with traces and rollback safely.
6. **07:30–09:00:** Show M30-style independent evidence decision: a valid signature does not override an incomplete physical/security control.
7. **09:00–10:00:** Report go/conditional-go/no-go with evidence and reusable client playbook.

**Current executable M0 alternative:** show `pytest`, `GET /livez`, synthetic allow and deny; explicitly identify missing real identity, tools, K8s and observability. Do not pretend planned steps have been executed.

## Questions to rehearse

- What made the environment uncertain? What single experiment would falsify your proposed approach quickest?
- Explain why a signed evidence receipt cannot authorize deployment when secure boot/MAC or authorized pentest evidence is missing.
- Demonstrate how a forged tenant parameter can bypass a weak database session variable, and how you contain it.
- Why is Redis `SET NX PX` not exactly-once execution?
- Trace an API request across ingress, identity, policy, SQL, vector store and bounded tool; what correlation metadata is safe to retain?
- Explain the difference between research branch acceptance, reproducible lab validation, independent verification and production authorization.

## Evidence pack required before claiming each skill

| Claim | Minimum defensible evidence |
|---|---|
| Kubernetes deployment | real `kubectl` output, rollouts, probes, rollback and logs |
| Observability | trace+metrics correlation and one induced incident |
| OIDC | valid and malicious token tests with real issuer/JWKS |
| Enterprise cloud | named approved platform, IAM/network topology, plan/apply/destroy evidence |
| Governance | policy and tenant negative tests, independent evidence and failed gate |
| CI/CD | immutable build artifacts, required status checks, staged approval and rollback |
