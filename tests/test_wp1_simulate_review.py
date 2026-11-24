import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('simulator',Path(__file__).parents[1]/'scripts/wp1_simulate_review.py')
sim=importlib.util.module_from_spec(spec);spec.loader.exec_module(sim)

def test_synthetic_scenarios():
    cases=sim.scenarios()
    assert len(cases)>=7 and all(v['passed'] for v in cases.values())
    assert cases['missing_approval']['decision']=='BLOCKED'
    assert cases['synthetic_happy_path']['decision']=='READY_FOR_AUTHORIZED_MERGE'
