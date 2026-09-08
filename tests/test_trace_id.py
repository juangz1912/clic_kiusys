def test_trace_id_propagates_from_header(client):
    response = client.get("/api/v2/health", headers={"X-Trace-Id": "trace-demo-123"})
    assert response.status_code == 200
    assert response.headers.get("X-Trace-Id") == "trace-demo-123"
    assert response.json()["trace_id"] == "trace-demo-123"
