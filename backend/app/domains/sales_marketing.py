"""Sales, CRM, Marketing, and Social Media domain blueprints (Domains 9, 10, 35)."""
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
    # 9. Sales and CRM
    DomainBlueprint(
        id="sales_crm",
        name="Sales and CRM",
        description="B2B sales pipelines, CRM opportunities, deal stages, account executives, lead conversions, and win rates.",
        keywords=("deal", "lead", "opportunity", "crm", "pipeline", "stage", "win_rate", "sales_rep", "quota", "contract_value", "acv", "close_date", "lead_source"),
        alternative_domains=("Marketing and Advertising", "General Business Analytics", "SaaS and Subscription"),
        entities=(
            EntityRule("opportunity", "Sales Deal / Opportunity", ("deal_id", "opportunity_id", "deal_name")),
            EntityRule("sales_rep", "Sales Representative", ("rep_name", "sales_rep", "owner_id", "account_executive")),
            EntityRule("account", "Prospective Account / Company", ("company_name", "account_name", "prospect_id")),
        ),
        kpis=(
            KpiRule("pipeline_value", "Total Pipeline Value", "Sum of all open and closed deal values in pipeline", ("numeric",), metric_patterns=("deal_value", "amount", "contract_value", "acv"), formula="sum", format="currency", business_meaning="Gross sales opportunity value"),
            KpiRule("win_rate", "Sales Win Rate", "Percentage of closed opportunities won by sales reps", ("numeric", "boolean"), metric_patterns=("is_won", "win_loss", "won"), formula="mean", format="percentage", business_meaning="Sales conversion closing effectiveness"),
            KpiRule("avg_deal_size", "Average Deal Size", "Mean contract value per closed-won opportunity", ("numeric",), metric_patterns=("deal_value", "amount", "contract_value"), formula="mean", format="currency", business_meaning="Deal monetization magnitude"),
            KpiRule("total_leads", "Total Leads Generated", "Total prospective leads entered into the CRM pipeline", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("lead_id", "deal_id"), formula="count_distinct", format="number", business_meaning="Sales pipeline volume"),
        ),
        charts=(
            ChartRule("pipeline_by_stage", "Pipeline Value by Deal Stage", "bar", dimension_patterns=("stage", "pipeline_stage", "status"), metric_patterns=("deal_value", "amount"), aggregation="sum", business_question="How is prospective contract value distributed across sales stages?"),
            ChartRule("rep_performance", "Bookings by Sales Representative", "bar", dimension_patterns=("sales_rep", "rep_name", "owner"), metric_patterns=("deal_value", "amount"), aggregation="sum", business_question="Which sales executives drive the highest closed revenue?"),
            ChartRule("win_rate_by_source", "Win Rate by Lead Source", "bar", dimension_patterns=("lead_source", "channel"), metric_patterns=("is_won", "win_loss"), aggregation="mean", business_question="Which lead generation channels produce the highest win rates?"),
        ),
        comparisons=(
            ComparisonRule("category", "Sales Rep Win Rates Comparison", ("sales_rep", "team"), ("is_won", "deal_value")),
        ),
        trends=(
            TrendRule(("deal_value", "amount"), ("close_date", "date"), "Tracking quarterly sales quota attainment velocity"),
        ),
        risks=(
            RiskRule("stalled_deals", "Stalled Pipeline Concentration", "concentration", dimension_patterns=("stage", "sales_rep"), metric_patterns=("deal_value", "amount"), threshold=0.6, label="Requires investigation", recommended_action="Conduct pipeline scrub on opportunities lingering in early stages beyond standard sales cycle."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "win_rate", "low_win_rate", "Shift sales enablement focus toward qualifying leads from highest-converting sources.", "Relies on consistent lead attribution tagging."),
        ),
    ),

    # 10. Marketing and Advertising
    DomainBlueprint(
        id="marketing_ads",
        name="Marketing and Advertising",
        description="Paid ad campaigns, digital advertising, impressions, clicks, CTR, CPC, CPA, ROAS, and conversions.",
        keywords=("campaign", "ad_group", "creative", "impressions", "clicks", "ctr", "cpc", "roas", "cpa", "ad_spend", "conversion", "cost_per_click"),
        alternative_domains=("Web Analytics", "Social Media", "Sales and CRM"),
        entities=(
            EntityRule("campaign", "Marketing Campaign", ("campaign_id", "campaign_name", "ad_name", "ad_id")),
            EntityRule("ad_channel", "Advertising Channel / Platform", ("channel", "network", "platform", "source")),
        ),
        kpis=(
            KpiRule("total_ad_spend", "Total Ad Spend", "Total monetary budget expended on advertising", ("numeric",), metric_patterns=("spend", "ad_spend", "cost"), formula="sum", format="currency", business_meaning="Gross advertising investment"),
            KpiRule("total_impressions", "Total Ad Impressions", "Total impressions delivered to audiences", ("numeric",), metric_patterns=("impressions", "views"), formula="sum", format="number", business_meaning="Brand exposure and audience reach"),
            KpiRule("total_clicks", "Total Clicks", "Total engagement clicks generated by ads", ("numeric",), metric_patterns=("clicks", "click_count"), formula="sum", format="number", business_meaning="Initial audience traffic engagement"),
            KpiRule("avg_ctr", "Click-Through Rate (CTR)", "Average percentage of impressions resulting in a click", ("numeric",), metric_patterns=("ctr", "click_through_rate"), formula="mean", format="percentage", business_meaning="Ad creative resonance and engagement"),
            KpiRule("avg_cpc", "Average Cost Per Click (CPC)", "Mean monetary spend required to acquire each ad click", ("numeric",), metric_patterns=("cpc", "cost_per_click"), formula="mean", format="currency", business_meaning="Traffic acquisition efficiency"),
            KpiRule("roas", "Return on Ad Spend (ROAS)", "Revenue generated per dollar spent on advertising", ("numeric",), metric_patterns=("roas", "return_on_spend"), formula="mean", format="number", business_meaning="Advertising economic productivity"),
        ),
        charts=(
            ChartRule("spend_by_channel", "Ad Spend by Advertising Channel", "pie", dimension_patterns=("channel", "network", "platform"), metric_patterns=("spend", "cost"), aggregation="sum", business_question="How is marketing budget distributed across ad networks?"),
            ChartRule("conversions_by_campaign", "Conversions by Campaign", "bar", dimension_patterns=("campaign_name", "campaign_id"), metric_patterns=("conversions", "leads"), aggregation="sum", business_question="Which marketing campaigns drive the highest volume of conversions?"),
            ChartRule("cpc_vs_ctr", "CPC vs CTR Distribution", "scatter", metric_patterns=("cpc", "cost_per_click"), dimension_patterns=(), aggregation="sum", business_question="Are high-CTR creatives effectively lowering average CPC?"),
        ),
        comparisons=(
            ComparisonRule("category", "ROAS Comparison across Campaigns", ("campaign_name", "channel"), ("roas", "conversions")),
        ),
        trends=(
            TrendRule(("impressions", "clicks", "spend"), ("date", "day"), "Monitoring campaign scaling and ad spend velocity"),
        ),
        risks=(
            RiskRule("cpc_inflation", "CPC Cost Inflation", "spike", metric_patterns=("cpc", "cost_per_click"), threshold=2.0, label="Requires investigation", recommended_action="Audit keyword bidding thresholds and ad relevance scores to avoid overpaying for traffic."),
        ),
        recommendations=(
            RecommendationRule("cost_reduction", "roas", "low_roas_campaigns", "Pause ad sets with ROAS below break-even thresholds and reallocate budget to top performers.", "Assumes conversion tracking pixel attribution is fully accurate."),
        ),
    ),

    # 35. Social Media
    DomainBlueprint(
        id="social_media",
        name="Social Media",
        description="Social media engagement, posts, followers, likes, retweets, comments, shares, video views, and hashtag performance.",
        keywords=("social_media", "likes", "shares", "retweets", "followers", "post", "hashtag", "comments", "engagement_rate", "reach", "impressions", "handle"),
        alternative_domains=("Marketing and Advertising", "Media and Publishing", "Web Analytics"),
        entities=(
            EntityRule("social_post", "Social Media Post", ("post_id", "tweet_id", "content_id", "url")),
            EntityRule("account_handle", "Social Channel / Handle", ("handle", "profile", "account_name", "platform")),
        ),
        kpis=(
            KpiRule("total_engagements", "Total Engagements", "Sum of all likes, shares, comments, and reactions", ("numeric",), metric_patterns=("engagements", "likes", "shares", "reactions"), formula="sum", format="number", business_meaning="Aggregate audience interaction volume"),
            KpiRule("avg_engagement_rate", "Average Engagement Rate", "Mean engagement rate per post as a percentage of reach", ("numeric",), metric_patterns=("engagement_rate", "er"), formula="mean", format="percentage", business_meaning="Content resonance and audience affinity"),
            KpiRule("total_social_reach", "Total Social Reach", "Total unique audience members reached by posts", ("numeric",), metric_patterns=("reach", "impressions"), formula="sum", format="number", business_meaning="Gross brand organic and paid reach"),
        ),
        charts=(
            ChartRule("engagements_by_post_type", "Engagements by Content Format", "bar", dimension_patterns=("post_type", "media_type", "format"), metric_patterns=("engagements", "likes"), aggregation="sum", business_question="Do video, carousel, or image posts generate higher engagement?"),
        ),
        comparisons=(
            ComparisonRule("category", "Engagement Rates across Social Platforms", ("platform", "network"), ("engagement_rate", "likes")),
        ),
        trends=(
            TrendRule(("engagements", "reach"), ("post_date", "date"), "Tracking social follower growth and content momentum"),
        ),
        risks=(
            RiskRule("engagement_drop", "Social Engagement Contraction", "drop", metric_patterns=("engagements", "likes"), threshold=0.4, label="Unusual pattern detected", recommended_action="Review social algorithm updates and posting frequency."),
        ),
        recommendations=(
            RecommendationRule("marketing_optimization", "avg_engagement_rate", "top_content", "Increase publishing frequency of high-performing visual content formats.", "Dependent on creative production capacity."),
        ),
    ),
]
