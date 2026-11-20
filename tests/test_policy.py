import pytest
from feasibility.policy import Principal, Denied, authorize

@pytest.mark.parametrize("tenant,resource,action,approved,allowed", [
    ("tenant-a","tenant-a","read_measurement",True,True),
    ("tenant-a","tenant-b","read_measurement",True,False),
    ("tenant-a","tenant-a","delete_device",True,False),
    ("tenant-a","tenant-a","read_measurement",False,False),
    ("","tenant-a","read_measurement",True,False),
])
def test_policy(tenant, resource, action, approved, allowed):
    p = Principal("demo-user",tenant,frozenset({"read_measurement"}))
    if allowed:
        assert authorize(p, resource_tenant=resource, action=action, approved=approved) is None
    else:
        with pytest.raises(Denied):authorize(p, resource_tenant=resource, action=action, approved=approved)

def test_no_permission():
    with pytest.raises(Denied):
        authorize(Principal('test','a',frozenset()),resource_tenant='a',action='read_measurement',approved=True)
