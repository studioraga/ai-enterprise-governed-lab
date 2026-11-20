from fastapi.testclient import TestClient
from feasibility.app import app

client=TestClient(app)
def test_liveness(): assert client.get('/livez').json()=={'status':'alive'}
def test_readiness_not_claimed(): assert client.get('/readyz').json()['scope']=='process-only'
def test_denied():
    req={'subject':'demo-user','tenant':'a','resource_tenant':'b','action':'read_measurement','approved':True}
    assert client.post('/demo/governed-read',json=req).status_code==403
def test_allowed_synthetic_only():
    req={'subject':'demo-user','tenant':'a','resource_tenant':'a','action':'read_measurement','approved':True}
    response=client.post('/demo/governed-read',json=req)
    assert response.status_code==200
    assert response.json()['scope']=='not-authenticated'
