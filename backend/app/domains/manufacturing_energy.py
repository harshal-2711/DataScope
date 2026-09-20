"""Manufacturing, Energy, Utilities, Agriculture, Construction, and Mining domain blueprints (Domains 38, 39, 40, 52, 53, 54, 63, 64)."""
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
    # 38. Manufacturing
    DomainBlueprint(
        id="manufacturing",
        name="Manufacturing",
        description="Industrial manufacturing, shop floor operations, assembly lines, equipment downtime, and overall equipment effectiveness (OEE).",
        keywords=("manufacturing", "assembly_line", "machine", "plant", "downtime", "oee", "work_order", "scrap", "cycle_time", "operator", "factory", "equipment"),
        alternative_domains=("Manufacturing Quality", "Production Analytics", "IoT and Sensor Data"),
        entities=(
            EntityRule("factory_machine", "Machine / Equipment", ("machine_id", "equipment_id", "asset_id", "line_id")),
            EntityRule("work_order", "Manufacturing Work Order", ("work_order_id", "wo_number", "job_id")),
        ),
        kpis=(
            KpiRule("oee", "Overall Equipment Effectiveness (OEE)", "Composite metric of machine availability, performance, and quality", ("numeric",), metric_patterns=("oee", "equipment_effectiveness"), formula="mean", format="percentage", business_meaning="Manufacturing plant productivity standard"),
            KpiRule("total_downtime_hours", "Total Equipment Downtime (Hours)", "Sum of unplanned and planned machine stoppage hours", ("numeric",), metric_patterns=("downtime_hours", "downtime", "stoppage_time"), formula="sum", format="duration", business_meaning="Lost factory operational capacity"),
            KpiRule("total_units_manufactured", "Total Manufactured Units", "Total physical product units completed on assembly lines", ("numeric",), metric_patterns=("units_produced", "output_quantity", "good_units"), formula="sum", format="number", business_meaning="Gross manufacturing production output"),
        ),
        charts=(
            ChartRule("downtime_by_machine", "Downtime Hours by Machine", "bar", dimension_patterns=("machine_id", "equipment_name", "line_id"), metric_patterns=("downtime_hours", "downtime"), aggregation="sum", business_question="Which machines account for the most production downtime?"),
            ChartRule("production_by_line", "Production Output by Assembly Line", "bar", dimension_patterns=("assembly_line", "line_name", "plant"), metric_patterns=("units_produced", "output_quantity"), aggregation="sum", business_question="How does output compare across factory production lines?"),
        ),
        comparisons=(
            ComparisonRule("category", "Downtime by Reason Code", ("downtime_reason", "fault_code"), ("downtime_hours", "downtime")),
        ),
        trends=(
            TrendRule(("units_produced", "downtime_hours"), ("date", "shift_date"), "Tracking factory throughput stability across operating shifts"),
        ),
        risks=(
            RiskRule("unplanned_downtime_spike", "Equipment Stoppage Spike", "spike", metric_patterns=("downtime_hours", "downtime"), threshold=10.0, label="Requires investigation", recommended_action="Initiate emergency predictive maintenance audit on high-downtime equipment."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "oee", "low_oee", "Implement Total Productive Maintenance (TPM) operator checklists prior to shift start.", "Requires shop floor operator training."),
        ),
    ),

    # 39. Manufacturing Quality
    DomainBlueprint(
        id="manufacturing_quality",
        name="Manufacturing Quality",
        description="Defect rates, parts per million (PPM), Six Sigma defects, scrap rate, non-conformance reports (NCR), and rework hours.",
        keywords=("quality", "defect_rate", "ppm", "scrap_rate", "ncr", "rework", "non_conformance", "tolerance", "inspection", "first_pass_yield", "fpy", "rejection"),
        alternative_domains=("Manufacturing", "Production Analytics"),
        entities=(
            EntityRule("quality_inspection", "Quality Inspection / Lot", ("inspection_id", "lot_id", "sample_id")),
            EntityRule("defect_type", "Defect Category / NCR", ("defect_code", "defect_type", "ncr_number")),
        ),
        kpis=(
            KpiRule("first_pass_yield", "First Pass Yield (FPY)", "Percentage of manufactured units passing inspection with no rework", ("numeric",), metric_patterns=("first_pass_yield", "fpy", "pass_rate"), formula="mean", format="percentage", business_meaning="Manufacturing process precision and quality"),
            KpiRule("scrap_rate", "Material Scrap Rate", "Proportion of total raw materials or parts discarded as scrap", ("numeric",), metric_patterns=("scrap_rate", "scrap_pct", "rejection_rate"), formula="mean", format="percentage", business_meaning="Manufacturing material waste efficiency"),
            KpiRule("total_defects", "Total Defect Count", "Sum of all non-conformance defects identified during inspection", ("numeric",), metric_patterns=("defect_count", "defects", "reject_count"), formula="sum", format="number", business_meaning="Total manufacturing error volume"),
        ),
        charts=(
            ChartRule("defects_by_type", "Defect Count by Defect Type (Pareto)", "bar", dimension_patterns=("defect_type", "defect_code", "reason"), metric_patterns=("defect_count", "defects"), aggregation="sum", business_question="What are the top 20% of defect types causing 80% of quality rejections?"),
        ),
        comparisons=(
            ComparisonRule("category", "First Pass Yield by Shift / Operator", ("shift", "operator_id"), ("first_pass_yield", "pass_rate")),
        ),
        trends=(
            TrendRule(("defect_count", "scrap_rate"), ("inspection_date", "date"), "Monitoring statistical process control (SPC) quality drift over time"),
        ),
        risks=(
            RiskRule("scrap_surge", "Scrap Rate Surge", "spike", metric_patterns=("scrap_rate", "rejection_rate"), threshold=0.08, label="Requires investigation", recommended_action="Inspect tooling wear and raw material lot certificates of analysis."),
        ),
        recommendations=(
            RecommendationRule("quality_improvement", "first_pass_yield", "low_fpy", "Calibrate CNC machines and re-validate tooling fixtures on low-yielding lines.", "Requires machine calibration downtime."),
        ),
    ),

    # 40. Production Analytics
    DomainBlueprint(
        id="production_analytics",
        name="Production Analytics",
        description="Production runs, batch cycles, target vs actual output, shift quotas, capacity utilization, and takt time.",
        keywords=("production", "batch_size", "takt_time", "actual_output", "target_output", "quota", "shift_production", "capacity_utilization", "run_time", "throughput_rate"),
        alternative_domains=("Manufacturing", "Supply Chain"),
        entities=(
            EntityRule("production_batch", "Production Batch / Run", ("batch_id", "run_id", "job_number")),
            EntityRule("production_shift", "Production Shift", ("shift_id", "shift_name", "shift_code")),
        ),
        kpis=(
            KpiRule("quota_attainment", "Production Quota Attainment", "Ratio of actual manufactured units to planned schedule target", ("numeric",), metric_patterns=("attainment", "plan_vs_actual", "quota_pct"), formula="mean", format="percentage", business_meaning="Manufacturing schedule execution fidelity"),
            KpiRule("avg_takt_time", "Average Takt / Cycle Time (seconds)", "Mean time required to produce one unit of finished product", ("numeric",), metric_patterns=("takt_time", "cycle_time", "seconds_per_unit"), formula="mean", format="duration", business_meaning="Manufacturing production pace"),
        ),
        charts=(
            ChartRule("actual_vs_target_output", "Actual vs Target Output by Line", "bar", dimension_patterns=("line_name", "product_line"), metric_patterns=("actual_output", "target_output"), aggregation="sum", business_question="Which production lines are meeting or falling short of output targets?"),
        ),
        comparisons=(
            ComparisonRule("category", "Throughput across Factory Shifts", ("shift_name", "shift_code"), ("actual_output", "units_produced")),
        ),
        trends=(
            TrendRule(("actual_output", "units_produced"), ("date", "production_date"), "Tracking daily factory output consistency"),
        ),
        risks=(
            RiskRule("production_shortfall", "Severe Production Deficit", "drop", metric_patterns=("attainment", "actual_output"), threshold=0.20, label="Requires investigation", recommended_action="Investigate raw material replenishment bottlenecks or operator absenteeism."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "quota_attainment", "low_quota", "Re-balance assembly station workloads to eliminate bottleneck cycle times.", "Requires industrial engineering line balancing analysis."),
        ),
    ),

    # 52. Energy and Utilities
    DomainBlueprint(
        id="energy_utilities",
        name="Energy and Utilities",
        description="Electricity generation, power grid load, kilowatt-hours (kWh), megawatts, renewable generation, utility bills, and outages.",
        keywords=("energy", "utility", "kwh", "megawatt", "grid_load", "electricity", "power_plant", "substation", "solar", "wind", "outage", "consumption", "voltage"),
        alternative_domains=("Oil and Gas", "Environment and Climate", "IoT and Sensor Data"),
        entities=(
            EntityRule("power_asset", "Power Generation / Grid Asset", ("asset_id", "plant_id", "substation_id", "meter_id")),
            EntityRule("utility_customer", "Utility Account / Meter", ("meter_number", "customer_account", "premise_id")),
        ),
        kpis=(
            KpiRule("total_energy_consumption", "Total Energy Consumed (kWh/MWh)", "Total electrical energy consumed across metered points", ("numeric",), metric_patterns=("kwh", "mwh", "consumption", "energy_used"), formula="sum", format="number", business_meaning="Gross electricity consumption volume"),
            KpiRule("peak_grid_demand", "Peak Grid Demand (MW)", "Highest power demand recorded during reporting period", ("numeric",), metric_patterns=("peak_demand", "max_mw", "peak_load"), formula="max", format="number", business_meaning="Peak power capacity stress"),
            KpiRule("total_utility_revenue", "Total Utility Billing Revenue", "Gross revenue billed for electricity and utility services", ("numeric",), metric_patterns=("billed_amount", "revenue", "utility_charges"), formula="sum", format="currency", business_meaning="Utility service operating receipts"),
        ),
        charts=(
            ChartRule("load_profile", "Hourly Grid Load Profile", "line", dimension_patterns=("hour", "time", "timestamp"), metric_patterns=("kwh", "megawatts", "consumption"), aggregation="sum", business_question="What are the daily peak power demand hours?"),
            ChartRule("generation_by_source", "Energy Generation by Fuel Source", "pie", dimension_patterns=("fuel_source", "generation_type", "source"), metric_patterns=("mwh", "generation", "kwh"), aggregation="sum", business_question="What proportion of energy is generated from renewable vs fossil sources?"),
        ),
        comparisons=(
            ComparisonRule("category", "Consumption across Customer Classes (Residential vs Industrial)", ("customer_class", "tariff"), ("kwh", "consumption")),
        ),
        trends=(
            TrendRule(("consumption", "kwh"), ("date", "month"), "Analyzing seasonal summer air conditioning and winter heating electricity peaks"),
        ),
        risks=(
            RiskRule("peak_demand_spike", "Grid Overload Peak Risk", "spike", metric_patterns=("peak_demand", "kwh"), threshold=1.2, label="Requires investigation", recommended_action="Activate demand-response industrial curtailment programs during critical peak hours."),
        ),
        recommendations=(
            RecommendationRule("cost_reduction", "total_energy_consumption", "peak_hours", "Incentivize commercial customers with time-of-use (TOU) rates to shift load off-peak.", "Requires smart meter infrastructure."),
        ),
    ),

    # 53. Oil and Gas
    DomainBlueprint(
        id="oil_gas",
        name="Oil and Gas",
        description="Upstream drilling, barrels of oil per day (BOPD), wellhead pressure, refinery throughput, pipeline flow, and natural gas.",
        keywords=("oil", "gas", "petroleum", "bopd", "barrels", "drilling", "wellhead", "refinery", "crude", "pipeline", "natural_gas", "upstream", "downstream"),
        alternative_domains=("Energy and Utilities", "Mining", "Commodities"),
        entities=(
            EntityRule("wellhead", "Oil / Gas Well", ("well_id", "well_name", "rig_id", "api_number")),
            EntityRule("pipeline_segment", "Pipeline / Facility", ("pipeline_id", "facility_id", "refinery_id")),
        ),
        kpis=(
            KpiRule("total_crude_production", "Total Crude Production (Barrels)", "Total volume of crude oil extracted in barrels", ("numeric",), metric_patterns=("barrels", "bopd", "crude_volume", "oil_production"), formula="sum", format="number", business_meaning="Upstream oil extraction volume"),
            KpiRule("gas_production", "Natural Gas Production (MCF)", "Total natural gas volume produced in thousand cubic feet", ("numeric",), metric_patterns=("gas_volume", "mcf", "gas_production"), formula="sum", format="number", business_meaning="Upstream gas extraction volume"),
        ),
        charts=(
            ChartRule("production_by_well", "Production Volume by Oil Well", "bar", dimension_patterns=("well_name", "well_id", "field"), metric_patterns=("barrels", "bopd", "crude_volume"), aggregation="sum", business_question="Which oil fields and wells are the primary extraction contributors?"),
        ),
        comparisons=(
            ComparisonRule("category", "Flow Rates across Production Basins", ("basin", "field"), ("barrels", "bopd")),
        ),
        trends=(
            TrendRule(("barrels", "bopd"), ("date", "production_date"), "Tracking well decline curves (Arps decline) over production lifespan"),
        ),
        risks=(
            RiskRule("well_pressure_drop", "Abnormal Wellhead Pressure Drop", "drop", metric_patterns=("pressure", "wellhead_psi"), threshold=0.3, label="Requires investigation", recommended_action="Inspect artificial lift pumps and conduct downhole casing integrity tests."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "total_crude_production", "well_decline", "Schedule artificial lift optimization or well workovers on declining productive assets.", "Requires capital expenditure approval."),
        ),
    ),

    # 54. Agriculture
    DomainBlueprint(
        id="agriculture",
        name="Agriculture",
        description="Crop yields, acreage, farm harvesting, soil moisture, irrigation, fertilizer application, livestock, and produce tonnage.",
        keywords=("agriculture", "crop", "yield", "acreage", "harvest", "soil_moisture", "fertilizer", "irrigation", "livestock", "bushels", "tonnage", "farm"),
        alternative_domains=("Food and Restaurant", "Environment and Climate", "Supply Chain"),
        entities=(
            EntityRule("farm_field", "Agricultural Field / Plot", ("field_id", "plot_id", "parcel_no", "farm_id")),
            EntityRule("crop_variety", "Crop Variety / Cultivar", ("crop_name", "crop_type", "variety")),
        ),
        kpis=(
            KpiRule("crop_yield_per_acre", "Average Crop Yield per Acre", "Mean harvested bushels or metric tons produced per planted acre", ("numeric",), metric_patterns=("yield", "bushels_per_acre", "yield_per_hectare"), formula="mean", format="number", business_meaning="Agricultural land productivity"),
            KpiRule("total_harvest_tonnage", "Total Harvested Production (Tons)", "Total agricultural commodity output produced", ("numeric",), metric_patterns=("harvest_weight", "total_yield", "production_tons"), formula="sum", format="number", business_meaning="Gross agricultural food output"),
        ),
        charts=(
            ChartRule("yield_by_crop", "Crop Yield by Variety", "bar", dimension_patterns=("crop_name", "variety", "crop_type"), metric_patterns=("yield", "total_yield"), aggregation="mean", business_question="Which crop varieties achieve the highest yield per acre?"),
        ),
        comparisons=(
            ComparisonRule("category", "Yield Comparison across Farm Fields", ("field_id", "plot_id"), ("yield", "harvest_weight")),
        ),
        trends=(
            TrendRule(("yield", "harvest_weight"), ("harvest_year", "season"), "Tracking multi-year agricultural harvest cycles against climate patterns"),
        ),
        risks=(
            RiskRule("crop_yield_deficit", "Severe Yield Deficit", "drop", metric_patterns=("yield", "bushels_per_acre"), threshold=0.30, label="Requires investigation", recommended_action="Inspect soil nutrient depletion and pest infestation evidence in low-yielding plots."),
        ),
        recommendations=(
            RecommendationRule("quality_improvement", "crop_yield_per_acre", "low_yield_plots", "Adopt precision variable-rate nitrogen fertilization based on soil moisture grid data.", "Requires GPS-guided fertilizer application equipment."),
        ),
    ),

    # 63. Construction
    DomainBlueprint(
        id="construction",
        name="Construction",
        description="Construction projects, job site safety, subcontractor milestones, material quantities, change orders, and cost variance.",
        keywords=("construction", "jobsite", "subcontractor", "change_order", "milestone", "concrete", "steel", "safety_incident", "labor_hours", "schedule_variance"),
        alternative_domains=("Manufacturing", "General Business Analytics", "Real Estate"),
        entities=(
            EntityRule("construction_project", "Construction Project / Jobsite", ("project_id", "job_number", "site_name")),
            EntityRule("subcontractor", "Subcontractor / Trade", ("subcontractor", "trade", "contractor_id")),
        ),
        kpis=(
            KpiRule("cost_variance", "Construction Cost Variance (CV)", "Earned Value minus Actual Cost across project work packages", ("numeric",), metric_patterns=("cost_variance", "cv", "budget_variance"), formula="sum", format="currency", business_meaning="Capital project budget adherence"),
            KpiRule("safety_incident_count", "Total Safety Incidents / OSHA", "Count of recordable safety events logged on job sites", ("numeric", "categorical"), metric_patterns=("incidents", "safety_events"), dimension_patterns=("incident_id",), formula="sum", format="number", business_meaning="Jobsite physical safety compliance"),
        ),
        charts=(
            ChartRule("cost_by_project", "Expenditure by Construction Project", "bar", dimension_patterns=("project_name", "job_number"), metric_patterns=("actual_cost", "spent_amount"), aggregation="sum", business_question="Which capital construction projects represent the highest expenditure?"),
        ),
        comparisons=(
            ComparisonRule("category", "Subcontractor Schedule Performance", ("subcontractor", "trade"), ("schedule_variance", "cost_variance")),
        ),
        trends=(
            TrendRule(("actual_cost", "spend"), ("month", "date"), "Monitoring construction progress cash flow drawdowns"),
        ),
        risks=(
            RiskRule("change_order_escalation", "Change Order Cost Escalation", "spike", metric_patterns=("change_order_amount", "change_cost"), threshold=0.15, label="Requires investigation", recommended_action="Audit scope gap root causes and freeze non-essential architect revisions."),
        ),
        recommendations=(
            RecommendationRule("cost_reduction", "cost_variance", "negative_cv", "Conduct weekly subcontractor earned-value reconciliations to prevent cost overruns.", "Requires standardized daily site logs."),
        ),
    ),

    # 64. Mining
    DomainBlueprint(
        id="mining",
        name="Mining",
        description="Mineral extraction, ore grade, haul truck cycles, tonnage moved, stripping ratio, tailings, and smelting output.",
        keywords=("mining", "ore_grade", "haul_truck", "tonnage", "stripping_ratio", "pit", "mineral", "crusher", "concentrate", "tailings", "excavator", "mine_site"),
        alternative_domains=("Oil and Gas", "Manufacturing", "Heavy Equipment"),
        entities=(
            EntityRule("mine_pit", "Mine Pit / Bench", ("pit_id", "bench_id", "site_id", "quarry")),
            EntityRule("haul_truck", "Haul Truck / Excavator", ("truck_id", "shovel_id", "equipment_id")),
        ),
        kpis=(
            KpiRule("total_ore_tonnage", "Total Ore Tonnage Mined", "Total metric tons of commercial mineral ore extracted", ("numeric",), metric_patterns=("ore_tonnage", "tons_mined", "tonnage"), formula="sum", format="number", business_meaning="Gross mineral extraction volume"),
            KpiRule("avg_ore_grade", "Average Mineral Ore Grade", "Mean assay grade percentage or grams per ton (g/t)", ("numeric",), metric_patterns=("ore_grade", "grade", "assay_pct", "grams_per_ton"), formula="mean", format="number", business_meaning="Ore economic mineral concentration"),
        ),
        charts=(
            ChartRule("tonnage_by_pit", "Tonnage Extracted by Mine Pit", "bar", dimension_patterns=("pit_id", "pit_name", "bench"), metric_patterns=("ore_tonnage", "tons_mined"), aggregation="sum", business_question="Which open-pit or underground zones yield the highest ore volumes?"),
        ),
        comparisons=(
            ComparisonRule("category", "Ore Grades across Mine Deposits", ("deposit_name", "pit_id"), ("ore_grade", "grade")),
        ),
        trends=(
            TrendRule(("ore_tonnage", "tons_mined"), ("date", "shift"), "Tracking daily excavation productivity across shifts"),
        ),
        risks=(
            RiskRule("ore_grade_dilution", "Severe Ore Grade Dilution", "drop", metric_patterns=("ore_grade", "grade"), threshold=0.25, label="Requires investigation", recommended_action="Adjust blast hole spacing and selective mining excavator controls to minimize waste rock dilution."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "total_ore_tonnage", "haulage_bottlenecks", "Optimize dispatch haul truck routing to reduce crusher queue idle times.", "Requires automated fleet management telematics."),
        ),
    ),
]
