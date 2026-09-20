"""HR, Recruitment, and Customer Support domain blueprints (Domains 18, 19, 62)."""
from __future__ import annotations

from app.domains.base import (
    ChartRule,
    ComparisonRule,
    DomainBlueprint,
    EntityRule,
    KpiRule,
    RecommendationRule,
    RiskRule,
    TrendRule,
)

DOMAINS: list[DomainBlueprint] = [
    # 18. HR and Workforce Analytics
    DomainBlueprint(
        id="hr_workforce",
        name="HR and Workforce Analytics",
        description="Employee headcount, compensation, turnover, retention, tenure, performance ratings, and department demographics.",
        keywords=("employee", "headcount", "salary", "attrition", "turnover", "tenure", "compensation", "job_title", "department", "hire_date", "termination_date", "performance_rating"),
        alternative_domains=("Recruitment", "Customer Support and Service", "General Business Analytics"),
        entities=(
            EntityRule("employee", "Employee", ("employee_id", "emp_id", "staff_id", "worker_id")),
            EntityRule("department", "Department / Business Unit", ("department", "dept", "division", "team")),
            EntityRule("job_role", "Job Role / Title", ("job_title", "role", "position", "designation")),
        ),
        kpis=(
            KpiRule("headcount", "Active Headcount", "Total active employees currently employed", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("employee_id", "emp_id"), formula="count_distinct", format="number", business_meaning="Total organization workforce size"),
            KpiRule("avg_salary", "Average Base Salary", "Mean compensation across employees", ("numeric",), metric_patterns=("salary", "compensation", "base_pay", "wage"), formula="mean", format="currency", business_meaning="Average employee payroll expense"),
            KpiRule("turnover_rate", "Employee Attrition Rate", "Percentage of workforce separated in the reporting period", ("numeric", "boolean"), metric_patterns=("attrition", "is_terminated", "left_company"), formula="mean", format="percentage", business_meaning="Workforce turnover rate"),
            KpiRule("avg_tenure", "Average Employee Tenure", "Mean length of service in years or months", ("numeric",), metric_patterns=("tenure", "years_at_company", "service_years"), formula="mean", format="number", business_meaning="Organizational institutional retention"),
        ),
        charts=(
            ChartRule("headcount_by_dept", "Headcount by Department", "bar", dimension_patterns=("department", "dept", "division"), metric_patterns=("employee_id", "emp_id"), aggregation="count", business_question="How is organizational staffing distributed across departments?"),
            ChartRule("salary_by_dept", "Average Salary by Department", "bar", dimension_patterns=("department", "dept", "job_title"), metric_patterns=("salary", "compensation"), aggregation="mean", business_question="Which departments command the highest average compensation?"),
            ChartRule("tenure_distribution", "Tenure Distribution", "histogram", metric_patterns=("tenure", "years_at_company"), aggregation="count", business_question="What is the distribution of employee tenure across the workforce?"),
        ),
        comparisons=(
            ComparisonRule("category", "Attrition Rate Comparison across Departments", ("department", "division"), ("attrition", "is_terminated")),
        ),
        trends=(
            TrendRule(("employee_id", "headcount"), ("hire_date", "date"), "Monitoring net workforce expansion and hiring cohorts"),
        ),
        risks=(
            RiskRule("attrition_spike", "Departmental Attrition Surge", "spike", metric_patterns=("attrition", "is_terminated"), threshold=0.15, label="Requires investigation", recommended_action="Conduct exit interviews and review management practices in high-turnover units."),
        ),
        recommendations=(
            RecommendationRule("customer_retention", "turnover_rate", "high_attrition", "Implement competitive salary band adjustments and career progression pathways.", "Subject to organizational compensation budgets."),
        ),
    ),

    # 19. Recruitment
    DomainBlueprint(
        id="recruitment",
        name="Recruitment",
        description="Talent acquisition, candidate pipelines, job requisitions, time to hire, interview stages, and offer acceptance rates.",
        keywords=("recruitment", "candidate", "applicant", "job_requisition", "time_to_hire", "interview_stage", "offer_accepted", "sourcing_channel", "recruiter", "resume"),
        alternative_domains=("HR and Workforce Analytics", "General Business Analytics"),
        entities=(
            EntityRule("candidate", "Job Candidate / Applicant", ("candidate_id", "applicant_id", "candidate_name")),
            EntityRule("requisition", "Job Requisition / Opening", ("requisition_id", "job_id", "opening_id", "role")),
        ),
        kpis=(
            KpiRule("total_applicants", "Total Applicants Sourced", "Sum of unique candidate job applications received", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("candidate_id", "applicant_id"), formula="count_distinct", format="number", business_meaning="Talent acquisition pipeline volume"),
            KpiRule("avg_time_to_hire", "Average Time to Hire (Days)", "Mean days from job posting to offer acceptance", ("numeric",), metric_patterns=("time_to_hire", "days_to_fill", "hiring_duration"), formula="mean", format="duration", business_meaning="Recruitment process efficiency"),
            KpiRule("offer_acceptance_rate", "Offer Acceptance Rate", "Proportion of extended job offers accepted by candidates", ("numeric", "boolean"), metric_patterns=("offer_accepted", "is_accepted"), formula="mean", format="percentage", business_meaning="Competitiveness of compensation offers"),
        ),
        charts=(
            ChartRule("applicants_by_source", "Applicants by Sourcing Channel", "pie", dimension_patterns=("sourcing_channel", "source", "recruiter"), metric_patterns=("candidate_id", "applicant_id"), aggregation="count", business_question="Which sourcing channels generate the highest candidate volume?"),
            ChartRule("time_to_hire_by_role", "Time to Hire by Job Role", "bar", dimension_patterns=("job_title", "department"), metric_patterns=("time_to_hire", "days_to_fill"), aggregation="mean", business_question="Which job roles experience the longest recruiting cycles?"),
        ),
        comparisons=(
            ComparisonRule("category", "Offer Acceptance by Department", ("department", "job_title"), ("offer_accepted", "is_accepted")),
        ),
        trends=(
            TrendRule(("candidate_id", "applicant_id"), ("application_date", "date"), "Tracking seasonal applicant volume across recruiting cycles"),
        ),
        risks=(
            RiskRule("hiring_delay", "Prolonged Time-to-Fill Anomaly", "spike", metric_patterns=("time_to_hire", "days_to_fill"), threshold=60.0, label="Requires investigation", recommended_action="Streamline interview panel stages and align recruiter sourcing targets."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "avg_time_to_hire", "slow_hiring", "Standardize interview rubrics to accelerate candidate evaluation stages.", "Requires interviewer alignment."),
        ),
    ),

    # 62. Customer Support and Service
    DomainBlueprint(
        id="customer_support",
        name="Customer Support and Service",
        description="Helpdesk tickets, resolution times, First Contact Resolution (FCR), CSAT scores, support agents, and ticket categories.",
        keywords=("ticket", "csat", "fcr", "resolution_time", "first_response_time", "support_agent", "helpdesk", "zendesk", "customer_service", "sla_breach", "escalation"),
        alternative_domains=("Product Analytics", "IT and Software", "HR and Workforce Analytics"),
        entities=(
            EntityRule("support_ticket", "Support Ticket", ("ticket_id", "case_id", "inquiry_id")),
            EntityRule("agent", "Support Agent / Specialist", ("agent_id", "agent_name", "assignee", "support_rep")),
        ),
        kpis=(
            KpiRule("avg_csat", "Average CSAT Score", "Mean customer satisfaction rating awarded upon ticket resolution", ("numeric",), metric_patterns=("csat", "satisfaction_score", "rating"), formula="mean", format="number", business_meaning="Customer support quality rating"),
            KpiRule("avg_first_response", "Average First Response Time (hours/mins)", "Mean elapsed time before initial agent response", ("numeric",), metric_patterns=("first_response_time", "frt", "response_hours"), formula="mean", format="duration", business_meaning="Support responsiveness speed"),
            KpiRule("fcr_rate", "First Contact Resolution (FCR) Rate", "Percentage of support inquiries resolved on initial interaction", ("numeric", "boolean"), metric_patterns=("is_fcr", "fcr", "resolved_first_contact"), formula="mean", format="percentage", business_meaning="Support problem-solving efficiency"),
            KpiRule("total_tickets", "Total Inbound Support Tickets", "Total support tickets received in period", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("ticket_id", "case_id"), formula="count_distinct", format="number", business_meaning="Gross customer support demand"),
        ),
        charts=(
            ChartRule("tickets_by_category", "Tickets by Inquiry Category", "bar", dimension_patterns=("category", "issue_type", "tag"), metric_patterns=("ticket_id", "case_id"), aggregation="count", business_question="What customer problems generate the highest support ticket volume?"),
            ChartRule("csat_by_agent", "CSAT Score by Support Agent", "bar", dimension_patterns=("agent_name", "agent_id", "tier"), metric_patterns=("csat", "rating"), aggregation="mean", business_question="Which support representatives achieve the highest customer satisfaction?"),
        ),
        comparisons=(
            ComparisonRule("category", "Resolution Time Comparison across Issue Types", ("category", "issue_type"), ("resolution_time", "frt")),
        ),
        trends=(
            TrendRule(("ticket_id", "case_id"), ("created_date", "date"), "Tracking daily and hourly support ticket queue influx"),
        ),
        risks=(
            RiskRule("sla_breach_rate", "Support SLA Breach Spike", "spike", metric_patterns=("sla_breach", "is_breached"), threshold=0.10, label="Requires investigation", recommended_action="Reallocate support agents to high-backlog queues to maintain SLA commitments."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "avg_first_response", "slow_frt", "Deploy automated response macros and self-service knowledge articles for top inquiry categories.", "Requires documented solution guides."),
        ),
    ),
]
