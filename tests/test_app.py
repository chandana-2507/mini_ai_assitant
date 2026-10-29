import os, tempfile
from pathlib import Path
from fastapi.testclient import TestClient
# Isolate the test database and seed from the supplied CSV.
tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
tmp.close()
os.environ["BI_DB_PATH"] = tmp.name
os.environ["BI_CSV_PATH"] = str(Path(__file__).resolve().parents[1] / "ai_bi_assistant_sales_data - GET.csv")
from app.main import app, init_db
init_db()
client = TestClient(app)

def test_health_and_data_loaded():
    r=client.get("/api/health")
    assert r.status_code==200
    assert r.json()["loaded_records"]==50

def test_total_revenue_has_supporting_formula():
    r=client.post("/api/ask",json={"question":"What is the total revenue?"})
    assert r.status_code==200
    assert r.json()["intent"]=="total_revenue"
    assert r.json()["supporting_data"]["formula"]

def test_top_product():
    r=client.post("/api/ask",json={"question":"Which product generated the highest revenue?"})
    assert r.status_code==200
    assert r.json()["intent"]=="top_product"
    assert r.json()["supporting_data"]["ranking"]

def test_monthly_trend():
    r=client.post("/api/ask",json={"question":"What is the monthly revenue trend?"})
    assert r.status_code==200
    assert len(r.json()["supporting_data"]["monthly_revenue"])==6

def test_top_region():
    r=client.post("/api/ask",json={"question":"Which region generated the highest sales?"})
    assert r.status_code==200
    assert r.json()["intent"]=="top_region"

def test_compare_months():
    r=client.post("/api/ask",json={"question":"How did revenue change between January and June 2026?"})
    assert r.status_code==200
    assert r.json()["intent"]=="month_comparison"
    assert "absolute_change" in r.json()["supporting_data"]

def test_unsupported_question_is_rejected():
    r=client.post("/api/ask",json={"question":"Tell me a joke"})
    assert r.status_code==400

def test_too_short_question_is_rejected():
    r=client.post("/api/ask",json={"question":"?"})
    assert r.status_code==422
