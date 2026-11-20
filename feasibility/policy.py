"""Minimal demonstrable default-deny policy; not an imported M30 production policy."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str
    permissions: frozenset[str]

class Denied(PermissionError):
    pass

def authorize(principal: Principal, *, resource_tenant: str, action: str, approved: bool) -> None:
    if not principal.subject or not principal.tenant:
        raise Denied("missing verified identity context")
    if principal.tenant != resource_tenant:
        raise Denied("cross-tenant action denied")
    if action not in principal.permissions or action != "read_measurement":
        raise Denied("action not permitted")
    if not approved:
        raise Denied("approval missing")
