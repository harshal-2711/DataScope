"""Finance, Banking, Insurance, and Risk domain blueprints (Domains 11, 12, 13, 14, 15, 16, 17, 56)."""
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
    # 11. Finance
    DomainBlueprint(
        id="finance",
        name="Finance",
        description="General corporate finance, financial statements, cash flows, ledger entries, and accounting.",
        keywords=("finance", "accounting", "ledger", "debit", "credit", "asset", "liability", "equity", "cash_flow", "operating_cash", "ebitda", "gross_margin", "balance_sheet"),
        alternative_domains=("Banking", "Investment and Stock Market", "General Business Analytics"),
        entities=(
            EntityRule("account", "General Ledger Account", ("account", "gl_account", "account_code", "account_name")),
            EntityRule("entry", "Journal Entry", ("entry_id", "journal_id", "voucher_no", "doc_number")),
        ),
        kpis=(
            KpiRule("total_debits", "Total Debits", "Sum of all debit journal entries", ("numeric",), metric_patterns=("debit", "debit_amount", "dr"), formula="sum", format="currency", business_meaning="Total debit transaction volume"),
            KpiRule("total_credits", "Total Credits", "Sum of all credit journal entries", ("numeric",), metric_patterns=("credit", "credit_amount", "cr"), formula="sum", format="currency", business_meaning="Total credit transaction volume"),
            KpiRule("net_cash_flow", "Net Cash Flow / Income", "Net periodic movement of funds", ("numeric",), metric_patterns=("net_flow", "cash_flow", "net_amount", "net_income"), formula="sum", format="currency", business_meaning="Net liquidity generation"),
        ),
        charts=(
            ChartRule("cash_flow_trend", "Cash Flow Over Time", "line", dimension_patterns=("date", "period", "month"), metric_patterns=("net_flow", "cash_flow", "amount"), aggregation="sum", business_question="Is liquidity increasing or contracting over time?"),
            ChartRule("expenses_by_account", "Expenditure by Account Category", "bar", dimension_patterns=("account", "category"), metric_patterns=("debit", "amount", "expense"), aggregation="sum", business_question="Which ledger accounts incur the largest expenses?"),
        ),
        comparisons=(
            ComparisonRule("time", "Quarter-over-Quarter Financial Performance", ("period", "quarter", "year"), ("amount", "net_income")),
        ),
        trends=(
            TrendRule(("amount", "net_flow"), ("date", "period"), "Tracking recurring financial inflows and outflows"),
        ),
        risks=(
            RiskRule("unbalanced_entries", "Abnormal Entry Outliers", "outlier", metric_patterns=("amount", "debit", "credit"), threshold=3.5, label="Requires investigation", recommended_action="Review high-magnitude journal adjustments with audit trails."),
        ),
        recommendations=(
            RecommendationRule("cost_reduction", "total_debits", "high_expenses", "Scrutinize top discretionary expenditure ledger items for budgetary consolidation.", "Requires detailed sub-ledger breakdown."),
        ),
    ),

    # 12. Banking
    DomainBlueprint(
        id="banking",
        name="Banking",
        description="Retail and commercial banking, deposits, withdrawals, loan balances, interest rates, and branch performance.",
        keywords=("banking", "bank", "deposit", "withdrawal", "account_balance", "loan_amount", "interest_rate", "branch", "teller", "overdraft", "savings", "checking"),
        alternative_domains=("Finance", "FinTech and Payments", "Financial Risk and Credit"),
        entities=(
            EntityRule("bank_account", "Bank Account", ("account_number", "acc_no", "account_id", "iban")),
            EntityRule("branch", "Bank Branch", ("branch_id", "branch_name", "branch_code", "city")),
            EntityRule("customer", "Banking Customer", ("customer_id", "cif", "client_id")),
        ),
        kpis=(
            KpiRule("total_deposits", "Total Deposit Balance", "Sum of all customer balances on deposit", ("numeric",), metric_patterns=("deposit", "balance", "account_balance"), formula="sum", format="currency", business_meaning="Total deposit liability base of the institution"),
            KpiRule("total_loans", "Total Loans Outstanding", "Total principal balances outstanding across customer loans", ("numeric",), metric_patterns=("loan_amount", "principal", "outstanding_balance"), formula="sum", format="currency", business_meaning="Total credit asset exposure"),
            KpiRule("avg_account_balance", "Average Customer Balance", "Mean funds maintained per banking customer", ("numeric",), metric_patterns=("balance", "account_balance"), formula="mean", format="currency", business_meaning="Customer relationship depth"),
        ),
        charts=(
            ChartRule("deposits_by_branch", "Deposits by Branch", "bar", dimension_patterns=("branch", "city", "region"), metric_patterns=("deposit", "balance"), aggregation="sum", business_question="Which bank branches hold the largest deposit reserves?"),
            ChartRule("balance_distribution", "Customer Balance Distribution", "histogram", metric_patterns=("balance", "account_balance"), aggregation="count", business_question="What is the distribution of wealth across the customer deposit base?"),
        ),
        comparisons=(
            ComparisonRule("category", "Branch Deposit & Loan Ratios", ("branch", "region"), ("balance", "loan_amount")),
        ),
        trends=(
            TrendRule(("balance", "deposit"), ("date", "month"), "Monitoring growth of core customer deposits over time"),
        ),
        risks=(
            RiskRule("rapid_withdrawal", "Unusual Account Outflow", "drop", metric_patterns=("balance", "withdrawal"), threshold=0.4, label="Requires investigation", recommended_action="Monitor high-velocity balance declines for liquidity and deposit flight risk."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "total_deposits", "high_deposits", "Cross-sell wealth management products to high-balance deposit accounts.", "Dependent on customer risk profile."),
        ),
    ),

    # 13. Insurance
    DomainBlueprint(
        id="insurance",
        name="Insurance",
        description="Underwriting, insurance policies, policyholders, premiums, claims, loss ratios, and coverage limits.",
        keywords=("insurance", "policy", "premium", "claim", "claim_amount", "deductible", "underwriting", "loss_ratio", "policyholder", "coverage", "actuarial", "claim_status"),
        alternative_domains=("Finance", "Healthcare", "Financial Risk and Credit"),
        entities=(
            EntityRule("policy", "Insurance Policy", ("policy_id", "policy_number", "policy_no")),
            EntityRule("claim", "Insurance Claim", ("claim_id", "claim_number", "claim_no")),
            EntityRule("policyholder", "Policyholder", ("policyholder_id", "insured_id", "customer_id")),
        ),
        kpis=(
            KpiRule("written_premium", "Total Gross Written Premium", "Sum of all premiums collected across issued policies", ("numeric",), metric_patterns=("premium", "written_premium", "premium_amount"), formula="sum", format="currency", business_meaning="Top-line underwriting revenue"),
            KpiRule("total_claims_paid", "Total Claims Paid / Incurred", "Total monetary amount disbursed or reserved for claims", ("numeric",), metric_patterns=("claim_amount", "paid_amount", "incurred_claims"), formula="sum", format="currency", business_meaning="Gross underwriting loss expense"),
            KpiRule("loss_ratio", "Underwriting Loss Ratio", "Ratio of claims incurred to premiums earned", ("numeric",), metric_patterns=("loss_ratio", "claim_ratio"), formula="mean", format="percentage", business_meaning="Underwriting profitability efficiency"),
            KpiRule("claim_frequency", "Average Claim Amount", "Average monetary payout per filed insurance claim", ("numeric",), metric_patterns=("claim_amount", "payout"), formula="mean", format="currency", business_meaning="Average claim severity"),
        ),
        charts=(
            ChartRule("claims_by_coverage", "Claims Paid by Coverage Line", "bar", dimension_patterns=("coverage", "policy_type", "line_of_business"), metric_patterns=("claim_amount", "paid_amount"), aggregation="sum", business_question="Which insurance coverage lines experience the heaviest claim payouts?"),
            ChartRule("loss_ratio_by_state", "Loss Ratio by Geographic Region", "bar", dimension_patterns=("state", "region", "territory"), metric_patterns=("loss_ratio", "claim_amount"), aggregation="mean", business_question="Are specific territories unprofitable from a claims perspective?"),
        ),
        comparisons=(
            ComparisonRule("category", "Premium vs Claims by Policy Type", ("policy_type", "coverage"), ("premium", "claim_amount")),
        ),
        trends=(
            TrendRule(("claim_amount", "premium"), ("date", "accident_date", "policy_start"), "Analyzing claims frequency patterns over seasonal horizons"),
        ),
        risks=(
            RiskRule("claim_severity_spike", "High Claim Severity Anomaly", "outlier", metric_patterns=("claim_amount", "payout"), threshold=3.5, label="Requires investigation", recommended_action="Perform detailed claims audit on top 1% payout outliers for potential leakage or fraud."),
        ),
        recommendations=(
            RecommendationRule("risk_mitigation", "loss_ratio", "high_loss_ratio", "Recalibrate underwriting criteria and deductibles for lines exceeding target loss ratios.", "Subject to state insurance commissioner rate approval."),
        ),
    ),

    # 14. Investment and Stock Market
    DomainBlueprint(
        id="investment_stock",
        name="Investment and Stock Market",
        description="Equities, portfolios, trading volume, tickers, asset prices, yields, returns, and market volatility.",
        keywords=("stock", "ticker", "shares", "portfolio", "dividend", "yield", "volatility", "trading_volume", "open_price", "close_price", "high_price", "low_price", "pe_ratio", "nav"),
        alternative_domains=("Finance", "FinTech and Payments", "Banking"),
        entities=(
            EntityRule("security", "Financial Security / Ticker", ("ticker", "symbol", "security", "asset_id", "isin")),
            EntityRule("portfolio", "Investment Portfolio", ("portfolio_id", "fund_id", "strategy")),
        ),
        kpis=(
            KpiRule("total_market_value", "Total Portfolio Market Value", "Sum of current position values across portfolio", ("numeric",), metric_patterns=("market_value", "total_value", "position_value"), formula="sum", format="currency", business_meaning="Aggregate asset under management (AUM)"),
            KpiRule("avg_return", "Average Return / Yield", "Mean periodic return percentage across holdings", ("numeric",), metric_patterns=("return", "yield", "roi", "gain_pct"), formula="mean", format="percentage", business_meaning="Overall investment performance yield"),
            KpiRule("total_volume_traded", "Total Volume Traded", "Aggregate share/contract volume exchanged", ("numeric",), metric_patterns=("volume", "trading_volume", "shares_traded"), formula="sum", format="number", business_meaning="Market liquidity depth"),
        ),
        charts=(
            ChartRule("price_history", "Asset Price Movement Over Time", "line", dimension_patterns=("date", "timestamp", "trading_day"), metric_patterns=("close", "price", "nav"), aggregation="mean", business_question="How have asset closing prices moved across trading dates?"),
            ChartRule("holdings_breakdown", "Portfolio Allocation by Asset Class", "pie", dimension_patterns=("asset_class", "sector", "industry"), metric_patterns=("market_value", "weight"), aggregation="sum", business_question="What is the sector diversification of investment holdings?"),
        ),
        comparisons=(
            ComparisonRule("category", "Returns Comparison across Asset Classes", ("asset_class", "sector"), ("return", "yield")),
        ),
        trends=(
            TrendRule(("close", "price"), ("date", "trading_day"), "Measuring price momentum and moving averages"),
        ),
        risks=(
            RiskRule("drawdown_risk", "Sharp Valuation Drawdown", "drop", metric_patterns=("return", "close", "price"), threshold=0.15, label="Requires investigation", recommended_action="Assess stop-loss thresholds and sector concentration hedges."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "avg_return", "underperforming_holdings", "Rebalance capital away from persistent negative-alpha positions into index benchmarks.", "Subject to transaction costs and capital gains taxes."),
        ),
    ),

    # 15. FinTech and Payments
    DomainBlueprint(
        id="fintech_payments",
        name="FinTech and Payments",
        description="Digital wallets, payment gateways, interchange fees, authorizations, settlements, chargebacks, and rails.",
        keywords=("fintech", "payment", "gateway", "interchange", "chargeback", "auth_rate", "settlement", "merchant", "processor", "pos_terminal", "wallet", "ach", "wire"),
        alternative_domains=("Banking", "Finance", "Fraud and Anomaly Detection"),
        entities=(
            EntityRule("payment_tx", "Payment Transaction", ("transaction_id", "payment_id", "charge_id")),
            EntityRule("merchant", "Merchant Account", ("merchant_id", "seller_id", "mid")),
        ),
        kpis=(
            KpiRule("payment_volume", "Total Payment Volume (TPV)", "Gross monetary volume processed across payment rails", ("numeric",), metric_patterns=("amount", "volume", "tpv", "gross_amount"), formula="sum", format="currency", business_meaning="Total platform processing throughput"),
            KpiRule("authorization_rate", "Payment Authorization Rate", "Proportion of initiated payment authorizations approved", ("numeric",), metric_patterns=("auth_rate", "approval_rate", "is_authorized"), formula="mean", format="percentage", business_meaning="Payment checkout conversion efficiency"),
            KpiRule("chargeback_rate", "Chargeback Ratio", "Percentage of processed transactions resulting in a dispute", ("numeric",), metric_patterns=("chargeback", "dispute_rate"), formula="mean", format="percentage", business_meaning="Fraud and dispute vulnerability metric"),
        ),
        charts=(
            ChartRule("tpv_by_method", "Payment Volume by Payment Method", "pie", dimension_patterns=("payment_method", "card_brand", "rail"), metric_patterns=("amount", "tpv"), aggregation="sum", business_question="What payment methods (cards, wallets, ACH) dominate checkout?"),
        ),
        comparisons=(
            ComparisonRule("category", "Approval Rates by Card Brand / Rail", ("payment_method", "card_brand"), ("auth_rate", "is_authorized")),
        ),
        trends=(
            TrendRule(("amount", "tpv"), ("date", "created_at"), "Monitoring daily processing volume and peak payment windows"),
        ),
        risks=(
            RiskRule("chargeback_surge", "Dispute / Chargeback Spike", "spike", metric_patterns=("chargeback", "dispute"), threshold=0.01, label="Requires investigation", recommended_action="Verify merchant compliance with card network dispute monitoring programs."),
        ),
        recommendations=(
            RecommendationRule("cost_reduction", "authorization_rate", "low_auth", "Implement intelligent transaction routing to primary acquirers to boost approval rates.", "Requires multi-acquirer integration."),
        ),
    ),

    # 16. Financial Risk and Credit
    DomainBlueprint(
        id="credit_risk",
        name="Financial Risk and Credit",
        description="Credit scoring, default rates, probability of default (PD), debt-to-income (DTI), loan delinquency, and underwriting.",
        keywords=("credit_score", "credit_risk", "default", "delinquency", "dti", "ltv", "pd", "lgd", "ead", "collateral", "fico", "overdue", "bad_debt", "provision"),
        alternative_domains=("Banking", "Finance", "Fraud and Anomaly Detection"),
        entities=(
            EntityRule("borrower", "Credit Borrower", ("borrower_id", "applicant_id", "customer_id")),
            EntityRule("loan", "Credit Facility / Loan", ("loan_id", "credit_id", "facility_id")),
        ),
        kpis=(
            KpiRule("default_rate", "Portfolio Default Rate", "Percentage of loan balance or accounts classified in default", ("numeric",), metric_patterns=("is_default", "default_rate", "delinquent"), formula="mean", format="percentage", business_meaning="Credit asset impairment frequency"),
            KpiRule("avg_credit_score", "Average Borrower Credit Score", "Mean credit bureau score of the borrower base", ("numeric",), metric_patterns=("credit_score", "fico", "bureau_score"), formula="mean", format="number", business_meaning="Underwriting creditworthiness profile"),
            KpiRule("total_delinquent_balance", "Delinquent Exposure Balance", "Total monetary amount overdue beyond 30+ days", ("numeric",), metric_patterns=("overdue_amount", "delinquent_balance", "past_due"), formula="sum", format="currency", business_meaning="Capital at immediate risk of impairment"),
        ),
        charts=(
            ChartRule("default_by_score_tier", "Default Rate by Credit Score Tier", "bar", dimension_patterns=("credit_tier", "score_bucket", "risk_rating"), metric_patterns=("is_default", "default_rate"), aggregation="mean", business_question="How strongly does credit score segment historical default rates?"),
            ChartRule("dti_vs_delinquency", "Debt-to-Income vs Delinquency Distribution", "scatter", metric_patterns=("dti", "debt_to_income"), dimension_patterns=(), aggregation="sum", business_question="Is high debt-to-income correlated with loan delinquency?"),
        ),
        comparisons=(
            ComparisonRule("category", "Delinquency Rates by Loan Purpose", ("loan_purpose", "product_type"), ("is_default", "delinquent_balance")),
        ),
        trends=(
            TrendRule(("is_default", "past_due"), ("origination_date", "date"), "Tracking vintage default curves across origination cohorts"),
        ),
        risks=(
            RiskRule("delinquency_surge", "Vintage Delinquency Surge", "spike", metric_patterns=("is_default", "delinquent_balance"), threshold=0.05, label="Requires investigation", recommended_action="Tighten debt-to-income and minimum credit score cutoffs on new originations."),
        ),
        recommendations=(
            RecommendationRule("risk_mitigation", "default_rate", "high_default", "Recalibrate credit risk scorecards to reduce portfolio exposure to high-DTI applicants.", "May reduce overall loan origination volume."),
        ),
    ),

    # 17. Fraud and Anomaly Detection
    DomainBlueprint(
        id="fraud_detection",
        name="Fraud and Anomaly Detection",
        description="Suspicious transactions, fraud scores, velocity checks, identity theft, unauthorized charges, and anti-money laundering.",
        keywords=("fraud", "suspicious", "aml", "sar", "flagged", "blacklist", "anomaly_score", "fraud_score", "velocity_check", "ip_risk", "unauthorized"),
        alternative_domains=("FinTech and Payments", "Cybersecurity", "Banking"),
        entities=(
            EntityRule("flagged_event", "Flagged Event / Case", ("case_id", "alert_id", "event_id", "transaction_id")),
            EntityRule("subject", "Investigated Subject / Device", ("user_id", "device_fingerprint", "account_id")),
        ),
        kpis=(
            KpiRule("fraud_rate", "Fraud Incident Rate", "Proportion of total events confirmed or flagged as fraudulent", ("numeric", "boolean"), metric_patterns=("is_fraud", "fraud_flag", "is_suspicious"), formula="mean", format="percentage", business_meaning="Systemic fraud vulnerability frequency"),
            KpiRule("fraud_loss_amount", "Total Flagged / Fraud Exposure", "Monetary sum of transactions identified as fraudulent", ("numeric",), metric_patterns=("fraud_amount", "loss_amount", "amount"), formula="sum", format="currency", business_meaning="Gross monetary loss from fraudulent actions"),
            KpiRule("false_positive_rate", "Flagged Review Volume", "Total number of transactions queued for manual fraud review", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("case_id", "alert_id"), formula="count_distinct", format="number", business_meaning="Operational burden of risk review"),
        ),
        charts=(
            ChartRule("fraud_by_rule", "Alerts Triggered by Detection Rule", "bar", dimension_patterns=("rule_name", "risk_factor", "alert_type"), metric_patterns=("case_id", "is_fraud"), aggregation="count", business_question="Which detection rules generate the highest volume of alerts?"),
        ),
        comparisons=(
            ComparisonRule("category", "Fraud Rates by Channel or Device", ("channel", "device_type", "country"), ("is_fraud", "fraud_score")),
        ),
        trends=(
            TrendRule(("is_fraud", "case_id"), ("timestamp", "date"), "Monitoring fraud attack vectors and surge patterns over time"),
        ),
        risks=(
            RiskRule("fraud_surge", "Coordinated Attack Wave", "spike", metric_patterns=("is_fraud", "fraud_score"), threshold=0.03, label="Requires investigation", recommended_action="Implement step-up multi-factor authentication for affected channels."),
        ),
        recommendations=(
            RecommendationRule("risk_mitigation", "fraud_rate", "high_fraud", "Deploy automated velocity rule triggers to decline rapid-fire transactions from identical fingerprints.", "Care must be taken to minimize false positive declines."),
        ),
    ),

    # 56. Government Finance and Public Finance
    DomainBlueprint(
        id="gov_finance",
        name="Government Finance and Public Finance",
        description="Public sector budgeting, tax revenues, municipal bonds, government spending, appropriations, and fiscal deficit.",
        keywords=("public_finance", "government_finance", "appropriation", "treasury", "tax_revenue", "fiscal", "deficit", "municipal", "bond", "public_expenditure", "civic_budget"),
        alternative_domains=("Finance", "Government and Public Data", "Economics and Macroeconomics"),
        entities=(
            EntityRule("appropriation_item", "Budget Appropriation Item", ("line_item", "appropriation_id", "program_code")),
            EntityRule("agency", "Public Agency / Department", ("agency", "ministry", "department", "municipality")),
        ),
        kpis=(
            KpiRule("allocated_budget", "Total Allocated Budget", "Total statutory budget appropriations authorized", ("numeric",), metric_patterns=("budget", "allocated", "appropriation"), formula="sum", format="currency", business_meaning="Statutory fiscal spending ceiling"),
            KpiRule("actual_public_spend", "Actual Public Expenditure", "Total funds disbursed by public authorities", ("numeric",), metric_patterns=("actual_spend", "expenditure", "disbursed"), formula="sum", format="currency", business_meaning="Realized public expenditure"),
            KpiRule("tax_receipts", "Total Public Revenues Collected", "Aggregate revenues from civic taxes, duties, and fees", ("numeric",), metric_patterns=("tax_revenue", "receipts", "revenue"), formula="sum", format="currency", business_meaning="Fiscal revenues available for public finance"),
        ),
        charts=(
            ChartRule("spend_by_agency", "Expenditure by Public Agency", "bar", dimension_patterns=("agency", "department", "ministry"), metric_patterns=("actual_spend", "expenditure", "budget"), aggregation="sum", business_question="Which public departments receive the largest budget disbursements?"),
        ),
        comparisons=(
            ComparisonRule("category", "Budget vs Actual Spend by Program", ("program", "agency"), ("budget", "actual_spend")),
        ),
        trends=(
            TrendRule(("expenditure", "actual_spend"), ("fiscal_year", "quarter"), "Tracking multi-year public capital and operating spending"),
        ),
        risks=(
            RiskRule("budget_overrun", "Fiscal Appropriation Overrun", "spike", metric_patterns=("actual_spend", "expenditure"), threshold=1.1, label="Requires investigation", recommended_action="Audit agency discretionary contracts to prevent year-end deficit overruns."),
        ),
        recommendations=(
            RecommendationRule("process_optimization", "allocated_budget", "surplus_or_deficit", "Reallocate unused capital expenditure appropriations toward underfunded civic programs.", "Requires legislative or municipal council approval."),
        ),
    ),
]
