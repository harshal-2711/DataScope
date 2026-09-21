# DataScope

A universal, dataset-agnostic, real-world data analytics and decision-intelligence platform.
DataScope helps users load, validate, explore, and understand any tabular dataset without
assuming a specific domain (it is not e-commerce-specific and never hard-codes
column names or structures).

## Technology Stack

**Frontend**
- React 18 + TypeScript
- Vite
- Tailwind CSS v4
- shadcn/ui & Lucide Icons
- Recharts (ComposedChart, Bar, Line, Scatter, Area)
- React Router

**Backend**
- Python 3.9+
- FastAPI & Uvicorn
- Pandas & NumPy
- In-memory dataset store (stateless HTTP, no external DB/auth required)

## Architecture

```
DataScope/
├── frontend/   # React SPA — UI only, clean components, no analytical business logic
└── backend/    # FastAPI service — Robust ingestion, type inference, grain engine, playbooks, trends, forecasting, data quality
```

- Frontend and backend are completely decoupled and communicate via typed JSON endpoints over HTTP.
- UI components never contain statistical or domain inference logic; all intelligence is computed by the backend.
- Purely dataset-agnostic: adapts dynamically to 77+ industry domains with evidence and confidence scores.
- Raw datasets are never modified in place; in-memory storage preserves uploaded data integrity.

---

## Phase 1 — Dataset Ingestion & Understanding

DataScope provides enterprise-grade tabular file ingestion:
1. **Multi-Format & Encoding Support**:
   - Parses CSV, TSV, TXT, Excel (`.xlsx`, `.xls`).
   - Automatic encoding fallbacks (`utf-8`, `utf-8-sig`, `latin1`, `cp1252`, `iso-8859-1`).
   - Delimiter sniffing (`,`, `;`, `\t`, `|`).
2. **Malformed Row Recovery & Header Normalization**:
   - Gracefully recovers from malformed rows (`on_bad_lines='skip'`).
   - Automatically detects and normalizes duplicate column headers with diagnostic tracking.
3. **Universal 12-Type Semantic Inference Engine**:
   - Classifies columns into 12 semantic types: `Integer`, `Float`, `Boolean`, `Text`, `Category`, `Identifier`, `Date`, `Datetime`, `Duration`, `Percentage`, `Currency`, `Timestamp`.
   - Protects against common errors: phone numbers and zip codes are guarded against being falsely classified as dates.
   - Provides confidence scores (0.0–1.0), missing value counts and percentages, unique cardinality, clean example values, and parsing warnings.
   - Never displays raw `object` for valid date columns.

---

## Phase 2 — Universal Data Analysis & Domain Intelligence

1. **Dataset Grain & Entity Engine**:
   - Identifies the analytical grain of the dataset:
     - `one_row_per_tender` (Government Procurement)
     - `one_row_per_transaction` (Sales & E-commerce)
     - `one_row_per_customer` (Customer Analytics)
     - `one_row_per_match` (IPL / Cricket fixtures)
     - `one_row_per_ball` (Cricket deliveries)
     - `one_row_per_student` (Education / Academic records)
     - `one_row_per_employee` (Workforce / HR)
     - `one_row_per_event` (Logs / Telemetry)
     - `one_row_per_measurement` (IoT / Sensors)
     - `one_row_per_record` (Generic fallback)
   - Distinguishes **Row Count** from **Unique Entity Count** and computes repeated observation ratios.
   - Enforces **Aggregation Guardrails** against double-counting hazards when multi-row entities are detected.
2. **77 Domain Blueprints (Including Government Procurement & Government Finance)**:
   - **Government Procurement**: Tender solicitations, buyer agencies, contract values, procurement methods, tender lifecycle duration, and bidder competition.
   - **Government Finance**: Budget appropriations, actual expenditures, departmental spend, and budget execution rates.
   - **Cricket / IPL**: Automatic separation of match-level vs ball-by-ball grain.
   - **Healthcare**: Strictly descriptive clinical operations (length of stay, bed occupancy, billing), with zero fabricated diagnoses or causes.
   - **Sales & Commerce**: Top-line revenue, order volumes, average order value, with profit margins calculated strictly when COGS/profit data is present.
   - **Generic / Unknown Domain**: Transparent fallback with confidence scoring ($\le 0.65$) without hallucinating business metrics.
3. **Universal Statistics**:
   - Parametric and non-parametric statistics for every column (mean, median, mode, variance, std dev, IQR, percentiles P25/P50/P75/P90/P99, skewness, frequency distribution, and Pearson correlation matrix).

---

## Phase 3 — Trends Intelligence, Smart Charts & Forecasting

1. **Centralized Trends Intelligence**:
   - **Time Dimension Validation**: Automatic identification of date/timestamp columns, parsing validation, interval frequency detection (Daily, Weekly, Monthly, Quarterly, Yearly, Irregular), and non-uniform interval detection.
   - **Multi-Granularity Aggregation**: Dynamic time-series aggregation with user-switchable granularities.
   - **Period-over-Period Comparisons**: Current vs Previous period calculations, absolute difference, percentage change, and identification of all-time peaks and troughs.
   - **Rolling Averages & Volatility**: 3-period and 7-period moving averages, standard deviation of changes, Coefficient of Variation (CV), and stability classification (`Stable`, `Moderate Volatility`, `High Volatility`).
   - **Anomaly & Spike/Drop Detection**: Identifies periods deviating $> 2\sigma$ from the rolling baseline with clear logs.
   - **Category Growth Breakdown**: Segment-level time series identifying which categories increased vs declined period-over-period.
   - **12 Practical Trend Questions**: Structured answers to key analytical questions (metric analyzed, current vs prior values, peak/trough, growing/declining segments, volatility, next recommended investigations).
2. **Smart Chart Recommendation Engine**:
   - Follows strict analytical hierarchy:
     `DATA UNDERSTANDING → DATASET GRAIN → DOMAIN DETECTION → ANALYTICAL QUESTION → METRIC VALIDATION → CHART SELECTION → EXPLANATION → LIMITATIONS`
   - **Strict Visual Rules**:
     - Bar charts for category comparisons.
     - Line charts for valid time trends.
     - Histograms for continuous distributions.
     - Scatter plots for bivariate numerical associations.
     - Pie/donut charts ONLY for valid part-to-whole proportions with $\le 6$ slices.
     - **NEVER use pie charts for durations, averages, or rates** (e.g. tender duration by category is strictly rendered as a bar chart).
   - Every chart card displays: analytical question, metric definition, unit, aggregation, dataset grain, explanation, and limitations.
3. **Statistical Forecasting Module (Optional)**:
   - Validates prerequisites (valid time column, $\ge 6$ historical observations, continuous numeric metric).
   - Fits **Holt's Linear Exponential Smoothing** (level and trend) with $80\%$ and $95\%$ analytical confidence intervals.
   - Computes in-sample accuracy metrics (MAPE, RMSE, MAE) and model confidence score.
   - Interactive horizon controls (+3, +6, +12, +24 periods).
   - Explicit analytical disclaimer: forecasts are mathematical extrapolations of historical patterns, not guaranteed outcomes.
4. **Comprehensive Data Quality & Hygiene Engine**:
   - Scores dataset quality on a 0–100 scale (`Healthy`, `Warning`, `Critical`).
   - 12-point hygiene check: missing value percentages, duplicate rows, duplicate primary IDs, invalid/mixed dates, irregular intervals, suspicious negative values in naturally non-negative measures, zero denominators, and extreme statistical outliers ($3\times \text{IQR}$).
   - Generates actionable recommendations and column-level hygiene diagnostics.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/dataset/upload` | In-memory upload, robust file parsing, and summary generation |
| `GET` | `/api/dataset/{dataset_id}/intelligence` | Full 15-step domain intelligence pipeline with grain detection |
| `GET` | `/api/dataset/{dataset_id}/trends` | Time-series trends intelligence and period comparisons |
| `GET` | `/api/dataset/{dataset_id}/forecast` | Holt's linear exponential smoothing forecast with confidence intervals |
| `GET` | `/api/dataset/{dataset_id}/data_quality` | Comprehensive 12-point data quality and hygiene report |
| `GET` | `/api/dataset/{dataset_id}/statistics` | Universal parametric and non-parametric statistics |
| `GET` | `/api/dataset/{dataset_id}/decision_dashboard` | Executive decision-oriented dashboard |
| `GET` | `/api/dataset/{dataset_id}/recommendations` | Auto-ranked chart recommendations |
| `GET` | `/api/dataset/{dataset_id}/drilldown` | Multi-level filtered drilldown aggregations |

---

## Setup & Running Instructions

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+

### Backend Setup
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Start the Backend Server (Port 8000)
```powershell
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup & Start (Port 5173)
```powershell
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`.

---

## Testing & Validation

### Run All Backend Unit & Integration Tests (49 tests):
```powershell
cd backend
$env:PYTHONPATH='.'
venv\Scripts\python -m unittest discover -s tests -p "test_*.py"
```

### Run End-to-End Real Data Verifications (12 datasets):
```powershell
cd backend
$env:PYTHONPATH='.'
venv\Scripts\python tests/verify_phase3_e2e.py
```

### Run Frontend Production Build & TypeScript Typecheck:
```powershell
cd frontend
npm run build
```

---

## Known Limitations & Extension Guide

- **In-Memory Storage**: Datasets are stored in memory for privacy, speed, and zero external dependency footprint. Server restart clears uploaded datasets.
- **Forecasting Horizons**: Extrapolations beyond 24 periods are disabled to prevent speculative drift.
- **High-Cardinality Dimensions**: Categorical charts display the top 12 categories (or top 6 for pie charts) to maintain legibility.
- **Adding New Domains**:
  1. Add a new blueprint in `backend/app/domains/<domain_module>.py` using `DomainBlueprint`.
  2. Register in `backend/app/domains/registry.py`.
  3. Add a specialized dashboard builder in `backend/app/services/business_analytics_engine.py`.
