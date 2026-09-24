# DataScope — Enterprise Business Intelligence & Decision Intelligence Platform

DataScope is a secure, multi-tenant enterprise Business Intelligence and Decision Support Platform powered exclusively by **Supabase** (Supabase Auth, Supabase PostgreSQL with Row-Level Security, Supabase Storage, and Supabase Realtime).

---

## 1. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, `@supabase/supabase-js`, Recharts, Lucide Icons, React Router 6.
- **Backend**: Python 3.9+, FastAPI, Uvicorn, Supabase Python Client (`supabase`), PyJWT, Pandas, NumPy, ReportLab (PDF), python-docx (DOCX).
- **Permanent Storage & Auth**: **Supabase Only**
  - **Authentication**: Supabase Auth (Email/Password, JWT sessions, Google OAuth 2.0 PKCE, Password Recovery).
  - **Database**: Supabase PostgreSQL with Row-Level Security (RLS).
  - **File Storage**: Supabase Storage private buckets (`datasets`, `reports`).
  - **Realtime**: Supabase Realtime WebSocket events.

---

## 2. Supabase Setup Instructions

### Step 1: Create a Supabase Project
1. Go to [https://database.new](https://database.new) and create a new Supabase project.
2. Note your **Project URL**, **Anon (public) Key**, **Service Role (secret) Key**, and **Database Connection String** from `Project Settings -> API & Database`.

### Step 2: Run Database Migrations
In your Supabase Dashboard, open the **SQL Editor** and run the migration scripts located in `supabase/migrations/`:
1. `supabase/migrations/20260923000000_datascope_schema.sql` (Creates profiles, companies/workspaces, memberships, datasets, versions, data sources, sync jobs, reports, audit logs).
2. `supabase/migrations/20260923000001_rls_policies.sql` (Enables RLS on all tables, creates tenant isolation policies, and initializes private storage buckets `datasets` and `reports`).

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` in the root (for backend) and `frontend/.env` (for frontend):

**Backend `.env`:**
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_DB_URL=postgresql://postgres.your-project-id:password@aws-0-region.pooler.supabase.com:6543/postgres
DATABASE_URL=sqlite:///./datascope.db
SECRET_KEY=your-jwt-secret-key
```

**Frontend `frontend/.env`:**
```env
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_BASE_URL=http://localhost:8000
```

---

## 3. Running the Project Locally

### Backend (FastAPI)
```bash
cd backend
# Activate virtual environment
.\venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run FastAPI development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
The application will be accessible at [http://localhost:5173](http://localhost:5173).

---

## 4. Key Business Intelligence Modules

1. **Overview & Executive Dashboard**: KPI scorecards, multi-granularity trend velocity, business alerts, and domain blueprints.
2. **Dataset Management**: Direct visible actions for CSV, Excel (.xlsx/.xls), JSON upload to Supabase Storage with preview and validation.
3. **Explore**: Dynamic multi-dimensional pivot tables, bar/line/scatter distributions, and stacked drill-downs.
4. **Trends Intelligence**: Moving averages (3/7 periods), volatility indices, and period-over-period delta calculations.
5. **Universal Forecasting**: Baseline projection horizons with 80% and 95% confidence intervals and seasonal decomposition.
6. **Risk & Anomaly Register**: Margin compression warnings, volume drops, and concentration risks with severity, evidence, and actions.
7. **Competition Intelligence**: Strict external peer company benchmark comparisons with market gaps and strategic positioning.
8. **Actionable Recommendations**: Quantified, evidence-backed roadmaps with problem definitions, root causes, actions, and expected ROI.
9. **8-Page Executive Reports**: Dense boardroom dossiers exportable to high-definition PDF and editable DOCX with 6-question analytical frameworks.
10. **Live Data Pipelines**: Multi-source connectors (PostgreSQL, MySQL, REST APIs, Google Sheets) with scheduled background sync workers.

---

## 5. Security & Row-Level Security (RLS)

- **Strict Tenant Isolation**: All datasets, sync jobs, and reports are scoped by `company_id`.
- **Row-Level Security**: Every SQL query is filtered by `user_has_company_access(company_id)` at the database engine level.
- **Service Role Protection**: The service role secret key is kept strictly on the backend server and never exposed to the frontend browser.
