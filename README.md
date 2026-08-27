# DataScope

A professional, dataset-agnostic data analysis and decision-intelligence platform.
DataScope helps users load, explore, and understand any tabular dataset without
assuming a specific domain (it is not e-commerce-specific and never hard-codes
column names).

## Technology Stack

**Frontend**
- React + TypeScript
- Vite
- Tailwind CSS v4
- shadcn/ui
- React Router

**Backend**
- Python
- FastAPI
- Uvicorn

## Architecture

```
DataScope/
├── frontend/   # React SPA — UI only, no business logic
└── backend/    # FastAPI service — API and (future) analytics logic
```

- Frontend and backend are fully separate applications communicating over HTTP.
- UI components never contain analysis/business logic; that logic lives in the backend.
- No dataset-specific assumptions (column names, industry, etc.) are hard-coded anywhere.
- Raw datasets are never modified in place (enforced from Phase 2 onward).

## Setup Instructions

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+

### Frontend
```powershell
cd frontend
npm install
```

### Backend
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run Instructions

### Start the backend (port 8000)
```powershell
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### Start the frontend (port 5173)
```powershell
cd frontend
npm run dev
```

Visit `http://localhost:5173`. The Overview page shows a live backend connection
status pulled from `GET /api/health`.

## Current Development Phase

**Phase 3 — Exploration and Automatic Visualization**
- Uploaded datasets are retained server-side in memory (no database) keyed
  by a generated `dataset_id`, so charts can be aggregated on demand
  without re-uploading
- A column profiler classifies every column (numeric, categorical,
  datetime, boolean, identifier, high-cardinality, or ignore) with no
  manual input
- A recommendation engine turns that profile straight into a ranked,
  diversified set of charts (bar, line, pie, histogram, scatter) —
  aggregation (sum/mean, time bucketing, top-N + "Other", correlation
  ranking for scatter pairs) happens entirely on the backend
- `GET /api/dataset/{dataset_id}/recommendations` returns ready-to-render,
  already-aggregated chart data — the frontend never sees raw rows or
  picks axes/columns/aggregations itself
- The Explore page automatically renders the recommended charts for
  whichever dataset was most recently uploaded on the Dataset page (shared
  via client-side `DatasetContext`, no auth/session concept)
- Categorical-only datasets (no numeric columns at all) still produce
  count/proportion charts rather than being silently dropped

Phase 2 (dataset ingestion) and Phase 1 (project foundation) remain intact
and unchanged.

## Roadmap (Summary)

- **Phase 1** — Foundation ✅
- **Phase 2** — Dataset ingestion and profiling ✅
- **Phase 3** — Exploration and visualization tools ✅ (this phase)
- **Phase 4** — Trend and risk detection
- **Phase 5** — Forecasting
- **Phase 6** — Recommendations and reporting

