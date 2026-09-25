# DataScope

DataScope is a multi-tenant business intelligence and decision support platform powered by Supabase and FastAPI.

---

## 1. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, `@supabase/supabase-js`, Recharts, Lucide Icons, React Router 6
- **Backend**: Python 3.9+, FastAPI, Uvicorn, Supabase Python Client, PyJWT, Pandas, NumPy, ReportLab, python-docx
- **Database & Auth**: Supabase PostgreSQL with Row-Level Security (RLS), Supabase Auth, Supabase Storage

---

## 2. Setup

### Step 1: Supabase Project
1. Create a project at [supabase.com](https://database.new).
2. Retrieve your project URL, anon key, service-role key, and database connection string from `Project Settings -> API & Database`.

### Step 2: Database Migrations
Run the SQL migration scripts in your Supabase SQL Editor:
1. `supabase/migrations/20260923000000_datascope_schema.sql`
2. `supabase/migrations/20260923000001_rls_policies.sql`

### Step 3: Environment Configuration
Copy `.env.example` to `.env` in the root (for backend) and `frontend/.env` (for frontend).

**Backend `.env`:**
```env
DATABASE_URL=sqlite:///./datascope.db
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_DB_URL=postgresql://postgres.your-project-id:your-password@aws-0-region.pooler.supabase.com:6543/postgres
SECRET_KEY=your-jwt-secret-key
```

**Frontend `frontend/.env`:**
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

> **Production Database Note:** Production deployments use Supabase PostgreSQL (`SUPABASE_DB_URL`). SQLite (`DATABASE_URL=sqlite:///./datascope.db`) is provided for local offline development and test execution.

---

## 3. Run Commands

### Backend (FastAPI)
```bash
cd backend
# Windows
.\venv\Scripts\activate
# Linux/macOS
# source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API docs are available at `http://localhost:8000/docs`.

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
The application runs at `http://localhost:5173`.

---

## 4. Key Modules

- **Executive Dashboard**: KPI scorecards, trend velocities, and business alerts.
- **Dataset Management**: CSV, Excel, and JSON ingestion with schema preview and validation.
- **Data Exploration**: Pivot tables, multi-dimensional distributions, and breakdowns.
- **Trends & Forecasting**: Moving averages, period-over-period variance, and baseline projection horizons.
- **Risk Register**: Margin alerts, volume drops, and concentration risk detection.
- **Reports Engine**: Automated PDF and DOCX export generation.
- **Data Connectors**: Multi-source sync pipelines (PostgreSQL, MySQL, REST, Google Sheets).

---

## 5. Security & Tenant Isolation

- **Tenant Isolation**: All datasets, sync jobs, and reports are scoped by `company_id`.
- **Row-Level Security**: Enforced via PostgreSQL RLS policies in Supabase.
- **Credential Protection**: Service role keys are restricted to backend environment variables and never exposed to the client.
