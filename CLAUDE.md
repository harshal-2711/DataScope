# DataScope

## Project

DataScope is a dataset-agnostic data analysis and decision-intelligence platform.

The dataset is the input. DataScope itself is the product.

The long-term platform will support:

- Dataset profiling
- Data quality analysis
- Data cleaning
- Exploratory analysis
- Statistical analysis
- Interactive visualization
- Trend detection
- Anomaly detection
- Forecasting
- Competition analysis when comparable data is available
- Risk detection
- Opportunity detection
- Evidence-based recommendations
- Report generation

## Current Development Approach

Build DataScope incrementally, phase by phase.

Do not implement future phases unless explicitly requested.

Current phase: Phase 1 — Project Setup.

## Initial Constraints

- No external APIs
- No AI APIs
- No authentication
- No payments
- No unnecessary database
- Do not fabricate data
- Do not fabricate competitor information

## Technology

Frontend:
- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui

Backend:
- Python
- FastAPI

Analytics:
- Pandas
- NumPy
- SciPy
- Statsmodels
- Scikit-learn

Visualization:
- Plotly and/or Recharts

## Architecture Rules

- Keep frontend and backend separate.
- Keep UI separate from business/analytics logic.
- Use reusable modules.
- Never hard-code dataset-specific column names.
- Never assume a dataset is e-commerce data.
- Never modify raw uploaded data.
- Keep processed data separate.
- Make automated insights traceable to evidence.
- Validate data before forecasting.
- Never present predictions as guaranteed outcomes.
- Avoid unnecessary dependencies and files.
- Do not create giant files when smaller modules are appropriate.

## Development Rules

Before implementing a task:

1. Inspect the existing project.
2. Understand the current structure.
3. Implement only the requested task.
4. Avoid changing unrelated files.
5. Test the implementation.
6. Report what was changed.
7. Report errors or limitations.

Do not claim a task is complete unless it has been tested.

## Design

DataScope should feel like a professional modern analytics/SaaS product.

Use:

- Clean layout
- Strong typography hierarchy
- Professional sidebar
- Consistent spacing
- Subtle cards
- Interactive data visualizations
- Responsive design
- Accessible contrast
- Useful empty states
- Useful loading and error states

Avoid:

- Excessive gradients
- Excessive animations
- Random colors
- Excessive cards
- Generic "AI" effects
- Unnecessary decoration

Use shadcn/ui where appropriate.

The visual design should be original and should not copy another product's branding.

## Dataset-Agnostic Requirement

Never assume specific column names.

Do not write logic such as:

if column == "Sales"

or:

if column == "Revenue"

Instead, determine column roles from data characteristics and/or user selection.

## Coding Style

Prefer:

- Clear names
- Small reusable functions
- Type safety
- Error handling
- Maintainable code
- Simple solutions before complex solutions

Do not over-engineer.