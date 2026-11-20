"""WP0 fixture only: no OIDC, distributed audit, external tools or production readiness."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .policy import Principal, authorize, Denied

app = FastAPI(title="Enterprise AI feasibility reference", version="0.1.0")

class DemoRequest(BaseModel):
    subject: str = Field(min_length=1)
    tenant: str = Field(min_length=1)
    resource_tenant: str = Field(min_length=1)
    action: str
    approved: bool = False

@app.get("/livez")
def livez():
    return {"status":"alive"}

@app.get("/readyz")
def readyz():
    # WP0 only; future WP1 must incorporate actual dependency readiness.
    return {"status":"fixture-ready", "scope":"process-only"}

@app.post("/demo/governed-read")
def governed_read(request: DemoRequest):
    # Explicitly synthetic identity context supplied in JSON. NOT a trusted auth input.
    principal = Principal(request.subject, request.tenant, frozenset({"read_measurement"}))
    try:
        authorize(principal, resource_tenant=request.resource_tenant,
                  action=request.action, approved=request.approved)
    except Denied:
        # No caller-provided tenant information in deny detail.
        raise HTTPException(status_code=403, detail="denied by demonstration policy")
    return {"result":"synthetic-measurement", "scope":"not-authenticated"}
