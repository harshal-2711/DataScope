"""Commerce and Retail domain blueprints (Domains 1, 2, 3, 4, 5, 6, 7, 8, 73, 74)."""
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
    # 1. General Business Analytics
    DomainBlueprint(
        id="general_business",
        name="General Business Analytics",
        description="General enterprise and commercial business operations, revenue, expenses, and operational performance.",
        keywords=("business", "revenue", "expense", "profit", "margin", "cost", "sales", "quarter", "annual", "budget", "target", "department", "company"),
        alternative_domains=("Retail", "Finance", "Sales and CRM"),
        entities=(
            EntityRule("transaction", "Transaction / Record", ("trans_id", "transaction_id", "record_id", "id", "ref_no")),
            EntityRule("department", "Department / Business Unit", ("dept", "department", "business_unit", "division", "team")),
            EntityRule("customer", "Customer / Client", ("customer", "client", "account", "cust_id")),
        ),
        kpis=(
            KpiRule("total_revenue", "Total Revenue", "Sum of all revenue or income recorded", ("numeric",), metric_patterns=("revenue", "sales", "income", "amount", "total"), formula="sum", format="currency", business_meaning="Gross top-line revenue generated"),
            KpiRule("total_cost", "Total Cost / Expense", "Total expenses incurred across operations", ("numeric",), metric_patterns=("cost", "expense", "spend", "expenditure"), formula="sum", format="currency", business_meaning="Total operational expenditure"),
            KpiRule("net_profit", "Net Profit", "Net financial profit (Revenue - Cost if both exist, or profit column)", ("numeric",), metric_patterns=("profit", "net_income", "earnings"), formula="sum", format="currency", business_meaning="Bottom-line financial return"),
            KpiRule("avg_transaction_value", "Average Transaction Value", "Mean value per recorded transaction", ("numeric",), metric_patterns=("amount", "revenue", "sales", "value"), formula="mean", format="currency", business_meaning="Typical commercial value of a transaction"),
        ),
        charts=(
            ChartRule("rev_by_dept", "Revenue by Department / Division", "bar", dimension_patterns=("dept", "department", "division", "category"), metric_patterns=("revenue", "sales", "amount"), aggregation="sum", business_question="Which business units contribute the highest share of revenue?"),
            ChartRule("rev_over_time", "Revenue Trend Over Time", "line", dimension_patterns=("date", "month", "quarter", "year", "time"), metric_patterns=("revenue", "sales", "amount"), aggregation="sum", business_question="How is revenue trending across operating periods?"),
            ChartRule("cost_vs_rev", "Revenue vs Cost Distribution", "scatter", metric_patterns=("revenue", "sales"), dimension_patterns=(), aggregation="sum", business_question="Is there a strong correlation between operational cost and revenue generation?"),
        ),
        comparisons=(
            ComparisonRule("category", "Revenue Comparison across Departments", ("dept", "department", "division"), ("revenue", "sales", "amount")),
            ComparisonRule("time", "Period-over-Period Performance", ("date", "month", "quarter"), ("revenue", "sales")),
        ),
        trends=(
            TrendRule(("revenue", "sales"), ("date", "month", "quarter"), "Tracking overall business growth or decline across reporting intervals"),
        ),
        risks=(
            RiskRule("cost_outlier", "Cost Anomaly", "outlier", metric_patterns=("cost", "expense", "amount", "spend"), threshold=3.0, label="Potential anomaly", recommended_action="Audit top expense line items for unapproved or abnormal disbursements."),
            RiskRule("rev_concentration", "Revenue Concentration", "concentration", dimension_patterns=("customer", "dept", "product", "category"), metric_patterns=("revenue", "sales", "amount"), threshold=0.5, label="Unusual pattern detected", recommended_action="Evaluate dependency on a small number of top contributors."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "total_revenue", "positive_trend", "Double down on top-performing departments with increased resource allocation.", "Relies on historical department sales consistency."),
            RecommendationRule("cost_reduction", "total_cost", "high_variance", "Implement spend controls across the highest-variance cost centers.", "Assumes cost line items are accurately categorized."),
        ),
    ),

    # 2. Retail
    DomainBlueprint(
        id="retail",
        name="Retail",
        description="Brick-and-mortar and multi-channel retail operations, stores, merchandise, and retail transactions.",
        keywords=("store", "retail", "pos", "sku", "item", "merchandise", "register", "cashier", "aisle", "barcode", "discount", "receipt"),
        alternative_domains=("E-commerce", "FMCG", "Grocery", "Retail Operations"),
        entities=(
            EntityRule("store", "Retail Store", ("store", "store_id", "shop", "outlet", "branch", "location")),
            EntityRule("product", "Product / SKU", ("product", "sku", "item", "barcode", "merchandise")),
            EntityRule("cashier", "Cashier / Staff", ("cashier", "staff", "associate", "employee")),
        ),
        kpis=(
            KpiRule("retail_sales", "Total Store Sales", "Total retail sales generated across all store locations", ("numeric",), metric_patterns=("sales", "revenue", "amount", "total"), formula="sum", format="currency", business_meaning="Total store retail receipts"),
            KpiRule("units_sold", "Total Units Sold", "Total physical quantity of items sold", ("numeric",), metric_patterns=("quantity", "units", "qty", "items_sold"), formula="sum", format="number", business_meaning="Total physical volume moved"),
            KpiRule("avg_basket_size", "Average Units per Basket", "Average quantity of items purchased per retail transaction", ("numeric",), metric_patterns=("quantity", "qty", "items"), formula="mean", format="number", business_meaning="Depth of shopping basket"),
            KpiRule("total_discounts", "Total Discounts Given", "Total monetary discount extended to retail shoppers", ("numeric",), metric_patterns=("discount", "rebate", "mark_down"), formula="sum", format="currency", business_meaning="Gross markdown and promotional expenditure"),
        ),
        charts=(
            ChartRule("sales_by_store", "Sales by Store Location", "bar", dimension_patterns=("store", "outlet", "location", "branch"), metric_patterns=("sales", "revenue", "total"), aggregation="sum", business_question="Which physical retail locations generate the highest revenue?"),
            ChartRule("top_products", "Top Selling Products by Volume", "bar", dimension_patterns=("product", "item", "sku", "category"), metric_patterns=("quantity", "units", "sales"), aggregation="sum", business_question="What are the best-selling retail items?"),
            ChartRule("hourly_traffic", "Sales by Hour / Day", "line", dimension_patterns=("time", "hour", "day", "date"), metric_patterns=("sales", "amount", "quantity"), aggregation="sum", business_question="When are stores experiencing peak shopping hours?"),
        ),
        comparisons=(
            ComparisonRule("category", "Store-to-Store Sales Comparison", ("store", "branch", "outlet"), ("sales", "revenue")),
            ComparisonRule("category", "Category Sales Breakdown", ("category", "department", "aisle"), ("sales", "quantity")),
        ),
        trends=(
            TrendRule(("sales", "revenue"), ("date", "time", "day"), "Evaluating seasonal foot traffic and sales patterns"),
        ),
        risks=(
            RiskRule("discount_leak", "Heavy Discounting", "outlier", metric_patterns=("discount", "markdown"), threshold=2.5, label="Requires investigation", recommended_action="Check whether margin erosion is occurring due to unauthorized or excessive markdowns."),
            RiskRule("slow_moving", "Underperforming Store Outliers", "drop", metric_patterns=("sales", "quantity"), threshold=0.3, label="Potential anomaly", recommended_action="Investigate underperforming stores for stockouts or low foot traffic."),
        ),
        recommendations=(
            RecommendationRule("inventory_optimization", "units_sold", "high_demand", "Restock top-moving SKUs to prevent retail stockouts during peak shopping periods.", "Dependent on lead time of suppliers."),
        ),
    ),

    # 3. E-commerce
    DomainBlueprint(
        id="ecommerce",
        name="E-commerce",
        description="Online shopping, digital storefronts, shopping carts, digital checkout, and online orders.",
        keywords=("order", "cart", "checkout", "shipping", "shipping_fee", "online_store", "ecommerce", "e-commerce", "buyer", "fulfillment", "return", "refund", "tracking"),
        alternative_domains=("Retail", "Quick Commerce", "Food Delivery"),
        entities=(
            EntityRule("order", "Online Order", ("order_id", "order_number", "order", "invoice")),
            EntityRule("customer", "Online Customer", ("customer_id", "user_id", "buyer_id", "customer_email")),
            EntityRule("product", "Product Catalog Item", ("product_id", "sku", "title", "product_name")),
        ),
        kpis=(
            KpiRule("gmv", "Gross Merchandise Value (GMV)", "Total gross merchandise value from all orders", ("numeric",), metric_patterns=("total", "amount", "gmv", "order_total", "price", "sales", "revenue"), formula="sum", format="currency", business_meaning="Total online platform sales volume"),
            KpiRule("total_orders", "Total Orders", "Total count of online orders placed", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("order", "order_id", "id"), formula="count_distinct", format="number", business_meaning="Gross order volume"),
            KpiRule("aov", "Average Order Value (AOV)", "Mean monetary spend per order", ("numeric",), metric_patterns=("total", "amount", "price", "order_total", "sales", "revenue"), formula="mean", format="currency", business_meaning="Average customer expenditure per online checkout"),
            KpiRule("total_shipping", "Total Shipping Collected", "Total shipping fees charged across orders", ("numeric",), metric_patterns=("shipping", "shipping_fee", "freight"), formula="sum", format="currency", business_meaning="Gross logistics fee revenue"),
        ),
        charts=(
            ChartRule("orders_over_time", "Order Volume Trend", "line", dimension_patterns=("order_date", "date", "created_at"), metric_patterns=("total", "amount", "order_id", "sales", "revenue"), aggregation="sum", business_question="How is online sales volume trending daily/monthly?"),
            ChartRule("sales_by_category", "Sales by Product Category", "pie", dimension_patterns=("category", "sub_category"), metric_patterns=("total", "amount", "price", "sales", "revenue"), aggregation="sum", business_question="Which categories drive the majority of online revenue?"),
            ChartRule("order_value_dist", "Order Value Distribution", "histogram", metric_patterns=("total", "amount", "price", "sales"), aggregation="count", business_question="What is the distribution profile of online checkout values?"),
        ),
        comparisons=(
            ComparisonRule("category", "Sales by Channel or Device", ("channel", "device", "platform"), ("total", "amount")),
            ComparisonRule("segment", "New vs Repeat Customer Spending", ("customer_type", "segment"), ("total", "amount")),
        ),
        trends=(
            TrendRule(("total", "amount"), ("order_date", "date"), "Tracking daily and weekly online purchasing velocity"),
        ),
        risks=(
            RiskRule("high_refund_rate", "Elevated Return / Refund Rate", "spike", metric_patterns=("refund", "return_amount"), threshold=0.15, label="Requires investigation", recommended_action="Inspect product quality and accurate listing descriptions for high-return items."),
            RiskRule("order_drop", "Sudden Order Drop", "drop", metric_patterns=("order_id", "total"), threshold=0.3, label="Unusual pattern detected", recommended_action="Verify checkout uptime and payment gateway health."),
        ),
        recommendations=(
            RecommendationRule("customer_retention", "aov", "repeat_buyers", "Introduce bundle discounts or tiered shipping thresholds to increase Average Order Value.", "Requires elastic consumer demand."),
        ),
    ),

    # 4. Grocery
    DomainBlueprint(
        id="grocery",
        name="Grocery",
        description="Supermarket, perishable goods, fresh produce, dry goods, and everyday household essentials.",
        keywords=("grocery", "produce", "perishable", "supermarket", "fresh", "dairy", "bakery", "meat", "shelf_life", "expiry", "weight", "kg"),
        alternative_domains=("Retail", "FMCG", "Quick Commerce"),
        entities=(
            EntityRule("grocery_item", "Grocery Item", ("item", "product", "sku", "produce", "barcode")),
            EntityRule("aisle_section", "Aisle / Section", ("aisle", "section", "department", "category")),
        ),
        kpis=(
            KpiRule("grocery_revenue", "Total Grocery Sales", "Gross sales from grocery merchandise", ("numeric",), metric_patterns=("sales", "revenue", "amount", "total"), formula="sum", format="currency", business_meaning="Total supermarket sales receipts"),
            KpiRule("perishable_share", "Perishable Sales Proportion", "Ratio of fresh/perishable item sales to total sales", ("numeric",), metric_patterns=("perishable_sales", "fresh_sales"), formula="sum", format="percentage", business_meaning="Exposure to perishable inventory shrinkage"),
        ),
        charts=(
            ChartRule("sales_by_section", "Sales by Grocery Section", "bar", dimension_patterns=("section", "aisle", "department"), metric_patterns=("sales", "amount"), aggregation="sum", business_question="Which supermarket sections generate highest turnover?"),
        ),
        comparisons=(
            ComparisonRule("category", "Section Performance Comparison", ("section", "department"), ("sales", "amount")),
        ),
        trends=(
            TrendRule(("sales", "amount"), ("date", "day"), "Tracking daily grocery restocking and consumer buying patterns"),
        ),
        risks=(
            RiskRule("shrinkage_spoilage", "Produce Spoilage Risk", "spike", metric_patterns=("waste", "shrinkage", "spoilage"), threshold=0.08, label="Requires investigation", recommended_action="Tighten stock rotation and dynamic discounting near expiry dates."),
        ),
        recommendations=(
            RecommendationRule("inventory_optimization", "grocery_revenue", "perishable", "Optimize daily fresh order quantities to minimize shrinkage.", "Assumes reliable supplier delivery schedules."),
        ),
    ),

    # 5. FMCG (Fast-Moving Consumer Goods)
    DomainBlueprint(
        id="fmcg",
        name="FMCG",
        description="High turnover consumer packaged goods, distributors, wholesalers, retail stocking, and brands.",
        keywords=("fmcg", "cpg", "distributor", "wholesaler", "pack", "carton", "brand", "case", "depot", "trade_spend", "off_invoice"),
        alternative_domains=("Grocery", "Supply Chain", "Retail"),
        entities=(
            EntityRule("brand", "CPG Brand", ("brand", "brand_name", "manufacturer")),
            EntityRule("distributor", "Distributor / Wholesaler", ("distributor", "wholesaler", "dealer", "agency")),
        ),
        kpis=(
            KpiRule("fmcg_volume", "Total Volume Dispatched", "Total volume in cases or cartons dispatched to trade", ("numeric",), metric_patterns=("cases", "cartons", "volume", "units"), formula="sum", format="number", business_meaning="Total brand distribution throughput"),
            KpiRule("trade_sales", "Gross Trade Sales", "Total value of goods sold to distributors and retailers", ("numeric",), metric_patterns=("sales", "trade_sales", "gross_sales"), formula="sum", format="currency", business_meaning="Top-line brand wholesale revenue"),
        ),
        charts=(
            ChartRule("brand_volume", "Volume by Brand", "pie", dimension_patterns=("brand", "category"), metric_patterns=("volume", "cases", "sales"), aggregation="sum", business_question="What is the sales contribution across consumer brands?"),
        ),
        comparisons=(
            ComparisonRule("category", "Brand-wise Distribution Comparison", ("brand", "manufacturer"), ("sales", "volume")),
        ),
        trends=(
            TrendRule(("sales", "volume"), ("date", "month"), "Monitoring monthly distributor off-take velocity"),
        ),
        risks=(
            RiskRule("distributor_lag", "Distributor Order Drop", "drop", metric_patterns=("sales", "volume"), threshold=0.25, label="Potential anomaly", recommended_action="Audit distributor inventory levels to assess secondary sales health."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "trade_sales", "volume", "Align manufacturing batch sizes with high-velocity SKU distribution schedules.", "Requires synchronized supply chain forecasting."),
        ),
    ),

    # 6. Food and Restaurant
    DomainBlueprint(
        id="food_restaurant",
        name="Food and Restaurant",
        description="Dine-in and takeaway restaurants, cafes, menus, kitchen operations, table turnover, and guest dining.",
        keywords=("restaurant", "dish", "menu", "table", "dine_in", "waiter", "server", "cover", "food_cost", "kitchen", "recipe", "beverage", "meal"),
        alternative_domains=("Food Delivery", "Hospitality and Hotels", "Restaurant Operations"),
        entities=(
            EntityRule("dish", "Menu Item / Dish", ("dish", "menu_item", "food_item", "item_name")),
            EntityRule("table", "Dining Table / Server", ("table_no", "table", "server", "waiter")),
        ),
        kpis=(
            KpiRule("restaurant_revenue", "Total Food & Beverage Revenue", "Total gross dining sales", ("numeric",), metric_patterns=("revenue", "sales", "bill_amount", "total"), formula="sum", format="currency", business_meaning="Total restaurant dining receipts"),
            KpiRule("avg_check", "Average Check / Bill Size", "Average spend per dining party or bill", ("numeric",), metric_patterns=("bill_amount", "amount", "total"), formula="mean", format="currency", business_meaning="Average table spend"),
            KpiRule("total_covers", "Total Covers / Guests", "Total number of guests served", ("numeric",), metric_patterns=("covers", "guests", "party_size"), formula="sum", format="number", business_meaning="Dining room footfall volume"),
        ),
        charts=(
            ChartRule("sales_by_dish", "Top Menu Items by Revenue", "bar", dimension_patterns=("dish", "menu_item", "category"), metric_patterns=("sales", "bill_amount", "quantity"), aggregation="sum", business_question="Which dishes are the primary revenue drivers?"),
            ChartRule("dining_hours", "Revenue by Meal Period / Hour", "line", dimension_patterns=("meal_type", "hour", "time"), metric_patterns=("sales", "revenue", "bill_amount"), aggregation="sum", business_question="What are the busiest meal periods (lunch vs dinner)?"),
        ),
        comparisons=(
            ComparisonRule("category", "Menu Category Contribution", ("category", "course"), ("sales", "quantity")),
        ),
        trends=(
            TrendRule(("sales", "revenue"), ("date", "day_of_week"), "Identifying peak weekday vs weekend dining demand"),
        ),
        risks=(
            RiskRule("high_food_cost", "High Food Cost Variance", "spike", metric_patterns=("food_cost_pct", "waste_cost"), threshold=0.35, label="Requires investigation", recommended_action="Audit portion control and supplier ingredient price fluctuations."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "avg_check", "dine_in", "Train servers on beverage and dessert upselling to increase average check size.", "Relies on staff adherence to service standards."),
        ),
    ),

    # 7. Food Delivery
    DomainBlueprint(
        id="food_delivery",
        name="Food Delivery",
        description="On-demand food delivery platforms, delivery riders, restaurant partners, prep times, and transit durations.",
        keywords=("delivery_time", "rider", "courier", "prep_time", "delivery_fee", "restaurant_partner", "food_delivery", "delivery_status", "dropoff", "pickup"),
        alternative_domains=("Food and Restaurant", "Quick Commerce", "Delivery and Courier"),
        entities=(
            EntityRule("rider", "Delivery Rider / Courier", ("rider_id", "driver_id", "courier_id", "delivery_partner")),
            EntityRule("restaurant_partner", "Restaurant Partner", ("restaurant_id", "merchant_id", "outlet_id", "kitchen")),
        ),
        kpis=(
            KpiRule("avg_delivery_time", "Average Delivery Time (mins)", "Mean time elapsed from order placement to customer handover", ("numeric",), metric_patterns=("delivery_time", "duration", "transit_mins"), formula="mean", format="duration", business_meaning="Customer fulfillment latency"),
            KpiRule("cancellation_rate", "Order Cancellation Rate", "Percentage of dispatched orders cancelled", ("numeric", "boolean"), metric_patterns=("cancelled", "is_cancelled"), formula="mean", format="percentage", business_meaning="Service reliability failure rate"),
        ),
        charts=(
            ChartRule("delivery_time_by_zone", "Delivery Time by Delivery Zone", "bar", dimension_patterns=("zone", "city", "area"), metric_patterns=("delivery_time", "duration"), aggregation="mean", business_question="Which delivery zones suffer from the longest fulfillment delays?"),
        ),
        comparisons=(
            ComparisonRule("category", "Delivery Performance across Zones", ("zone", "area", "region"), ("delivery_time", "duration")),
        ),
        trends=(
            TrendRule(("delivery_time", "duration"), ("hour", "time", "date"), "Tracking delivery delays during peak lunch and dinner rush hours"),
        ),
        risks=(
            RiskRule("delivery_delay_spike", "Delivery Latency Spike", "spike", metric_patterns=("delivery_time", "duration"), threshold=45.0, label="Requires investigation", recommended_action="Increase rider density or limit order radius during adverse weather or traffic peaks."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "avg_delivery_time", "long_latency", "Optimize kitchen prep dispatch handoffs to decrease idle rider waiting time.", "Depends on restaurant partner compliance."),
        ),
    ),

    # 8. Quick Commerce
    DomainBlueprint(
        id="quick_commerce",
        name="Quick Commerce",
        description="Ultra-fast 10-30 minute delivery, dark stores, micro-fulfillment centers, and high-frequency essentials.",
        keywords=("dark_store", "micro_fulfillment", "quick_commerce", "10_min", "instant_delivery", "picker", "packer", "sla_breach", "dispatch_time"),
        alternative_domains=("E-commerce", "Food Delivery", "Grocery"),
        entities=(
            EntityRule("dark_store", "Dark Store / Pod", ("dark_store_id", "pod_id", "mfc_id", "store_code")),
            EntityRule("picker", "Store Picker / Packer", ("picker_id", "packer_id", "staff_id")),
        ),
        kpis=(
            KpiRule("sla_compliance", "SLA Delivery Compliance", "Proportion of orders delivered strictly within guaranteed window", ("numeric", "boolean"), metric_patterns=("on_time", "sla_met", "within_sla"), formula="mean", format="percentage", business_meaning="Commitment fulfillment reliability"),
            KpiRule("avg_picking_time", "Average Picking Time", "Mean seconds or minutes to pick and pack items in dark store", ("numeric",), metric_patterns=("pick_time", "pack_time", "prep_seconds"), formula="mean", format="duration", business_meaning="Dark store fulfillment efficiency"),
        ),
        charts=(
            ChartRule("orders_per_pod", "Order Throughput by Dark Store", "bar", dimension_patterns=("dark_store", "pod", "store_code"), metric_patterns=("order_id", "total"), aggregation="count", business_question="Which dark stores handle the highest instant order volume?"),
        ),
        comparisons=(
            ComparisonRule("category", "SLA Compliance across Dark Stores", ("dark_store", "pod"), ("sla_met", "on_time")),
        ),
        trends=(
            TrendRule(("order_id", "total"), ("hour", "date"), "Monitoring minute-by-minute order surge waves"),
        ),
        risks=(
            RiskRule("sla_breach_surge", "Elevated SLA Breach Rate", "spike", metric_patterns=("breach", "late_delivery"), threshold=0.10, label="Requires investigation", recommended_action="Rebalance picker staffing in overloaded micro-fulfillment centers."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "sla_compliance", "low_sla", "Re-layout dark store fast-moving inventory near packing stations to speed picking.", "Assumes space availability inside pod."),
        ),
    ),

    # 73. Restaurant Operations
    DomainBlueprint(
        id="restaurant_ops",
        name="Restaurant Operations",
        description="Back-of-house kitchen operations, food prep times, station performance, ingredient wastage, and table turnover.",
        keywords=("kitchen", "prep_time", "cook_time", "station", "chef", "table_turnover", "food_waste", "86ed", "out_of_stock_item", "ticket_time"),
        alternative_domains=("Food and Restaurant", "Food Delivery"),
        entities=(
            EntityRule("station", "Kitchen Station", ("station", "line", "grill", "fryer", "prep_station")),
            EntityRule("ticket", "Kitchen Order Ticket (KOT)", ("kot_id", "ticket_id", "order_no")),
        ),
        kpis=(
            KpiRule("ticket_time", "Average Kitchen Ticket Time", "Mean duration from order receipt in kitchen to food ready", ("numeric",), metric_patterns=("ticket_time", "cook_time", "prep_time"), formula="mean", format="duration", business_meaning="Back-of-house kitchen velocity"),
            KpiRule("table_turn_rate", "Table Turns per Shift", "Average times a dining table is seated during a service period", ("numeric",), metric_patterns=("turnover", "turns", "seatings"), formula="mean", format="number", business_meaning="Front-of-house capacity utilization"),
        ),
        charts=(
            ChartRule("prep_by_station", "Ticket Time by Kitchen Station", "bar", dimension_patterns=("station", "line"), metric_patterns=("ticket_time", "cook_time"), aggregation="mean", business_question="Which kitchen station creates the biggest dining bottlenecks?"),
        ),
        comparisons=(
            ComparisonRule("category", "Ticket Times across Service Shifts", ("shift", "meal_period"), ("ticket_time", "prep_time")),
        ),
        trends=(
            TrendRule(("ticket_time", "prep_time"), ("time", "date"), "Tracking kitchen backlog build-up during rush hours"),
        ),
        risks=(
            RiskRule("kitchen_delay", "Kitchen Bottleneck", "spike", metric_patterns=("ticket_time", "cook_time"), threshold=25.0, label="Requires investigation", recommended_action="Reassign kitchen prep tasks to relieve overloaded cook stations."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "ticket_time", "slow_ticket", "Pre-portion high-demand menu ingredients prior to peak dinner rush.", "Requires refrigerated prep space."),
        ),
    ),

    # 74. Retail Operations
    DomainBlueprint(
        id="retail_ops",
        name="Retail Operations",
        description="Store-level operations, footfall counters, inventory shrinkage, stock-outs, register queue times, and staffing.",
        keywords=("footfall", "conversion_rate", "shrinkage", "stockout", "shelf_space", "planogram", "queue_time", "pos_terminal", "store_ops", "audit_score"),
        alternative_domains=("Retail", "Grocery", "General Business Analytics"),
        entities=(
            EntityRule("store_register", "POS Register / Terminal", ("register_id", "terminal_id", "pos_no", "lane")),
            EntityRule("staff_member", "Floor Staff / Associate", ("associate_id", "staff_id", "employee_id")),
        ),
        kpis=(
            KpiRule("store_conversion", "Store Footfall Conversion Rate", "Proportion of store visitors who complete a retail transaction", ("numeric",), metric_patterns=("conversion", "conversion_rate", "buyer_ratio"), formula="mean", format="percentage", business_meaning="Efficiency of converting in-store traffic into buyers"),
            KpiRule("avg_checkout_duration", "Average Checkout Duration", "Mean time spent per shopper at the POS checkout lane", ("numeric",), metric_patterns=("checkout_time", "scan_time", "lane_time"), formula="mean", format="duration", business_meaning="Cashier throughput speed and queue efficiency"),
        ),
        charts=(
            ChartRule("conversion_by_store", "Conversion Rate by Store", "bar", dimension_patterns=("store", "location", "branch"), metric_patterns=("conversion", "conversion_rate"), aggregation="mean", business_question="Which stores excel at converting foot traffic into paying customers?"),
        ),
        comparisons=(
            ComparisonRule("category", "Store Operational Audit Scores", ("store", "branch"), ("audit_score", "conversion")),
        ),
        trends=(
            TrendRule(("footfall", "visitors"), ("date", "hour"), "Monitoring store shopper traffic volume throughout the week"),
        ),
        risks=(
            RiskRule("low_conversion_anomaly", "Low Conversion Anomaly", "drop", metric_patterns=("conversion", "conversion_rate"), threshold=0.10, label="Requires investigation", recommended_action="Investigate store inventory availability and customer service coverage."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "store_conversion", "low_traffic_conversion", "Align floor associate shift scheduling directly with historical footfall surge hours.", "Subject to retail staff scheduling regulations."),
        ),
    ),
]
