import os
os.environ["DB_PATH"]="/tmp/test-reviewer.db"
from fastapi.testclient import TestClient
from app.main import app
from app.core.preprocessing import validate_source, ValidationError
from app.core.static_analyzer import analyze

def test_validation():
    assert validate_source("x.py","print('x')").language=="python"
    try: validate_source("x.exe","x")
    except ValidationError: pass
    else: assert False

def test_static_findings():
    u=validate_source("x.py","value = eval(input())\ntry:\n pass\nexcept:\n pass\n")
    findings,_=analyze(u); rules={f["rule_id"] for f in findings}
    assert "PY-EVAL" in rules and "PY-BARE-EXCEPT" in rules

def test_api_flow():
    client=TestClient(app)
    r=client.post("/api/reviews",json={"filename":"demo.py","project":"Test","version":"1","code":"x = eval(input())"})
    assert r.status_code==200
    rid=r.json()["review_id"]
    assert client.get(f"/api/reviews/{rid}").status_code==200
    assert client.get(f"/api/reviews/{rid}/report/json").status_code==200
    fid=r.json()["findings"][0]["id"]
    assert client.patch(f"/api/reviews/{rid}/findings/{fid}",json={"status":"Fixed"}).status_code==200
