"""Real Estate, Telecom, Government, Environment, Weather, Science, Crime, Demographics, Economics, and General domain blueprints (Domains 36, 37, 51, 55, 65, 66, 67, 70, 71, 72, 75)."""
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
    # 36. Real Estate
    DomainBlueprint(
        id="real_estate",
        name="Real Estate",
        description="Residential and commercial property listings, square footage, sale prices, days on market, bedrooms, and neighborhoods.",
        keywords=("property", "real_estate", "listing", "sqft", "square_feet", "bedroom", "bathroom", "sale_price", "mls", "neighborhood", "broker", "agent", "zoning"),
        alternative_domains=("Real Estate Investment", "Construction", "General Business Analytics"),
        entities=(
            EntityRule("property_listing", "Property Listing", ("property_id", "listing_id", "mls_number", "address")),
            EntityRule("real_estate_agent", "Real Estate Agent / Broker", ("agent_id", "broker_name", "listing_agent")),
        ),
        kpis=(
            KpiRule("avg_price_per_sqft", "Average Price per Square Foot", "Mean property price divided by interior square footage", ("numeric",), metric_patterns=("price_per_sqft", "price_sqft", "cost_per_sqft"), formula="mean", format="currency", business_meaning="Normalized property valuation benchmark"),
            KpiRule("avg_days_on_market", "Average Days on Market (DOM)", "Mean days elapsed between listing date and sale contract", ("numeric",), metric_patterns=("days_on_market", "dom", "listing_age"), formula="mean", format="number", business_meaning="Real estate market liquidity and buyer velocity"),
            KpiRule("median_listing_price", "Median Property Listing Price", "Central transaction price across listed properties", ("numeric",), metric_patterns=("sale_price", "price", "listing_price"), formula="mean", format="currency", business_meaning="Local housing affordability benchmark"),
        ),
        charts=(
            ChartRule("price_by_neighborhood", "Average Price by Neighborhood", "bar", dimension_patterns=("neighborhood", "city", "zip_code"), metric_patterns=("sale_price", "price"), aggregation="mean", business_question="Which neighborhoods command the highest property valuations?"),
            ChartRule("sqft_vs_price", "Square Footage vs Listing Price", "scatter", metric_patterns=("sale_price", "price"), dimension_patterns=(), aggregation="sum", business_question="How reliably does property size predict market listing price?"),
        ),
        comparisons=(
            ComparisonRule("category", "Days on Market by Property Type", ("property_type", "building_type"), ("days_on_market", "dom")),
        ),
        trends=(
            TrendRule(("sale_price", "price_per_sqft"), ("listing_date", "date"), "Tracking neighborhood property appreciation cycles"),
        ),
        risks=(
            RiskRule("aging_listing_stagnation", "Stagnant Listing Spike", "spike", metric_patterns=("days_on_market", "dom"), threshold=120.0, label="Requires investigation", recommended_action="Evaluate price reduction or staging upgrades on properties lingering beyond 120 days on market."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "median_listing_price", "high_demand_neighborhoods", "Focus brokerage marketing acquisitions on zip codes with low average days on market.", "Subject to local housing inventory availability."),
        ),
    ),

    # 37. Real Estate Investment
    DomainBlueprint(
        id="real_estate_investment",
        name="Real Estate Investment",
        description="Commercial real estate portfolios, capitalization rates (Cap Rate), net operating income (NOI), rent rolls, and tenant leases.",
        keywords=("cap_rate", "noi", "net_operating_income", "rent_roll", "tenant", "lease_term", "occupancy", "reit", "commercial_property", "square_footage", "yield"),
        alternative_domains=("Real Estate", "Finance", "Investment and Stock Market"),
        entities=(
            EntityRule("commercial_asset", "Investment Property / Asset", ("asset_id", "building_id", "property_name")),
            EntityRule("tenant_lease", "Tenant Lease", ("lease_id", "tenant_name", "suite_no")),
        ),
        kpis=(
            KpiRule("avg_cap_rate", "Average Portfolio Cap Rate", "Net Operating Income divided by current property asset value", ("numeric",), metric_patterns=("cap_rate", "capitalization_rate", "yield"), formula="mean", format="percentage", business_meaning="Unleveraged property investment yield"),
            KpiRule("total_noi", "Total Net Operating Income (NOI)", "Sum of rental revenues minus property operating expenses", ("numeric",), metric_patterns=("noi", "net_operating_income", "operating_income"), formula="sum", format="currency", business_meaning="Core property cash generation"),
            KpiRule("portfolio_occupancy", "Leased Occupancy Rate", "Percentage of rentable square footage under active lease", ("numeric",), metric_patterns=("occupancy", "leased_pct", "is_leased"), formula="mean", format="percentage", business_meaning="Real estate asset income security"),
        ),
        charts=(
            ChartRule("noi_by_asset", "NOI Contribution by Property Asset", "bar", dimension_patterns=("property_name", "building_id"), metric_patterns=("noi", "net_operating_income"), aggregation="sum", business_question="Which commercial properties produce the highest net operating income?"),
        ),
        comparisons=(
            ComparisonRule("category", "Cap Rates across Asset Classes (Industrial, Office, Retail)", ("asset_class", "property_type"), ("cap_rate", "noi")),
        ),
        trends=(
            TrendRule(("noi", "revenue"), ("year", "quarter"), "Monitoring multi-year commercial lease rental escalations"),
        ),
        risks=(
            RiskRule("lease_rollover_cliff", "Lease Expiration Rollover Risk", "spike", metric_patterns=("expiring_sqft", "rollover_pct"), threshold=0.30, label="Requires investigation", recommended_action="Commence early lease renewal negotiations with anchor tenants expiring within 18 months."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "total_noi", "below_market_rents", "Institute market-rate lease renewals on suites with expiring below-market rents.", "Subject to tenant lease agreements."),
        ),
    ),

    # 51. Telecom
    DomainBlueprint(
        id="telecom",
        name="Telecom",
        description="Telecommunications, subscriber churn, call detail records (CDR), broadband bandwidth, dropped calls, tower cells, and ARPU.",
        keywords=("telecom", "cdr", "subscriber", "broadband", "dropped_calls", "cell_tower", "roaming", "sim", "plan_type", "voice_minutes", "data_usage", "arpu", "telephony"),
        alternative_domains=("Network and Infrastructure Monitoring", "SaaS and Subscription", "Customer Support and Service"),
        entities=(
            EntityRule("telecom_subscriber", "Telecom Subscriber", ("subscriber_id", "msisdn", "phone_number", "account_id")),
            EntityRule("cell_tower", "Cell Tower / Sector", ("tower_id", "cell_id", "site_id", "base_station")),
        ),
        kpis=(
            KpiRule("telecom_arpu", "Average Revenue Per User (ARPU)", "Mean monthly billing revenue generated per mobile/broadband subscriber", ("numeric",), metric_patterns=("arpu", "revenue", "bill_amount", "charges"), formula="mean", format="currency", business_meaning="Subscriber monthly revenue yield"),
            KpiRule("call_drop_rate", "Dropped Call Rate", "Percentage of mobile calls terminated abnormally due to network fault", ("numeric",), metric_patterns=("dropped_calls", "drop_rate", "is_dropped"), formula="mean", format="percentage", business_meaning="Wireless network voice quality standard"),
            KpiRule("total_data_consumed", "Total Data Consumed (GB/TB)", "Aggregate gigabytes of mobile data payload transferred", ("numeric",), metric_patterns=("data_usage", "gigabytes", "gb_consumed"), formula="sum", format="number", business_meaning="Broadband network throughput volume"),
        ),
        charts=(
            ChartRule("churn_by_plan", "Churn Rate by Mobile Plan", "bar", dimension_patterns=("plan_type", "tariff", "tier"), metric_patterns=("churn", "is_churned"), aggregation="mean", business_question="Which mobile plan tiers suffer from the highest subscriber churn?"),
            ChartRule("data_by_tower", "Data Traffic by Cell Tower", "bar", dimension_patterns=("tower_id", "cell_name", "location"), metric_patterns=("data_usage", "gb_consumed"), aggregation="sum", business_question="Which wireless cell sites experience severe data bandwidth congestion?"),
        ),
        comparisons=(
            ComparisonRule("category", "Call Drop Rates across Network Vendors", ("vendor", "equipment_make"), ("dropped_calls", "drop_rate")),
        ),
        trends=(
            TrendRule(("data_usage", "gigabytes"), ("date", "month"), "Forecasting 5G mobile data bandwidth compound growth"),
        ),
        risks=(
            RiskRule("call_drop_spike", "Tower Quality Degradation", "spike", metric_patterns=("dropped_calls", "drop_rate"), threshold=0.03, label="Requires investigation", recommended_action="Dispatch RF engineers to inspect antenna azimuth and transmit power on affected cell towers."),
        ),
        recommendations=(
            RecommendationRule("customer_retention", "telecom_arpu", "high_data_users", "Offer discounted 5G unlimited data upgrade tiers to heavy 4G mobile users.", "Assumes 5G network coverage availability."),
        ),
    ),

    # 55. Government and Public Data
    DomainBlueprint(
        id="government_public",
        name="Government and Public Data",
        description="Public sector administration, census records, public programs, municipal services, civic licensing, and public welfare.",
        keywords=("government", "public_data", "census", "citizen", "municipality", "agency", "civic", "permit", "license", "welfare", "district", "public_service"),
        alternative_domains=("Government Finance and Public Finance", "Population and Demographics", "Crime and Public Safety"),
        entities=(
            EntityRule("citizen_applicant", "Citizen / Applicant", ("citizen_id", "applicant_id", "case_no")),
            EntityRule("public_service", "Public Service / Program", ("service_id", "program_name", "department")),
        ),
        kpis=(
            KpiRule("total_service_requests", "Total Civic Service Inquiries", "Sum of public service requests logged across municipal departments", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("request_id", "case_no"), formula="count_distinct", format="number", business_meaning="Civic administrative demand volume"),
            KpiRule("avg_processing_days", "Average Application Processing Time (Days)", "Mean days elapsed to review and approve civic applications", ("numeric",), metric_patterns=("processing_days", "turnaround_time", "resolution_days"), formula="mean", format="duration", business_meaning="Public administrative delivery responsiveness"),
        ),
        charts=(
            ChartRule("requests_by_district", "Service Requests by Municipal District", "bar", dimension_patterns=("district", "ward", "county"), metric_patterns=("request_id", "case_no"), aggregation="count", business_question="Which civic districts log the highest volume of municipal requests?"),
        ),
        comparisons=(
            ComparisonRule("category", "Processing Times across Municipal Agencies", ("agency", "department"), ("processing_days", "turnaround_time")),
        ),
        trends=(
            TrendRule(("request_id", "case_no"), ("filing_date", "date"), "Tracking seasonal public permitting surges"),
        ),
        risks=(
            RiskRule("civic_backlog_spike", "Administrative Backlog Surge", "spike", metric_patterns=("processing_days", "backlog_count"), threshold=30.0, label="Requires investigation", recommended_action="Streamline digital permit approval workflows and reassign municipal intake clerks."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "avg_processing_days", "slow_agencies", "Digitize intake document verification to eliminate manual paper processing delays.", "Subject to civic regulatory guidelines."),
        ),
    ),

    # 65. Environment and Climate
    DomainBlueprint(
        id="environment_climate",
        name="Environment and Climate",
        description="Air quality index (AQI), greenhouse gas emissions, carbon footprint (CO2), particulate matter (PM2.5), water quality, and pollution.",
        keywords=("climate", "environment", "aqi", "co2", "emissions", "pm25", "pm10", "pollution", "air_quality", "carbon_footprint", "water_quality", "greenhouse_gas"),
        alternative_domains=("Weather", "Energy and Utilities", "Science and Research"),
        entities=(
            EntityRule("monitoring_station", "Air / Environmental Monitoring Station", ("station_id", "site_name", "sensor_id")),
        ),
        kpis=(
            KpiRule("avg_aqi", "Average Air Quality Index (AQI)", "Mean AQI recorded across environmental monitoring stations", ("numeric",), metric_patterns=("aqi", "air_quality_index"), formula="mean", format="number", business_meaning="Ambient public air quality standard"),
            KpiRule("total_co2_emissions", "Total CO2 Emissions (Metric Tons)", "Sum of greenhouse gas emissions generated", ("numeric",), metric_patterns=("co2", "emissions", "carbon_tons", "ghg"), formula="sum", format="number", business_meaning="Gross environmental carbon footprint"),
            KpiRule("avg_pm25", "Average PM2.5 Concentration (ug/m3)", "Mean fine particulate matter concentration recorded", ("numeric",), metric_patterns=("pm25", "pm2_5", "particulate_matter"), formula="mean", format="number", business_meaning="Fine airborne particulate health hazard"),
        ),
        charts=(
            ChartRule("aqi_by_location", "Average AQI by City / Monitoring Station", "bar", dimension_patterns=("station_name", "city", "region"), metric_patterns=("aqi", "air_quality_index"), aggregation="mean", business_question="Which geographical regions experience the most hazardous air quality?"),
            ChartRule("emissions_trend", "Carbon Emissions Over Time", "line", dimension_patterns=("date", "year", "month"), metric_patterns=("co2", "emissions"), aggregation="sum", business_question="Are regional greenhouse gas emissions expanding or contracting?"),
        ),
        comparisons=(
            ComparisonRule("category", "Pollution Levels across Industrial vs Urban Zones", ("zone_type", "land_use"), ("aqi", "pm25")),
        ),
        trends=(
            TrendRule(("aqi", "pm25"), ("date", "month"), "Detecting seasonal winter thermal inversion air pollution spikes"),
        ),
        risks=(
            RiskRule("hazardous_aqi_spike", "Hazardous Air Quality Spike", "spike", metric_patterns=("aqi", "pm25"), threshold=200.0, label="Requires investigation", recommended_action="Issue municipal public health advisories and restrict heavy industrial emissions during hazardous AQI episodes."),
        ),
        recommendations=(
            RecommendationRule("risk_mitigation", "avg_aqi", "unhealthy_air", "Implement emergency vehicle traffic restrictions in urban corridors during persistent particulate inversions.", "Requires civic enforcement coordination."),
        ),
    ),

    # 66. Weather
    DomainBlueprint(
        id="weather",
        name="Weather",
        description="Meteorological observations, ambient temperature, precipitation, humidity, wind speed, barometric pressure, and snowfall.",
        keywords=("weather", "temperature", "precipitation", "rainfall", "humidity", "wind_speed", "barometric_pressure", "forecast", "meteorological", "dew_point", "celsius", "fahrenheit"),
        alternative_domains=("Environment and Climate", "Science and Research", "Agriculture"),
        entities=(
            EntityRule("weather_station", "Meteorological Weather Station", ("station_id", "station_name", "wmo_id")),
        ),
        kpis=(
            KpiRule("avg_temperature", "Average Ambient Temperature", "Mean temperature recorded over the observation timeframe", ("numeric",), metric_patterns=("temperature", "temp", "temp_c", "temp_f"), formula="mean", format="number", business_meaning="Central climate temperature baseline"),
            KpiRule("total_precipitation", "Total Precipitation (mm / inches)", "Sum of recorded rainfall and liquid precipitation", ("numeric",), metric_patterns=("precipitation", "rainfall", "rain_mm", "rain_inches"), formula="sum", format="number", business_meaning="Gross precipitation water volume"),
            KpiRule("avg_wind_speed", "Average Wind Speed (mph / km/h)", "Mean atmospheric wind velocity recorded", ("numeric",), metric_patterns=("wind_speed", "wind_mph", "wind_kmh"), formula="mean", format="number", business_meaning="Atmospheric wind conditions"),
        ),
        charts=(
            ChartRule("temp_trend", "Temperature Fluctuations Over Time", "line", dimension_patterns=("date", "timestamp", "day"), metric_patterns=("temperature", "temp"), aggregation="mean", business_question="How does ambient temperature fluctuate across the observation period?"),
            ChartRule("rainfall_by_month", "Monthly Precipitation Total", "bar", dimension_patterns=("month", "season"), metric_patterns=("precipitation", "rainfall"), aggregation="sum", business_question="What are the wettest and driest months of the year?"),
        ),
        comparisons=(
            ComparisonRule("category", "Temperature across Elevation / Stations", ("station_name", "city"), ("temperature", "temp")),
        ),
        trends=(
            TrendRule(("temperature", "precipitation"), ("date", "month"), "Tracking long-term seasonal meteorological departures"),
        ),
        risks=(
            RiskRule("extreme_weather_event", "Extreme Temperature Anomaly", "outlier", metric_patterns=("temperature", "temp"), threshold=3.0, label="Requires investigation", recommended_action="Verify station thermometer calibration and cross-reference with adjacent radar data."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "total_precipitation", "storm_events", "Prepare municipal storm drainage and flood abatement reservoirs prior to heavy precipitation events.", "Relies on meteorological radar forecast accuracy."),
        ),
    ),

    # 67. Science and Research
    DomainBlueprint(
        id="science_research",
        name="Science and Research",
        description="Scientific experiments, laboratory samples, control vs treatment trials, measurements, p-values, and publication datasets.",
        keywords=("experiment", "sample_id", "treatment", "control_group", "measurement", "p_value", "laboratory", "assay", "replicate", "hypothesis", "standard_deviation"),
        alternative_domains=("Clinical Research", "Pharmaceuticals", "Environment and Climate"),
        entities=(
            EntityRule("lab_sample", "Laboratory Sample / Specimen", ("sample_id", "specimen_id", "replicate_id")),
            EntityRule("experimental_run", "Experimental Run / Trial", ("run_id", "trial_id", "experiment_id")),
        ),
        kpis=(
            KpiRule("avg_experimental_value", "Average Experimental Measurement", "Mean quantitative response value measured across sample replicates", ("numeric",), metric_patterns=("value", "measurement", "concentration", "absorbance"), formula="mean", format="number", business_meaning="Central experimental biological or physical response"),
            KpiRule("total_samples_analyzed", "Total Samples / Replicates Analyzed", "Total biological or physical specimens processed", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("sample_id", "specimen_id"), formula="count_distinct", format="number", business_meaning="Experimental statistical sample power"),
        ),
        charts=(
            ChartRule("measurement_by_condition", "Response by Experimental Condition", "bar", dimension_patterns=("condition", "treatment_group", "dose"), metric_patterns=("value", "measurement"), aggregation="mean", business_question="How does the quantitative response vary between control and experimental treatments?"),
        ),
        comparisons=(
            ComparisonRule("category", "Response across Experimental Batches", ("batch_id", "operator"), ("value", "measurement")),
        ),
        trends=(
            TrendRule(("value", "measurement"), ("time_point", "run_id"), "Tracking kinetic reaction curves across time increments"),
        ),
        risks=(
            RiskRule("experimental_outlier", "Measurement Replicate Outlier", "outlier", metric_patterns=("value", "measurement"), threshold=3.0, label="Requires investigation", recommended_action="Inspect pipetting errors, contamination, or instrument calibration drift on outlier replicates."),
        ),
        recommendations=(
            RecommendationRule("quality_improvement", "avg_experimental_value", "high_variance", "Increase replicate sample size (n >= 5) on assays showing high coefficient of variation.", "Requires additional consumable laboratory reagents."),
        ),
    ),

    # 70. Crime and Public Safety
    DomainBlueprint(
        id="crime_public_safety",
        name="Crime and Public Safety",
        description="Law enforcement, crime incident reports, offense types, arrest rates, police precincts, emergency 911 calls, and response times.",
        keywords=("crime", "incident", "police", "precinct", "offense", "arrest", "911", "emergency", "dispatch_time", "felony", "misdemeanor", "public_safety"),
        alternative_domains=("Government and Public Data", "Transportation"),
        entities=(
            EntityRule("crime_incident", "Crime Incident / Case", ("incident_number", "case_id", "report_no")),
            EntityRule("police_precinct", "Police Precinct / Sector", ("precinct", "sector", "beat", "zone")),
        ),
        kpis=(
            KpiRule("total_incidents", "Total Crime Incidents", "Count of criminal offenses logged across jurisdictions", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("incident_number", "case_id"), formula="count_distinct", format="number", business_meaning="Total reported public crime incidence"),
            KpiRule("avg_dispatch_response", "Average Emergency Response Time (mins)", "Mean minutes from emergency call receipt to officer arrival on scene", ("numeric",), metric_patterns=("response_time", "dispatch_minutes", "arrival_time"), formula="mean", format="duration", business_meaning="Emergency public safety responsiveness"),
            KpiRule("arrest_clearance_rate", "Arrest Clearance Rate", "Percentage of criminal incidents cleared by arrest", ("numeric", "boolean"), metric_patterns=("is_arrest", "arrest_made", "cleared"), formula="mean", format="percentage", business_meaning="Law enforcement investigative resolution efficiency"),
        ),
        charts=(
            ChartRule("incidents_by_offense", "Incidents by Offense Category", "bar", dimension_patterns=("offense_type", "crime_category", "description"), metric_patterns=("incident_number", "case_id"), aggregation="count", business_question="What are the most frequent criminal offenses reported?"),
            ChartRule("incidents_by_precinct", "Incidents by Police Precinct", "bar", dimension_patterns=("precinct", "district", "beat"), metric_patterns=("incident_number", "case_id"), aggregation="count", business_question="Which police precincts manage the heaviest incident caseload?"),
        ),
        comparisons=(
            ComparisonRule("category", "Response Times across Geographic Zones", ("district", "precinct"), ("response_time", "dispatch_minutes")),
        ),
        trends=(
            TrendRule(("incident_number", "case_id"), ("incident_date", "date"), "Tracking seasonal summer property and violent crime surges"),
        ),
        risks=(
            RiskRule("violent_crime_surge", "Incident Wave Anomaly", "spike", metric_patterns=("incident_number", "case_id"), threshold=0.25, label="Requires investigation", recommended_action="Deploy targeted patrol visibility in hotspots experiencing consecutive incident spikes."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "avg_dispatch_response", "slow_dispatch", "Optimize beat patrol sector boundaries to reduce cross-district emergency transit times.", "Assumes police vehicle staffing capacity."),
        ),
    ),

    # 71. Population and Demographics
    DomainBlueprint(
        id="demographics",
        name="Population and Demographics",
        description="Census demographics, population counts, age distribution, gender ratios, household income, education attainment, and migration.",
        keywords=("population", "demographics", "census", "age_group", "gender", "household_income", "median_age", "fertility_rate", "mortality_rate", "migration", "ethnicity"),
        alternative_domains=("Government and Public Data", "Economics and Macroeconomics"),
        entities=(
            EntityRule("demographic_cohort", "Demographic Cohort / Tract", ("tract_id", "census_block", "fips", "cohort")),
        ),
        kpis=(
            KpiRule("total_population", "Total Population Count", "Aggregate headcount recorded across demographic survey tracts", ("numeric",), metric_patterns=("population", "total_pop", "headcount", "residents"), formula="sum", format="number", business_meaning="Gross demographic population size"),
            KpiRule("median_household_income", "Median Household Income", "Central household earnings benchmark across census tracts", ("numeric",), metric_patterns=("household_income", "income", "median_income"), formula="mean", format="currency", business_meaning="Demographic economic prosperity benchmark"),
            KpiRule("avg_median_age", "Average Median Age", "Mean population age in years", ("numeric",), metric_patterns=("age", "median_age"), formula="mean", format="number", business_meaning="Demographic population aging profile"),
        ),
        charts=(
            ChartRule("population_by_age", "Population Distribution by Age Cohort", "bar", dimension_patterns=("age_group", "age_bucket", "cohort"), metric_patterns=("population", "count"), aggregation="sum", business_question="What is the age pyramid structure of the analyzed population?"),
        ),
        comparisons=(
            ComparisonRule("category", "Income Levels across Geographic Counties / Regions", ("county", "state", "region"), ("household_income", "median_income")),
        ),
        trends=(
            TrendRule(("population", "total_pop"), ("census_year", "year"), "Tracking decennial population migration and growth patterns"),
        ),
        risks=(
            RiskRule("population_depopulation", "Severe Depopulation Anomaly", "drop", metric_patterns=("population", "residents"), threshold=0.10, label="Requires investigation", recommended_action="Review out-migration factors and regional industrial employment contractions."),
        ),
        recommendations=(
            RecommendationRule("resource_allocation", "total_population", "aging_population", "Direct municipal healthcare and public transit infrastructure toward districts with aging cohorts.", "Requires multi-year capital funding."),
        ),
    ),

    # 72. Economics and Macroeconomics
    DomainBlueprint(
        id="macroeconomics",
        name="Economics and Macroeconomics",
        description="Macroeconomic indicators, GDP, inflation rate (CPI), unemployment rate, interest rates, trade balance, and foreign exchange.",
        keywords=("gdp", "inflation", "cpi", "unemployment", "interest_rate", "macroeconomics", "trade_balance", "exports", "imports", "central_bank", "forex", "exchange_rate"),
        alternative_domains=("Finance", "Government Finance and Public Finance", "Population and Demographics"),
        entities=(
            EntityRule("country_economy", "Country / Sovereign Economy", ("country", "country_code", "iso3", "nation")),
        ),
        kpis=(
            KpiRule("gdp_value", "Gross Domestic Product (GDP)", "Total monetary value of goods and services produced by economy", ("numeric",), metric_patterns=("gdp", "gross_domestic_product", "nominal_gdp"), formula="sum", format="currency", business_meaning="Sovereign economic scale"),
            KpiRule("avg_inflation_rate", "Average Inflation Rate (CPI %)", "Mean annual percentage change in Consumer Price Index", ("numeric",), metric_patterns=("inflation", "cpi_change", "inflation_rate"), formula="mean", format="percentage", business_meaning="Macroeconomic currency purchasing power erosion"),
            KpiRule("unemployment_rate", "Unemployment Rate", "Percentage of civilian labor force currently unemployed and seeking work", ("numeric",), metric_patterns=("unemployment", "unemployment_rate"), formula="mean", format="percentage", business_meaning="Macroeconomic labor market slack"),
        ),
        charts=(
            ChartRule("gdp_growth_trend", "GDP Growth Over Time", "line", dimension_patterns=("year", "quarter", "date"), metric_patterns=("gdp", "gdp_growth"), aggregation="sum", business_question="How is national economic output expanding across macroeconomic cycles?"),
            ChartRule("cpi_by_country", "Inflation Rate by Country", "bar", dimension_patterns=("country", "nation"), metric_patterns=("inflation", "cpi"), aggregation="mean", business_question="Which sovereign nations experience the highest consumer price inflation?"),
        ),
        comparisons=(
            ComparisonRule("category", "Unemployment vs Inflation (Phillips Curve)", ("country", "year"), ("unemployment", "inflation")),
        ),
        trends=(
            TrendRule(("gdp", "cpi"), ("year", "quarter"), "Measuring economic business cycle expansions and recessions"),
        ),
        risks=(
            RiskRule("stagflation_signal", "Stagflation Signal Anomaly", "spike", metric_patterns=("inflation", "unemployment"), threshold=8.0, label="Requires investigation", recommended_action="Monitor simultaneous escalation of consumer prices and unemployment for stagflation risks."),
        ),
        recommendations=(
            RecommendationRule("risk_mitigation", "avg_inflation_rate", "high_inflation", "Hedge investment portfolios against persistent consumer price index inflation.", "Subject to central bank monetary policy shifts."),
        ),
    ),

    # 75. General / Unknown
    DomainBlueprint(
        id="general_unknown",
        name="General / Unknown",
        description="Dataset-agnostic baseline analytics when no specialized domain vocabulary is strongly identified.",
        keywords=(),
        alternative_domains=("General Business Analytics", "Retail", "Finance"),
        entities=(
            EntityRule("record", "Data Record", ("id", "record_id", "row_id", "index")),
        ),
        kpis=(
            KpiRule("total_records", "Total Records", "Count of rows in the dataset", ("numeric", "categorical"), metric_patterns=(), formula="count", format="number", business_meaning="Dataset record volume"),
        ),
        charts=(
            ChartRule("metric_distribution", "Primary Metric Distribution", "histogram", metric_patterns=(), aggregation="count", business_question="How are values distributed across the primary numeric measure?"),
        ),
        comparisons=(),
        trends=(),
        risks=(
            RiskRule("data_missingness", "High Missing Value Rate", "missing", threshold=0.20, label="Requires investigation", recommended_action="Audit data collection pipelines for missing field values."),
        ),
        recommendations=(
            RecommendationRule("data_quality", "total_records", "general_data", "Profile column types and ensure missing value rates remain under 5%.", "Applies universally across tabular datasets."),
        ),
    ),
]
