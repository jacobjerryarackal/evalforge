import pytest
from fastapi.testclient import TestClient

from src.adapters.api.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.anyio
async def test_health_check(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.anyio
async def test_datasets_endpoints(client: TestClient) -> None:
    # 1. Register a dataset via POST
    payload = {
        "dataset_id": "api-test-ds",
        "name": "API Test Dataset",
        "version": "1.0.0",
        "test_cases": [
            {
                "case_id": "tc-api-1",
                "input_query": "Find flight JFK to LAX",
                "expected_output": "Flight UA100",
            }
        ],
    }
    res = client.post("/api/datasets", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "registered"

    # 2. List datasets
    res_list = client.get("/api/datasets")
    assert res_list.status_code == 200
    data = res_list.json()
    assert len(data) >= 1
    assert any(d["dataset_id"] == "api-test-ds" for d in data)

    # 3. Get dataset details
    res_detail = client.get("/api/datasets/api-test-ds")
    assert res_detail.status_code == 200
    assert res_detail.json()["dataset_id"] == "api-test-ds"

    # 4. Get specific version
    res_ver = client.get("/api/datasets/api-test-ds/versions/1.0.0")
    assert res_ver.status_code == 200
    assert res_ver.json()["version"] == "1.0.0"


@pytest.mark.anyio
async def test_experiments_endpoints(client: TestClient) -> None:
    # 1. Create an experiment
    payload = {
        "experiment_id": "api-test-exp",
        "name": "API Experiment",
        "description": "Test via REST API",
    }
    res = client.post("/api/experiments", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "created"

    # 2. List experiments
    res_list = client.get("/api/experiments")
    assert res_list.status_code == 200
    data = res_list.json()
    assert any(e["experiment_id"] == "api-test-exp" for e in data)

    # 3. Get experiment details (empty runs initially)
    res_detail = client.get("/api/experiments/api-test-exp")
    assert res_detail.status_code == 200
    assert res_detail.json()["experiment_id"] == "api-test-exp"
    assert len(res_detail.json()["runs"]) == 0


@pytest.mark.anyio
async def test_benchmark_execution_and_run_history(client: TestClient) -> None:
    # First, make sure the dataset is registered in the repo
    payload = {
        "dataset_id": "api-exec-ds",
        "name": "API Execution Dataset",
        "version": "1.0.0",
        "test_cases": [
            {
                "case_id": "tc-exec-1",
                "input_query": "Convert USD to EUR",
                "expected_output": "0.92",
            }
        ],
    }
    client.post("/api/datasets", json=payload)

    # Trigger async benchmark run
    run_payload = {
        "dataset_id": "api-exec-ds",
        "version": "1.0.0",
        "sut_name": "travel_agent",
        "run_id": "run-api-exec-1",
    }
    res = client.post("/api/benchmarks/run", json=run_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "running"
    assert res.json()["run_id"] == "run-api-exec-1"

    res_runs = client.get("/api/runs")
    assert res_runs.status_code == 200


@pytest.mark.anyio
async def test_cors_origins(monkeypatch) -> None:
    import importlib
    import src.adapters.api.app

    # Test case 1: Local development / wildcard fallback (no env set)
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    importlib.reload(src.adapters.api.app)
    from fastapi.testclient import TestClient as Client
    client_wildcard = Client(src.adapters.api.app.app)
    
    res = client_wildcard.get("/health", headers={"Origin": "https://random-origin.com"})
    assert res.headers.get("access-control-allow-origin") == "https://random-origin.com"

    # Test case 2: Configured origins accepted, others rejected
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://evalforge.vercel.app, https://another-allowed.com")
    importlib.reload(src.adapters.api.app)
    client_configured = Client(src.adapters.api.app.app)

    # Configured origin accepted
    res_accepted = client_configured.get("/health", headers={"Origin": "https://evalforge.vercel.app"})
    assert res_accepted.headers.get("access-control-allow-origin") == "https://evalforge.vercel.app"

    # Unconfigured origin rejected (CORS headers not returned)
    res_rejected = client_configured.get("/health", headers={"Origin": "https://unconfigured-site.com"})
    assert "access-control-allow-origin" not in res_rejected.headers

    # Clean up env
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    importlib.reload(src.adapters.api.app)

