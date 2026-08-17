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

**Phase 2 — Dataset Ingestion and Understanding**
- Dataset upload (CSV, XLSX, XLS) via drag-and-drop or file picker
- Backend validation: file type, size limit, corrupt/empty file, empty dataset
- Dataset metadata: row/column counts, column names, detected data types
- Preview of the first 10 rows
- Upload flow states: idle → selected → processing → success/error, with retry
- Files are processed in memory only and are never persisted to disk
- No analytics, forecasting, database, auth, or external APIs yet

Phase 1 (project foundation) is complete: frontend/backend scaffolding, app
shell, navigation, and the `/api/health` connectivity check.

## Roadmap (Summary)

- **Phase 1** — Foundation ✅
- **Phase 2** — Dataset ingestion and profiling ✅ (this phase)
- **Phase 3** — Exploration and visualization tools
- **Phase 4** — Trend and risk detection
- **Phase 5** — Forecasting
- **Phase 6** — Recommendations and reporting
