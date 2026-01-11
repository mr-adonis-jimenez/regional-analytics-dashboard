from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_sample_dataset_present():
    res = client.get("/api/datasets")
    assert res.status_code == 200
    datasets = res.json()
    assert any(d["dataset_id"] == "sample" for d in datasets)


def test_regions_works_for_sample():
    res = client.get("/api/regions")
    assert res.status_code == 200
    rows = res.json()
    assert isinstance(rows, list)
    assert len(rows) >= 1
    assert {"region", "metric", "value", "lat", "lon"} <= set(rows[0].keys())


def test_ingest_json_and_analytics():
    payload = [
        {"region": "A", "lat": 10.0, "lon": 10.0, "date": "2025-01-01", "revenue": 100},
        {"region": "A", "lat": 10.0, "lon": 10.0, "date": "2025-02-01", "revenue": 150},
        {"region": "B", "lat": 20.0, "lon": 20.0, "date": "2025-01-01", "revenue": 90},
    ]
    res = client.post("/api/datasets/json?name=unit-test", json=payload)
    assert res.status_code == 200
    dataset_id = res.json()["dataset_id"]

    res2 = client.get(f"/api/analytics/regions?dataset_id={dataset_id}&value_col=revenue&agg=sum")
    assert res2.status_code == 200
    regions = res2.json()["regions"]
    assert [r["region"] for r in regions] == ["A", "B"]
    assert regions[0]["value"] == 250

    res3 = client.get(f"/api/analytics/trends?dataset_id={dataset_id}&date_col=date&region_col=region&value_col=revenue")
    assert res3.status_code == 200
    series = res3.json()["series"]
    assert any(p["region"] == "A" for p in series)

