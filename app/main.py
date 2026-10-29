import csv, os, re, sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("BI_DB_PATH", ROOT / "sales.db"))
CSV_PATH = Path(os.getenv("BI_CSV_PATH", ROOT / "ai_bi_assistant_sales_data - GET.csv"))
app = FastAPI(title="Mini AI Business Intelligence Assistant", version="1.0.0",
              description="Natural-language sales analytics backed by validated SQLite queries.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class QuestionRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect()
    conn.execute("""
      CREATE TABLE IF NOT EXISTS sales (
        transaction_id TEXT PRIMARY KEY, order_date TEXT NOT NULL, product TEXT NOT NULL,
        category TEXT NOT NULL, region TEXT NOT NULL, sales_channel TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity >= 0), unit_price REAL NOT NULL CHECK(unit_price >= 0),
        discount_amount REAL NOT NULL CHECK(discount_amount >= 0), status TEXT NOT NULL
      )
    """)
    count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    if count == 0 and CSV_PATH.exists():
        with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = datetime.strptime(row["Order_date"].strip(), "%d-%m-%Y").strftime("%Y-%m-%d")
                    quantity = int(row["Quantity"])
                    price = float(row["Unit_price"])
                    discount = float(row["Discount_amount"] or 0)
                    if not row["Transaction_Id"] or not row["Product"] or quantity < 0 or price < 0 or discount < 0:
                        continue
                    conn.execute("""INSERT OR IGNORE INTO sales VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (row["Transaction_Id"].strip(), date, row["Product"].strip(), row["Category"].strip(),
                         row["Region"].strip(), row["Sales_channel"].strip(), quantity, price, discount,
                         row["Status"].strip()))
                except (ValueError, TypeError, KeyError):
                    # Reject malformed rows instead of silently inventing missing values.
                    continue
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

def money(v):
    return round(float(v or 0), 2)

def run_question(question: str):
    q = re.sub(r"\s+", " ", question.lower()).strip()
    if not q or len(q) < 2:
        raise HTTPException(422, "Please enter a meaningful question.")
    conn = connect()
    # Revenue is net sales (quantity * unit price - discount); returned transactions are excluded.
    base = " FROM sales WHERE lower(status) != 'returned' "
    try:
        if any(x in q for x in ["total revenue", "revenue overall", "overall revenue", "total sales", "how much revenue"]):
            row = conn.execute("SELECT ROUND(SUM(quantity * unit_price - discount_amount),2) AS revenue, COUNT(*) AS orders, SUM(quantity) AS units" + base).fetchone()
            value = money(row["revenue"])
            return {"question": question, "intent": "total_revenue",
                "answer": f"Total net revenue is ₹{value:,.2f} across {row['orders']} non-returned transactions.",
                "value": value, "unit": "INR", "supporting_data": {"eligible_transactions": row["orders"], "units_sold": row["units"], "formula": "SUM(quantity × unit_price − discount_amount)", "excluded_status": "Returned"}}
        if ("highest" in q or "top" in q or "best" in q) and "product" in q:
            rows = conn.execute("SELECT product, ROUND(SUM(quantity*unit_price-discount_amount),2) revenue, SUM(quantity) units FROM sales WHERE lower(status)!='returned' GROUP BY product ORDER BY revenue DESC, product ASC LIMIT 10").fetchall()
            if not rows: raise HTTPException(404, "No sales data is available.")
            top = rows[0]
            return {"question": question, "intent": "top_product", "answer": f"{top['product']} generated the highest net revenue: ₹{money(top['revenue']):,.2f}.",
                "value": money(top["revenue"]), "unit": "INR", "supporting_data": {"top_product": dict(top), "ranking": [dict(r) for r in rows]}}
        if "month" in q and any(x in q for x in ["trend", "monthly", "each month", "by month", "per month"]):
            rows = conn.execute("SELECT strftime('%Y-%m',order_date) month, ROUND(SUM(quantity*unit_price-discount_amount),2) revenue FROM sales WHERE lower(status)!='returned' GROUP BY month ORDER BY month").fetchall()
            data = [{"month":r["month"],"revenue":money(r["revenue"])} for r in rows]
            return {"question":question,"intent":"monthly_trend","answer":f"Monthly net revenue is available for {len(data)} months, from {data[0]['month']} through {data[-1]['month']}.",
                    "value":None,"unit":"INR","supporting_data":{"monthly_revenue":data}}
        if "region" in q and any(x in q for x in ["highest","top","best","sales","revenue"]):
            rows = conn.execute("SELECT region, ROUND(SUM(quantity*unit_price-discount_amount),2) revenue FROM sales WHERE lower(status)!='returned' GROUP BY region ORDER BY revenue DESC, region ASC").fetchall()
            top=rows[0]
            return {"question":question,"intent":"top_region","answer":f"{top['region']} generated the highest net sales at ₹{money(top['revenue']):,.2f}.",
                    "value":money(top["revenue"]),"unit":"INR","supporting_data":{"top_region":dict(top),"regional_breakdown":[dict(r) for r in rows]}}
        if any(x in q for x in ["change", "compare", "difference", "between"]) and ("revenue" in q or "sales" in q):
            months = re.findall(r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b", q)
            month_map={"jan":"01","january":"01","feb":"02","february":"02","mar":"03","march":"03","apr":"04","april":"04","may":"05","jun":"06","june":"06","jul":"07","july":"07","aug":"08","august":"08","sep":"09","september":"09","oct":"10","october":"10","nov":"11","november":"11","dec":"12","december":"12"}
            if len(months)>=2:
                m1,m2=month_map[months[0]],month_map[months[1]]
                year_match=re.search(r"20\d{2}",q); year=year_match.group(0) if year_match else "2026"
                keys=[f"{year}-{m1}",f"{year}-{m2}"]
                vals=[]
                for key in keys:
                    r=conn.execute("SELECT ROUND(SUM(quantity*unit_price-discount_amount),2) revenue FROM sales WHERE lower(status)!='returned' AND strftime('%Y-%m',order_date)=?",(key,)).fetchone()
                    vals.append(money(r["revenue"]))
                diff=round(vals[1]-vals[0],2)
                pct=round(diff/vals[0]*100,2) if vals[0] else None
                direction="increased" if diff>0 else "decreased" if diff<0 else "did not change"
                return {"question":question,"intent":"month_comparison","answer":f"Revenue {direction} by ₹{abs(diff):,.2f} from {keys[0]} (₹{vals[0]:,.2f}) to {keys[1]} (₹{vals[1]:,.2f}).",
                    "value":diff,"unit":"INR","supporting_data":{"from_month":keys[0],"from_revenue":vals[0],"to_month":keys[1],"to_revenue":vals[1],"absolute_change":diff,"percentage_change":pct}}
        raise HTTPException(400, "I couldn't map that question to a supported analysis. Try total revenue, highest-revenue product, monthly revenue trend, highest-sales region, or compare revenue between two months.")
    finally:
        conn.close()

@app.get("/api/health")
def health():
    conn=connect()
    try:
        count=conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        return {"status":"ok","database":"sqlite","loaded_records":count}
    finally: conn.close()

@app.post("/api/ask")
def ask(payload: QuestionRequest):
    return run_question(payload.question)

@app.get("/api/summary")
def summary():
    conn=connect()
    try:
        row=conn.execute("SELECT COUNT(*) n, COUNT(DISTINCT product) products, COUNT(DISTINCT region) regions FROM sales").fetchone()
        return dict(row)
    finally: conn.close()

# Serve the lightweight frontend from the same app.
if (ROOT / "frontend").exists():
    app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")
    @app.get("/")
    def home():
        return FileResponse(ROOT / "frontend" / "index.html")
