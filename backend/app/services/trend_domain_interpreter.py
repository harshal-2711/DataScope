"""Domain-Aware Trend Intelligence Interpreter.

Interprets time-series trends according to detected dataset domain and
semantic metric meaning instead of generic increase/decrease statements.

Ensures:
1. Strict distinction between Revenue, Profit, Loss, Cost, and Expenses (Revenue != Profit).
2. Domain-specific contextual phrasing for Finance, Sports, Healthcare, HR, Education,
   Operations/Procurement, and General/Unknown domains.
3. Strict safety guardrails (no medical diagnoses, no unsupported sentiment assumptions for unknown metrics).
4. Full qualification and confidence metadata.
"""
from __future__ import annotations

import re
from typing import Dict, List, Literal, Optional, Set, Tuple

import pandas as pd

from app.schemas.domain_blueprint import (
    DomainIdentitySchema,
    DomainTrendInterpretationSchema,
    MetricDescriptorSchema,
)


def _tokenize(text: str) -> Set[str]:
    """Tokenize string into lowercase alphanumeric tokens."""
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", str(text))
    spaced = spaced.replace("_", " ").replace("-", " ").replace(".", " ").replace("/", " ")
    return set(re.findall(r"[a-z0-9]+", spaced.lower()))


def classify_metric_semantic_role(
    col_name: str,
    domain_id: Optional[str] = None,
    all_columns: Optional[List[str]] = None,
) -> Tuple[str, str, float]:
    """Classify a numeric column into a precise semantic role.
    
    Returns:
        (semantic_role, role_label, confidence)
    """
    col_lower = col_name.lower().strip().replace(" ", "_").replace("-", "_").replace("/", "_")
    tokens = _tokenize(col_name)
    dom = (domain_id or "").lower()

    # 1. Profit vs Revenue vs Loss vs Expense Distinction (Universal & Strict)
    if "net_loss" in col_lower or "financial_loss" in col_lower or "operating_loss" in col_lower or "gross_loss" in col_lower:
        return "loss", "Financial Loss", 0.98

    if any(k in tokens for k in ("profit", "margin", "ebitda", "net_income", "earnings", "gross_profit", "net_profit")) or "profit" in col_lower or "margin" in col_lower:
        if "loss" in col_lower and "profit" not in col_lower:
            return "loss", "Financial Loss", 0.98
        return "profit", "Profit / Net Margin", 0.98

    if any(k in tokens for k in ("loss", "losses", "deficit")) or "loss" in col_lower or "defeat" in col_lower:
        # Check if sports match losses
        if any(k in tokens for k in ("match", "game", "fixture", "defeat", "defeats")) or "match_loss" in col_lower or "defeat" in col_lower:
            return "sports_losses", "Match Defeats / Losses", 0.95
        if ("sports" in dom or "cricket" in dom) and not any(k in tokens for k in ("net", "financial", "dollar", "amount", "currency", "cost", "revenue", "loss_amount")):
            return "sports_losses", "Match Defeats / Losses", 0.95
        return "loss", "Financial Loss", 0.95

    if any(k in tokens for k in ("revenue", "sales", "turnover", "gross_sales", "income", "billings", "gmv", "tender_value")) or any(col_lower.startswith(k) for k in ("sales", "rev")) or "revenue" in col_lower or "sales" in col_lower:
        return "revenue", "Sales Revenue / Top-Line Turnover", 0.98

    if any(k in tokens for k in ("expense", "cost", "expenses", "costs", "spend", "expenditure", "freight", "shipping_cost", "fee", "procurement_cost")) or "cost" in col_lower or "expense" in col_lower or "spend" in col_lower:
        if "procurement" in dom or "tender" in col_lower or "material" in col_lower:
            return "procurement_cost", "Procurement / Purchase Cost", 0.95
        return "expense_cost", "Operational Cost / Expense", 0.96

    # 2. Sports Domain Roles
    if "sport" in dom or "cricket" in dom or any(k in tokens for k in ("runs", "wickets", "goals", "points", "wins", "losses", "batsman", "bowler", "score")) or any(k in col_lower for k in ("match", "team", "run", "wicket", "goal", "win", "loss")):
        if any(k in tokens for k in ("win", "wins", "won", "victories")) or "win" in col_lower or "victor" in col_lower:
            return "sports_wins", "Match Wins", 0.96
        if any(k in tokens for k in ("loss", "losses", "lost", "defeats")) or "loss" in col_lower or "defeat" in col_lower:
            return "sports_losses", "Match Defeats", 0.96
        if any(k in tokens for k in ("runs", "points", "goals", "score", "strike_rate", "batting_avg", "extras", "boundaries")) or any(k in col_lower for k in ("run", "point", "goal", "score", "strike")):
            return "sports_scoring", "Scoring & Performance Output", 0.95
        if any(k in tokens for k in ("wickets", "overs", "balls", "assists", "rebounds", "tackles")) or any(k in col_lower for k in ("wicket", "over", "assist", "rebound")):
            return "sports_metrics", "Sports Athletic Metric", 0.92

    # 3. Healthcare Domain Roles
    if "health" in dom or "hospit" in dom or "clinic" in dom or "medic" in dom or any(k in tokens for k in ("patient", "recovery", "readmission", "diagnosis", "admission")) or any(k in col_lower for k in ("patient", "recovery", "readmission", "admission")):
        if any(k in tokens for k in ("readmission", "readmissions", "complication", "complications", "infection")) or "readmission" in col_lower or "complication" in col_lower:
            return "healthcare_readmission", "Patient Readmission / Complication", 0.95
        if any(k in tokens for k in ("recovery", "cure_rate", "discharge_rate", "survival")) or "recovery" in col_lower or "discharge" in col_lower:
            return "healthcare_recovery", "Recovery / Discharge Rate", 0.95
        if any(k in tokens for k in ("patient", "patients", "admissions", "inpatient", "outpatient", "bed_occupancy", "volume")) or "patient" in col_lower or "admission" in col_lower:
            return "healthcare_patient_volume", "Patient Volume", 0.94

    # 4. HR / Employee Analytics Roles
    if "hr" in dom or "people" in dom or "employee" in dom or "workforce" in dom or any(k in tokens for k in ("attrition", "turnover", "headcount", "salary", "employee", "compensation")) or any(k in col_lower for k in ("attrition", "turnover", "headcount", "salary", "wage", "payroll")):
        if any(k in tokens for k in ("attrition", "churn", "turnover", "resignation", "exit", "leaves")) or "attrition" in col_lower or "turnover" in col_lower or "resignation" in col_lower:
            return "hr_attrition", "Employee Attrition / Turnover", 0.96
        if any(k in tokens for k in ("salary", "compensation", "wage", "payroll", "bonus", "ctc")) or "salary" in col_lower or "compensation" in col_lower or "payroll" in col_lower:
            return "hr_salary", "Employee Compensation / Payroll", 0.95
        if any(k in tokens for k in ("headcount", "employees", "staff", "workers", "fte", "workforce")) or "headcount" in col_lower or "employee" in col_lower or "staff" in col_lower:
            return "hr_headcount", "Workforce Headcount", 0.94
        if any(k in tokens for k in ("attendance", "present", "absenteeism", "work_hours", "shifts")) or "attendance" in col_lower or "absent" in col_lower:
            return "hr_attendance", "Employee Attendance", 0.93

    # 5. Education Domain Roles
    if "edu" in dom or "academic" in dom or "student" in dom or "school" in dom or any(k in tokens for k in ("marks", "gpa", "score", "grade", "student", "attendance", "failure", "dropout")) or any(k in col_lower for k in ("gpa", "grade", "student", "failure", "dropout", "mark")):
        if any(k in tokens for k in ("failure", "failed", "dropout", "dropouts", "absent", "detention")) or "failure" in col_lower or "dropout" in col_lower:
            return "edu_failure_rate", "Student Failure / Dropout Rate", 0.95
        if any(k in tokens for k in ("marks", "score", "scores", "gpa", "grade", "performance", "percentile", "pass_rate")) or "gpa" in col_lower or "grade" in col_lower or "score" in col_lower or "mark" in col_lower or "pass_rate" in col_lower:
            return "edu_student_performance", "Student Academic Performance", 0.95
        if any(k in tokens for k in ("attendance", "presence", "enrolled", "enrolment")) or "attendance" in col_lower:
            return "edu_attendance", "Student Attendance", 0.93

    # 6. Operations / Procurement / Supply Chain Roles
    if "procure" in dom or "operat" in dom or "logist" in dom or "manufact" in dom or "supply" in dom or any(k in tokens for k in ("delivery", "lead_time", "turnaround", "defect", "orders", "quantity", "volume", "cycle_time", "aging")) or any(k in col_lower for k in ("delivery", "defect", "lead_time", "aging", "procure", "tender", "order")):
        if any(k in tokens for k in ("delivery", "turnaround", "aging", "delay")) or any(k in col_lower for k in ("delivery", "lead_time", "turnaround", "cycle_time", "aging", "processing_time", "duration", "durationindays", "delay")):
            return "ops_delivery_time", "Turnaround & Delivery Time", 0.95
        if any(k in tokens for k in ("defect", "defects", "error", "errors", "scrap", "rework", "failure")) or any(k in col_lower for k in ("defect", "error_rate", "scrap", "rework")):
            return "ops_defect_rate", "Defect & Error Rate", 0.96
        if any(k in tokens for k in ("procurement", "tender_value", "bids", "contract_value", "material_cost")) or any(k in col_lower for k in ("procure", "tender", "bid", "contract")):
            return "procurement_cost", "Procurement Value / Cost", 0.94
        if any(k in tokens for k in ("orders", "quantity", "units", "items", "throughput", "volume")) or any(k in col_lower for k in ("order", "quantity", "unit", "volume", "throughput")):
            return "ops_order_volume", "Order & Throughput Volume", 0.94

    # 7. Fallback keywords for general domains
    if any(k in tokens for k in ("quantity", "qty", "units", "count", "volume")) or any(k in col_lower for k in ("qty", "count", "volume")):
        return "general_volume", "Transaction / Unit Volume", 0.85
    if any(k in tokens for k in ("rate", "pct", "percentage", "ratio")) or any(k in col_lower for k in ("pct", "percentage", "ratio")):
        return "general_rate", "Percentage Rate / Ratio", 0.80
    if any(k in tokens for k in ("duration", "days", "time", "hours")) or any(k in col_lower for k in ("duration", "days", "hours")):
        return "general_duration", "Time Duration", 0.80

    return "general_measure", "Numerical Measure", 0.50


def interpret_domain_trend(
    metric_name: str,
    metric_column: str,
    direction: Literal["increasing", "decreasing", "stable", "fluctuating", "insufficient_data"],
    abs_change: Optional[float],
    pct_change: Optional[float],
    overall_change_pct: Optional[float],
    current_val: float,
    previous_val: Optional[float],
    all_dataset_columns: List[str],
    domain: Optional[DomainIdentitySchema] = None,
    granularity_label: str = "Monthly",
) -> DomainTrendInterpretationSchema:
    """Generate precise, domain-aware business and analytical interpretations."""
    domain_id = domain.domain_id if domain else "general_unknown"
    domain_name = domain.name if domain else "General Analytics"

    role, role_label, confidence = classify_metric_semantic_role(
        col_name=metric_column,
        domain_id=domain_id,
        all_columns=all_dataset_columns,
    )

    # Determine direction for the latest period delta vs overall trajectory
    if direction == "insufficient_data" or previous_val is None:
        period_direction = "insufficient_data"
    elif abs_change is not None and abs_change > 0:
        period_direction = "increasing"
    elif abs_change is not None and abs_change < 0:
        period_direction = "decreasing"
    elif direction == "fluctuating":
        period_direction = "fluctuating"
    else:
        period_direction = "stable"

    # Format actual change text
    pct_display = f"{abs(pct_change):.1f}%" if pct_change is not None else "N/A"
    abs_display = f"{abs(abs_change):,.2f}" if abs_change is not None else "0.00"
    
    if period_direction == "insufficient_data":
        actual_change_text = "Baseline observation (single period recorded; longitudinal change N/A)"
    elif period_direction == "stable" or abs_change == 0 or pct_change == 0:
        actual_change_text = f"Remained stable at {current_val:,.2f} (0.0% period change)"
    elif period_direction == "increasing":
        actual_change_text = f"Increased by {pct_display} (+{abs_display})"
    else:
        actual_change_text = f"Decreased by {pct_display} (-{abs_display})"

    # Contextual interpretation, sentiment, distinction, and qualification logic
    sentiment: Literal["positive", "negative", "neutral", "warning", "concern", "improvement", "informational"] = "neutral"
    contextual_interpretation = ""
    qualification = ""
    distinction_note: Optional[str] = None

    # Check for profit vs revenue co-existence in dataset
    has_profit_col = any("profit" in c.lower() for c in all_dataset_columns)
    has_revenue_col = any(any(k in c.lower() for k in ("revenue", "sales", "turnover")) for c in all_dataset_columns)

    # =========================================================================
    # 1. FINANCE / SALES / E-COMMERCE
    # =========================================================================
    if role == "revenue":
        distinction_note = (
            "Financial Distinction: This metric tracks top-line sales turnover (Gross Revenue), "
            "not net profit. Revenue changes reflect commercial sales intake rather than bottom-line earnings."
        )
        if period_direction == "increasing":
            sentiment = "positive"
            contextual_interpretation = (
                f"Top-Line Sales Growth: {granularity_label} revenue increased by {pct_display}, "
                f"indicating expanding commercial volume and positive top-line sales traction."
            )
        elif period_direction == "decreasing":
            sentiment = "warning"
            contextual_interpretation = (
                f"Revenue Decline: {granularity_label} revenue decreased by {pct_display}. "
                f"This indicates a top-line sales contraction (lower sales volume/turnover) rather than a net margin deficit."
            )
        elif period_direction == "fluctuating":
            sentiment = "informational"
            contextual_interpretation = (
                f"Revenue Fluctuation: {granularity_label} revenue demonstrates periodic variability "
                f"across observed sales periods."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"{granularity_label} revenue remained steady across observed sales periods."
        qualification = "High confidence: Metric identified as top-line revenue based on column metadata and domain detection."

    elif role == "profit":
        distinction_note = (
            "Financial Distinction: This metric tracks bottom-line profit (Net Margin / Income) after costs, "
            "distinct from gross top-line revenue."
        )
        if period_direction == "increasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Profit Improvement: {granularity_label} profit increased by {pct_display}, "
                f"indicating expanding net profitability and improved margin performance."
            )
        elif period_direction == "decreasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Profit Reduction: {granularity_label} profit decreased by {pct_display}, "
                f"indicating net margin compression or reduced earnings."
            )
        elif period_direction == "fluctuating":
            sentiment = "informational"
            contextual_interpretation = f"{granularity_label} profit shows period-over-period margin variability."
        else:
            sentiment = "neutral"
            contextual_interpretation = f"{granularity_label} profit margin remained consistent across periods."
        qualification = "High confidence: Metric identified as net profit/margin."

    elif role == "loss":
        distinction_note = "Financial Distinction: Inverted financial metric where higher values represent increased deficit."
        if period_direction == "increasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Loss Worsening: Recorded losses increased by {pct_display}, "
                f"indicating an escalating financial deficit that requires cost or margin review."
            )
        elif period_direction == "decreasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Loss Reduction: Recorded losses decreased by {pct_display}, "
                f"reflecting positive loss mitigation and deficit reduction."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Recorded losses remained level at {current_val:,.2f}."
        qualification = "High confidence: Inverted loss metric; reduction indicates financial improvement."

    elif role == "expense_cost":
        distinction_note = "Cost Management: Higher expenses represent potential margin pressure unless offset by revenue growth."
        if period_direction == "increasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Cost Increase Concern: Operational costs/expenses increased by {pct_display}, "
                f"representing potential cost inflation or budget pressure."
            )
        elif period_direction == "decreasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Cost Reduction: Operational costs/expenses decreased by {pct_display}, "
                f"indicating successful expenditure savings and leaner operations."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Operational expenses remained stable across periods."
        qualification = "High confidence: Expense/cost metric; reduction indicates operational savings."

    # =========================================================================
    # 2. SPORTS
    # =========================================================================
    elif role == "sports_wins":
        if period_direction == "increasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Improved Performance: Team match victories increased by {pct_display}, "
                f"reflecting strong competitive momentum and higher match conversion."
            )
        elif period_direction == "decreasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Performance Dip: Match wins decreased by {pct_display}, "
                f"reflecting lower match success rate across recent fixtures."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Match win rate remained consistent across observed periods."
        qualification = "Sports Analytics: Tracks team match victory frequency."

    elif role == "sports_losses":
        if period_direction == "increasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Performance Concern: Match defeats increased by {pct_display}, "
                f"signaling a losing trend that warrants tactical and lineup review."
            )
        elif period_direction == "decreasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Form Improvement: Match defeats decreased by {pct_display}, "
                f"indicating improved match competitiveness and defeat reduction."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Match defeat frequency remained steady across periods."
        qualification = "Sports Analytics: Inverted metric; defeat reduction indicates improved form."

    elif role in ("sports_scoring", "sports_metrics"):
        if period_direction == "increasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Scoring Improvement: {metric_name} increased by {pct_display}, "
                f"indicating improved offensive scoring efficiency and match output."
            )
        elif period_direction == "decreasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Scoring Decline: {metric_name} decreased by {pct_display}, "
                f"indicating reduced offensive conversion or scoring output."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"{metric_name} remained stable across observed match periods."
        qualification = "Sports Analytics: Tracks athletic scoring and in-match performance metrics."

    # =========================================================================
    # 3. HEALTHCARE (Strict Clinical Guardrails)
    # =========================================================================
    elif role == "healthcare_patient_volume":
        if direction == "increasing":
            sentiment = "informational"
            contextual_interpretation = (
                f"Patient Volume Expansion: Inpatient/admissions volume increased by {pct_display}, "
                f"indicating higher clinical capacity utilization and service demand."
            )
        elif direction == "decreasing":
            sentiment = "informational"
            contextual_interpretation = (
                f"Patient Volume Contraction: Patient volume decreased by {pct_display}, "
                f"reflecting lower inpatient occupancy during this period."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Patient admission volume remained steady across observed periods."
        qualification = (
            "Healthcare Operational Guardrail: Tracks patient flow and hospital capacity volume. "
            "Does not make medical diagnoses or clinical efficacy assessments."
        )

    elif role == "healthcare_recovery":
        if direction == "increasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Improved Recovery Rate: Patient recovery/discharge rate increased by {pct_display}, "
                f"indicating positive patient outcome progression across observed periods."
            )
        elif direction == "decreasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Recovery Rate Decline: Patient recovery rate decreased by {pct_display}, "
                f"warranting clinical care flow and patient follow-up review."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Patient recovery rate remained consistent at {current_val:,.2f}."
        qualification = "Clinical Analytics: Evaluates recorded patient discharge and recovery rates."

    elif role == "healthcare_readmission":
        if direction == "increasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Potential Concern (Readmission Escalation): Patient readmissions increased by {pct_display}, "
                f"highlighting potential post-discharge care or follow-up concerns."
            )
        elif direction == "decreasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Readmission Reduction: Patient readmissions decreased by {pct_display}, "
                f"indicating improved post-discharge stability and care continuity."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Patient readmission rate remained level across observed periods."
        qualification = "Healthcare Quality Guardrail: Inverted quality metric; readmission drop is positive."

    # =========================================================================
    # 4. HR / EMPLOYEE ANALYTICS
    # =========================================================================
    elif role == "hr_headcount":
        if direction == "increasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Workforce Growth: Organization headcount expanded by {pct_display}, "
                f"reflecting team hiring and organizational scaling."
            )
        elif direction == "decreasing":
            sentiment = "warning"
            contextual_interpretation = (
                f"Workforce Contraction: Organization headcount decreased by {pct_display}, "
                f"reflecting team downsizing or net departures."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Total workforce headcount remained steady at {current_val:,.0f} employees."
        qualification = "HR Analytics: Measures total organizational staffing capacity over time."

    elif role == "hr_attrition":
        if direction == "increasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Higher Attrition Concern: Employee turnover increased by {pct_display}, "
                f"signaling an elevated talent retention risk."
            )
        elif direction == "decreasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Attrition Reduction: Employee turnover decreased by {pct_display}, "
                f"indicating improved employee retention and organizational stability."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Employee attrition remained consistent across observed periods."
        qualification = "HR Analytics: Inverted metric; turnover reduction indicates improved talent retention."

    elif role == "hr_salary":
        if direction == "increasing":
            sentiment = "informational"
            contextual_interpretation = (
                f"Compensation Increase: Average/total compensation increased by {pct_display}, "
                f"reflecting payroll expansion, merit adjustments, or grade changes."
            )
        elif direction == "decreasing":
            sentiment = "informational"
            contextual_interpretation = (
                f"Payroll Contraction: Total/average compensation decreased by {pct_display}."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Compensation levels remained stable across observed periods."
        qualification = "HR Analytics: Measures payroll expenditure and compensation benchmarks."

    elif role in ("hr_attendance", "edu_attendance"):
        if direction == "increasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Attendance Improvement: Attendance rate increased by {pct_display}, "
                f"indicating higher participation and reduced absenteeism."
            )
        elif direction == "decreasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Attendance Decline: Attendance decreased by {pct_display}, "
                f"highlighting an absenteeism concern requiring engagement follow-up."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Attendance rate remained steady across periods."
        qualification = "Engagement Analytics: Evaluates cohort attendance and participation consistency."

    # =========================================================================
    # 5. EDUCATION
    # =========================================================================
    elif role == "edu_student_performance":
        if direction == "increasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Academic Performance Improvement: Student performance scores increased by {pct_display}, "
                f"indicating higher mastery and positive academic attainment."
            )
        elif direction == "decreasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Academic Performance Decline: Student scores decreased by {pct_display}, "
                f"signaling a performance dip that may require curricular intervention."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Student performance benchmarks remained steady across assessment periods."
        qualification = "Academic Analytics: Measures student test results, marks, or GPA progress."

    elif role == "edu_failure_rate":
        if direction == "increasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Potential Academic Concern: Course failure/dropout rate increased by {pct_display}, "
                f"indicating escalating academic risk that requires targeted academic support."
            )
        elif direction == "decreasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Academic Risk Reduction: Failure/dropout rate decreased by {pct_display}, "
                f"reflecting positive pass rate improvements."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Academic failure rate remained level across observed periods."
        qualification = "Academic Analytics: Inverted metric; reduction indicates higher course completion."

    # =========================================================================
    # 6. OPERATIONS / PROCUREMENT
    # =========================================================================
    elif role == "ops_delivery_time":
        if direction == "increasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Slower Delivery / Turnaround Delay: Delivery/lead time increased by {pct_display}, "
                f"indicating operational delays or supply chain bottlenecks."
            )
        elif direction == "decreasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Faster Delivery / Turnaround Improvement: Delivery/lead time decreased by {pct_display}, "
                f"indicating improved fulfillment speed and leaner processing."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Delivery turnaround remained steady across periods."
        qualification = "Supply Chain Analytics: Inverted metric; shorter lead time indicates superior operational velocity."

    elif role == "ops_defect_rate":
        if direction == "increasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Quality Concern (Defect Escalation): Defect/error rate increased by {pct_display}, "
                f"indicating quality variance that warrants quality assurance inspection."
            )
        elif direction == "decreasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Quality Improvement: Defect/error rate decreased by {pct_display}, "
                f"reflecting improved manufacturing precision and lower scrap."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Defect rate remained stable across observed production runs."
        qualification = "Quality Assurance Analytics: Inverted metric; defect reduction indicates improved product quality."

    elif role == "procurement_cost":
        if direction == "increasing":
            sentiment = "concern"
            contextual_interpretation = (
                f"Procurement Cost Increase: Procurement/contract spending increased by {pct_display}, "
                f"representing potential budget escalation or material price inflation."
            )
        elif direction == "decreasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Cost Reduction: Procurement costs decreased by {pct_display}, "
                f"indicating contract savings and cost reduction."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Procurement expenditure remained consistent across tender periods."
        qualification = "Procurement Analytics: Evaluates purchasing expenditure across contracts."

    elif role == "ops_order_volume":
        if direction == "increasing":
            sentiment = "improvement"
            contextual_interpretation = (
                f"Volume Growth: Order/throughput volume increased by {pct_display}, "
                f"reflecting expanding customer demand and higher order intake."
            )
        elif direction == "decreasing":
            sentiment = "warning"
            contextual_interpretation = (
                f"Volume Contraction: Order/throughput volume decreased by {pct_display}, "
                f"reflecting a reduction in unit demand."
            )
        else:
            sentiment = "neutral"
            contextual_interpretation = f"Order throughput remained stable across observed periods."
        qualification = "Operations Analytics: Measures physical order throughput and unit demand."

    # =========================================================================
    # 7. GENERAL / UNKNOWN DOMAINS (Strict Neutral Language)
    # =========================================================================
    else:
        # Default completely neutral language:
        # "The selected metric increased by X%."
        # "The selected metric decreased by X%."
        sentiment = "neutral"
        if direction == "increasing":
            contextual_interpretation = (
                f"The selected metric ({metric_name}) increased by {pct_display} "
                f"(+{abs_display}) across the observed period."
            )
        elif direction == "decreasing":
            contextual_interpretation = (
                f"The selected metric ({metric_name}) decreased by {pct_display} "
                f"(-{abs_display}) across the observed period."
            )
        elif direction == "fluctuating":
            contextual_interpretation = (
                f"The selected metric ({metric_name}) exhibited periodic fluctuations "
                f"across observed time intervals."
            )
        elif direction == "insufficient_data":
            contextual_interpretation = (
                f"Recorded single-period baseline for {metric_name} ({current_val:,.2f}). "
                f"Multi-period longitudinal comparison is unavailable."
            )
        else:
            contextual_interpretation = (
                f"The selected metric ({metric_name}) remained stable at {current_val:,.2f}."
            )
        confidence = 0.50
        qualification = (
            "Neutral Interpretation: Dataset belongs to a general or domain-agnostic category. "
            "Metric movement is presented factually without making unsupported positive or negative assumptions."
        )

    conf_level: Literal["High", "Moderate", "Neutral / Unassumed"] = (
        "High" if confidence >= 0.85 else ("Moderate" if confidence >= 0.70 else "Neutral / Unassumed")
    )

    return DomainTrendInterpretationSchema(
        domain_id=domain_id,
        domain_name=domain_name,
        metric_name=metric_name,
        metric_role=role_label,
        direction=direction,
        actual_change_text=actual_change_text,
        contextual_interpretation=contextual_interpretation,
        business_sentiment=sentiment,
        confidence=round(confidence, 2),
        confidence_level=conf_level,
        qualification=qualification,
        distinction_note=distinction_note,
    )
