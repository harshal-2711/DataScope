"""Technology, SaaS, Web, IoT, and Cybersecurity domain blueprints (Domains 57, 58, 59, 60, 61, 68, 69)."""
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
    # 57. IT and Software
    DomainBlueprint(
        id="it_software",
        name="IT and Software",
        description="Software development projects, sprint velocity, bug tracking, code commits, deployments, and IT asset management.",
        keywords=("software", "jira", "git", "commit", "sprint", "velocity", "bug", "defect", "deployment", "pull_request", "build_status", "release", "story_points"),
        alternative_domains=("Product Analytics", "SaaS and Subscription", "Network and Infrastructure Monitoring"),
        entities=(
            EntityRule("ticket", "Development Issue / Ticket", ("ticket_id", "issue_key", "bug_id", "task_id")),
            EntityRule("developer", "Engineer / Contributor", ("developer", "assignee", "author", "engineer")),
            EntityRule("sprint", "Sprint / Milestone", ("sprint", "milestone", "release_version")),
        ),
        kpis=(
            KpiRule("story_points_completed", "Completed Story Points", "Total engineering story points delivered in the period", ("numeric",), metric_patterns=("story_points", "points", "completed_points"), formula="sum", format="number", business_meaning="Engineering delivery velocity"),
            KpiRule("bug_count", "Total Defect Count", "Total software defects logged during cycle", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("bug_id", "ticket_id"), formula="count_distinct", format="number", business_meaning="Software defect surface"),
            KpiRule("avg_resolution_time", "Average Issue Resolution Time", "Mean time from ticket creation to resolution", ("numeric",), metric_patterns=("resolution_hours", "lead_time_days", "cycle_time"), formula="mean", format="duration", business_meaning="Engineering cycle lead time"),
        ),
        charts=(
            ChartRule("velocity_by_sprint", "Sprint Velocity (Story Points)", "bar", dimension_patterns=("sprint", "release"), metric_patterns=("story_points", "points"), aggregation="sum", business_question="Is team delivery velocity stabilizing or increasing over sprints?"),
            ChartRule("bugs_by_severity", "Defect Count by Severity", "pie", dimension_patterns=("severity", "priority"), metric_patterns=("ticket_id", "bug_id"), aggregation="count", business_question="What proportion of open defects are critical/high severity?"),
        ),
        comparisons=(
            ComparisonRule("category", "Resolution Times by Issue Type", ("issue_type", "component"), ("cycle_time", "lead_time_days")),
        ),
        trends=(
            TrendRule(("story_points", "ticket_id"), ("sprint", "date"), "Tracking sprint capacity trends across quarters"),
        ),
        risks=(
            RiskRule("defect_spike", "Post-Release Defect Surge", "spike", metric_patterns=("bug_id", "ticket_id"), threshold=20.0, label="Requires investigation", recommended_action="Halt non-critical feature releases and conduct retrospective on QA test coverage."),
        ),
        recommendations=(
            RecommendationRule("quality_improvement", "bug_count", "high_defects", "Mandate automated regression testing in CI pipeline prior to merging pull requests.", "Requires team engineering capacity for test authoring."),
        ),
    ),

    # 58. SaaS and Subscription
    DomainBlueprint(
        id="saas_subscription",
        name="SaaS and Subscription",
        description="Subscription businesses, MRR, ARR, churn, Net Revenue Retention (NRR), customer lifetime value (LTV), and cohorts.",
        keywords=("mrr", "arr", "subscription", "churn", "renewal", "plan", "tier", "saas", "ltv", "cac", "nrr", "expansion_revenue", "downgrade", "cancellation"),
        alternative_domains=("IT and Software", "Product Analytics", "Sales and CRM"),
        entities=(
            EntityRule("subscriber", "Subscribed Account / Tenant", ("account_id", "tenant_id", "customer_id", "subscriber_id")),
            EntityRule("subscription", "Subscription Contract", ("subscription_id", "plan_id", "contract_id")),
        ),
        kpis=(
            KpiRule("mrr", "Monthly Recurring Revenue (MRR)", "Sum of normalized recurring monthly subscription fees", ("numeric",), metric_patterns=("mrr", "recurring_revenue", "monthly_fee"), formula="sum", format="currency", business_meaning="Predictable monthly subscription revenue base"),
            KpiRule("arr", "Annual Recurring Revenue (ARR)", "Annualized run-rate of recurring subscription contracts", ("numeric",), metric_patterns=("arr", "annual_revenue"), formula="sum", format="currency", business_meaning="Contracted annual revenue foundation"),
            KpiRule("churn_rate", "Customer Churn Rate", "Percentage of subscription base terminating recurring contracts", ("numeric", "boolean"), metric_patterns=("churn", "is_churned", "cancelled"), formula="mean", format="percentage", business_meaning="Rate of customer attrition"),
            KpiRule("arpu", "Average Revenue Per Account (ARPA)", "Mean recurring revenue generated per subscribed customer", ("numeric",), metric_patterns=("mrr", "fee", "amount"), formula="mean", format="currency", business_meaning="Account monetization depth"),
        ),
        charts=(
            ChartRule("mrr_trend", "MRR Growth Over Time", "line", dimension_patterns=("date", "month", "billing_period"), metric_patterns=("mrr", "recurring_revenue"), aggregation="sum", business_question="How is recurring monthly subscription revenue expanding?"),
            ChartRule("mrr_by_tier", "MRR Contribution by Subscription Tier", "pie", dimension_patterns=("plan", "tier", "package"), metric_patterns=("mrr", "amount"), aggregation="sum", business_question="Which subscription tiers drive the core recurring revenue?"),
        ),
        comparisons=(
            ComparisonRule("category", "Churn Rates by Plan Tier", ("plan", "tier"), ("is_churned", "churn")),
            ComparisonRule("segment", "Expansion vs Churn MRR", ("activity_type", "movement_type"), ("mrr", "amount")),
        ),
        trends=(
            TrendRule(("mrr", "recurring_revenue"), ("date", "month"), "Analyzing compound monthly growth rate of subscriptions"),
        ),
        risks=(
            RiskRule("churn_spike", "Elevated Subscriber Churn", "spike", metric_patterns=("churn", "is_churned"), threshold=0.05, label="Requires investigation", recommended_action="Initiate customer success outreach for accounts showing declining product activity."),
        ),
        recommendations=(
            RecommendationRule("customer_retention", "churn_rate", "high_churn", "Introduce annual contract incentives and proactive onboarding to curb early churn.", "Requires discounting annual upfront commitments."),
        ),
    ),

    # 59. Product Analytics
    DomainBlueprint(
        id="product_analytics",
        name="Product Analytics",
        description="Digital product usage, daily active users (DAU), monthly active users (MAU), feature adoption, and retention funnels.",
        keywords=("dau", "mau", "active_users", "feature", "event_name", "session_length", "stickiness", "funnel", "adoption", "user_journey", "onboarding_step"),
        alternative_domains=("SaaS and Subscription", "Web Analytics", "Gaming"),
        entities=(
            EntityRule("user", "Active Product User", ("user_id", "user_uuid", "account_id")),
            EntityRule("feature_event", "Product Event / Interaction", ("event_name", "event_id", "feature_id", "action")),
        ),
        kpis=(
            KpiRule("dau", "Daily Active Users (DAU)", "Unique active users recorded in daily product sessions", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("user_id", "user_uuid"), formula="count_distinct", format="number", business_meaning="Daily engaged user volume"),
            KpiRule("avg_session_length", "Average Session Duration", "Mean time users spend actively engaged in the product", ("numeric",), metric_patterns=("session_duration", "duration_seconds", "time_spent"), formula="mean", format="duration", business_meaning="Product engagement depth"),
        ),
        charts=(
            ChartRule("events_by_feature", "Interactions by Feature", "bar", dimension_patterns=("event_name", "feature_id", "screen"), metric_patterns=("event_id", "user_id"), aggregation="count", business_question="Which product features receive the highest engagement?"),
        ),
        comparisons=(
            ComparisonRule("category", "Engagement by User Segment", ("user_tier", "role", "cohort"), ("session_duration", "events")),
        ),
        trends=(
            TrendRule(("user_id", "event_id"), ("date", "day"), "Monitoring daily user active trends and stickiness"),
        ),
        risks=(
            RiskRule("dau_drop", "Sudden DAU Contraction", "drop", metric_patterns=("user_id", "active_users"), threshold=0.25, label="Potential anomaly", recommended_action="Check for client application crashes or recent breaking UI changes."),
        ),
        recommendations=(
            RecommendationRule("product_optimization", "dau", "feature_usage", "Simplify onboarding navigation to drive higher adoption for underutilized core features.", "Dependent on UX redesign testing."),
        ),
    ),

    # 60. Web Analytics
    DomainBlueprint(
        id="web_analytics",
        name="Web Analytics",
        description="Website visitors, pageviews, bounce rate, traffic sources, referrers, UTM campaigns, and browser sessions.",
        keywords=("pageview", "bounce_rate", "traffic_source", "referrer", "utm_source", "utm_campaign", "session_id", "landing_page", "exit_rate", "browser", "device_category"),
        alternative_domains=("Product Analytics", "Marketing and Advertising", "Social Media"),
        entities=(
            EntityRule("visitor", "Website Visitor", ("visitor_id", "client_id", "cookie_id")),
            EntityRule("web_session", "Web Browsing Session", ("session_id", "visit_id")),
            EntityRule("page", "Webpage / URL", ("page_url", "page_path", "landing_page")),
        ),
        kpis=(
            KpiRule("total_pageviews", "Total Pageviews", "Total web pages viewed across sessions", ("numeric", "categorical"), metric_patterns=("pageviews", "views"), dimension_patterns=("page_url", "session_id"), formula="sum", format="number", business_meaning="Gross digital content consumption"),
            KpiRule("avg_bounce_rate", "Average Bounce Rate", "Percentage of single-page visits where visitor exited without interaction", ("numeric",), metric_patterns=("bounce_rate", "is_bounce"), formula="mean", format="percentage", business_meaning="Landing page relevance and engagement effectiveness"),
        ),
        charts=(
            ChartRule("traffic_by_source", "Sessions by Traffic Channel", "pie", dimension_patterns=("traffic_source", "channel", "medium"), metric_patterns=("session_id", "pageviews"), aggregation="count", business_question="Which marketing channels drive the majority of website visitors?"),
            ChartRule("top_landing_pages", "Top Landing Pages by Traffic", "bar", dimension_patterns=("landing_page", "page_path"), metric_patterns=("session_id", "visits"), aggregation="count", business_question="Which entry pages attract the highest visitor volume?"),
        ),
        comparisons=(
            ComparisonRule("category", "Bounce Rates across Traffic Sources", ("traffic_source", "medium"), ("bounce_rate", "session_id")),
        ),
        trends=(
            TrendRule(("session_id", "pageviews"), ("date", "day"), "Evaluating visitor traffic patterns across days and marketing campaigns"),
        ),
        risks=(
            RiskRule("high_bounce_landing", "Elevated Landing Page Bounce Rate", "spike", metric_patterns=("bounce_rate", "is_bounce"), threshold=0.75, label="Requires investigation", recommended_action="Audit landing page load performance and keyword messaging alignment."),
        ),
        recommendations=(
            RecommendationRule("marketing_optimization", "avg_bounce_rate", "high_bounce", "Optimize page load speed and call-to-action visibility on top entry pages.", "Assumes page content is indexed correctly."),
        ),
    ),

    # 61. Cybersecurity
    DomainBlueprint(
        id="cybersecurity",
        name="Cybersecurity",
        description="Security event logs, CVE vulnerabilities, firewall alerts, intrusion attempts, malware scans, and SOC incidents.",
        keywords=("cybersecurity", "cve", "vulnerability", "firewall", "intrusion", "malware", "soc", "siem", "threat", "ip_source", "cve_id", "exploit", "auth_failure", "endpoint"),
        alternative_domains=("IT and Software", "Network and Infrastructure Monitoring", "Fraud and Anomaly Detection"),
        entities=(
            EntityRule("security_incident", "Security Incident / Event", ("incident_id", "alert_id", "event_id")),
            EntityRule("host_asset", "Targeted Asset / Host", ("host_name", "ip_address", "endpoint_id", "server_ip")),
        ),
        kpis=(
            KpiRule("critical_vulnerabilities", "Critical Vulnerabilities Detected", "Count of high or critical CVE security vulnerabilities open", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("cve_id", "vulnerability_id"), formula="count_distinct", format="number", business_meaning="Critical security exposure surface"),
            KpiRule("mttd", "Mean Time to Detect (MTTD)", "Average hours to identify and log a security incident", ("numeric",), metric_patterns=("detection_time", "mttd", "time_to_detect"), formula="mean", format="duration", business_meaning="Security Operations Center response agility"),
        ),
        charts=(
            ChartRule("threats_by_type", "Security Alerts by Threat Category", "bar", dimension_patterns=("threat_type", "attack_vector", "category"), metric_patterns=("incident_id", "alert_id"), aggregation="count", business_question="What are the most common cyber attack vectors encountered?"),
        ),
        comparisons=(
            ComparisonRule("category", "Incident Severity across Network Zones", ("network_zone", "environment"), ("incident_id", "severity")),
        ),
        trends=(
            TrendRule(("incident_id", "alert_id"), ("date", "timestamp"), "Detecting attack surges and scanning activity across time"),
        ),
        risks=(
            RiskRule("brute_force_spike", "Authentication Failure Surge", "spike", metric_patterns=("failed_logins", "auth_failure"), threshold=100.0, label="Requires investigation", recommended_action="Enforce IP rate limiting and quarantine affected user credentials."),
        ),
        recommendations=(
            RecommendationRule("risk_mitigation", "critical_vulnerabilities", "unpatched_cves", "Prioritize emergency patch deployment for internet-facing critical CVEs.", "Requires scheduled maintenance window."),
        ),
    ),

    # 68. IoT and Sensor Data
    DomainBlueprint(
        id="iot_sensor",
        name="IoT and Sensor Data",
        description="Connected telemetry devices, physical sensor streams, temperature, pressure, vibration, battery, and firmware status.",
        keywords=("sensor", "telemetry", "iot", "temperature", "pressure", "humidity", "vibration", "voltage", "battery_level", "sensor_id", "firmware", "device_id", "reading"),
        alternative_domains=("Network and Infrastructure Monitoring", "Manufacturing", "Energy and Utilities"),
        entities=(
            EntityRule("sensor_device", "IoT Sensor / Device", ("device_id", "sensor_id", "node_id", "mac_address")),
            EntityRule("reading", "Telemetry Reading", ("reading_id", "timestamp", "log_id")),
        ),
        kpis=(
            KpiRule("avg_reading_value", "Average Telemetry Reading", "Mean measurement value recorded across active sensors", ("numeric",), metric_patterns=("value", "reading", "temperature", "pressure"), formula="mean", format="number", business_meaning="Central baseline telemetry state"),
            KpiRule("threshold_violations", "Sensor Threshold Violations", "Count of telemetry readings exceeding safety boundaries", ("numeric", "boolean"), metric_patterns=("is_violation", "exceeded", "alert"), formula="sum", format="number", business_meaning="Physical operating anomaly count"),
        ),
        charts=(
            ChartRule("telemetry_over_time", "Telemetry Stream Over Time", "line", dimension_patterns=("timestamp", "time", "date"), metric_patterns=("value", "reading", "temperature"), aggregation="mean", business_question="How are physical sensor values fluctuating over time?"),
            ChartRule("reading_distribution", "Sensor Value Distribution", "histogram", metric_patterns=("value", "reading", "vibration"), aggregation="count", business_question="What is the distribution and dispersion of sensor readings?"),
        ),
        comparisons=(
            ComparisonRule("category", "Sensor Readings across Device Nodes", ("device_id", "sensor_type"), ("value", "reading")),
        ),
        trends=(
            TrendRule(("value", "reading"), ("timestamp", "time"), "Detecting sensor drift and thermal/pressure degradation trends"),
        ),
        risks=(
            RiskRule("sensor_outlier", "Physical Telemetry Outlier", "outlier", metric_patterns=("value", "reading"), threshold=3.0, label="Requires investigation", recommended_action="Inspect sensor calibration and physical hardware connections."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "avg_reading_value", "sensor_drift", "Recalibrate edge IoT sensor probes exhibiting significant baseline drift.", "Requires physical field technician dispatch."),
        ),
    ),

    # 69. Network and Infrastructure Monitoring
    DomainBlueprint(
        id="network_infrastructure",
        name="Network and Infrastructure Monitoring",
        description="Network bandwidth, server latency, CPU/memory utilization, packet loss, uptime, DNS queries, and router throughput.",
        keywords=("latency", "bandwidth", "cpu_utilization", "memory_usage", "packet_loss", "ping", "throughput", "router", "switch", "interface", "uptime", "server_load"),
        alternative_domains=("IoT and Sensor Data", "Cybersecurity", "IT and Software"),
        entities=(
            EntityRule("network_node", "Network Node / Server", ("node_id", "server_name", "host", "router_id", "interface")),
        ),
        kpis=(
            KpiRule("avg_latency", "Average Network Latency (ms)", "Mean round-trip network response latency", ("numeric",), metric_patterns=("latency", "ping_ms", "rtt"), formula="mean", format="duration", business_meaning="Network transmission responsiveness"),
            KpiRule("packet_loss_rate", "Packet Loss Ratio", "Percentage of transmitted network packets dropped", ("numeric",), metric_patterns=("packet_loss", "drop_rate"), formula="mean", format="percentage", business_meaning="Network transmission integrity"),
            KpiRule("avg_cpu_utilization", "Average CPU Utilization", "Mean server CPU load percentage across infrastructure", ("numeric",), metric_patterns=("cpu", "cpu_pct", "cpu_utilization"), formula="mean", format="percentage", business_meaning="Compute resource capacity consumption"),
        ),
        charts=(
            ChartRule("latency_trend", "Network Latency Over Time", "line", dimension_patterns=("timestamp", "time", "date"), metric_patterns=("latency", "ping_ms"), aggregation="mean", business_question="Are network latencies experiencing intermittent latency spikes?"),
            ChartRule("cpu_by_server", "CPU Utilization by Server Node", "bar", dimension_patterns=("server_name", "host", "node_id"), metric_patterns=("cpu", "cpu_pct"), aggregation="mean", business_question="Which server instances are running at near-capacity load?"),
        ),
        comparisons=(
            ComparisonRule("category", "Latency Comparison across Data Centers", ("datacenter", "region", "zone"), ("latency", "packet_loss")),
        ),
        trends=(
            TrendRule(("cpu", "latency"), ("timestamp", "time"), "Forecasting infrastructure saturation and peak load periods"),
        ),
        risks=(
            RiskRule("packet_loss_surge", "Packet Loss Anomaly", "spike", metric_patterns=("packet_loss", "drop_rate"), threshold=0.05, label="Requires investigation", recommended_action="Inspect physical switch interfaces and upstream transit provider connectivity."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "avg_cpu_utilization", "high_cpu", "Auto-scale server compute instances during recurring high-utilization hours.", "Subject to cloud infrastructure provisioning budgets."),
        ),
    ),
]
