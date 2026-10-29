# SalesIQ — Mini AI Business Intelligence Assistant

A small, runnable natural-language sales analytics application built for the AI-Assisted Development Challenge. It uses **FastAPI + SQLite + a lightweight HTML/CSS/JavaScript UI**. No API key or paid LLM is required.

## Features
- Imports the supplied sales CSV into a local SQLite database at first startup.
- Supports all five challenge questions: total revenue, highest-revenue product, monthly revenue trend, highest-sales region, and revenue change between two months.
- Returns structured JSON with an answer, intent, and supporting figures.
- Rejects unsupported questions and too-short inputs with clear errors.
- Uses an allowlist of deterministic, read-only SQL query templates; user text is never concatenated into SQL.
- Includes eight automated tests.

## Revenue definition and data quality
Net revenue = `quantity × unit_price − discount_amount`. Returned transactions are excluded. The supplied file contains 51 rows; one row (`TXN0051`) has a missing unit price and is skipped rather than assigning an invented value. This leaves 50 valid records. Zero-quantity records are retained because they are valid records with zero sales. The app uses the CSV's `DD-MM-YYYY` date format and stores dates as ISO `YYYY-MM-DD`.

## Run locally (Windows PowerShell or terminal)
1. Install Python 3.10 or newer.
2. Extract this project folder and open a terminal inside it.
3. Create and activate a virtual environment:

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
4. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Start the app:
   ```bash
   uvicorn app.main:app --reload
   ```
6. Open `http://127.0.0.1:8000`. API docs: `http://127.0.0.1:8000/docs`.

The SQLite database `sales.db` is created automatically beside the README on first launch. To re-import a changed CSV, stop the app and delete `sales.db`, then restart.

## Example questions
- What is the total revenue?
- Which product generated the highest revenue?
- What is the monthly revenue trend?
- Which region generated the highest sales?
- How did revenue change between January and June 2026?

## Run tests
```bash
pytest -q
```

## Architecture
```text
Business User
     |
     v
Web UI (HTML / CSS / JavaScript)
     |
     | POST /api/ask { question }
     v
FastAPI Question API
     |
     v
Intent Mapper (supported question patterns)
     |
     v
Allowlisted, read-only SQL templates
     |
     v
SQLite sales table  <--- CSV import + validation
     |
     v
Structured JSON (answer + supporting figures)
     |
     v
Web UI result display
```

## AI approach, safety, and limitations
This implementation uses an **AI-assisted interpretation mechanism**: a transparent intent mapper recognises common natural-language phrasings and routes them to predefined analytical SQL. This was chosen for a short challenge to keep answers reproducible and auditable. It does not call an external LLM, so it works offline and avoids model hallucinations/API costs. Because no arbitrary SQL is generated, destructive operations cannot be triggered through the question endpoint. Unknown questions are rejected instead of guessed.

Limitations: intent coverage is limited to supported patterns; month comparison expects two month names and defaults to 2026 when a year is omitted; there is no login or multi-user access control; data is loaded from one CSV; charts and exports are not included. These can be added next.

## Development note 
- **AI tools used:** ChatGPT for implementation planning, code drafting, and debugging assistance; Python/pytest for local verification.
- **How AI was used:** to break the task into API, data ingestion, analytics, UI, testing, and documentation; and to review validation and query-safety choices.
- **Problems and debugging:** missing numeric fields can distort revenue, so the importer skips rows with invalid/missing required values and the health endpoint reports loaded row count. Query support is deliberately allowlisted so unsupported questions return a clear error.
- **What I would improve with another day:** add an LLM intent parser with schema-constrained output and validation, visual trend charts, CSV/JSON export, broader date parsing, richer edge-case tests, and deployment configuration.

