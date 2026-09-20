"""Logistics, Supply Chain, Travel, Airlines, and Hospitality domain blueprints (Domains 41, 42, 43, 44, 45, 46, 47, 48, 49, 50)."""
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
    # 41. Logistics
    DomainBlueprint(
        id="logistics",
        name="Logistics",
        description="Freight shipping, cargo transport, carrier contracts, freight costs, transit times, and demurrage.",
        keywords=("freight", "logistics", "cargo", "carrier", "shipment", "transit_time", "bol", "bill_of_lading", "container", "origin", "destination", "demurrage"),
        alternative_domains=("Supply Chain", "Transportation", "Delivery and Courier"),
        entities=(
            EntityRule("shipment", "Freight Shipment", ("shipment_id", "bol_number", "consignment_id", "container_no")),
            EntityRule("carrier", "Freight Carrier / Logistics Provider", ("carrier", "carrier_id", "freight_company")),
        ),
        kpis=(
            KpiRule("total_freight_cost", "Total Freight Spend", "Total monetary spend incurred on freight movements", ("numeric",), metric_patterns=("freight_cost", "cost", "shipping_cost"), formula="sum", format="currency", business_meaning="Gross logistics transportation expenditure"),
            KpiRule("avg_transit_days", "Average Transit Time (Days)", "Mean days elapsed between cargo dispatch and receipt", ("numeric",), metric_patterns=("transit_days", "transit_time", "duration_days"), formula="mean", format="duration", business_meaning="Logistics pipeline cycle velocity"),
        ),
        charts=(
            ChartRule("cost_by_carrier", "Freight Spend by Carrier", "bar", dimension_patterns=("carrier", "carrier_name"), metric_patterns=("freight_cost", "cost"), aggregation="sum", business_question="Which freight carriers manage the largest volume of shipping spend?"),
        ),
        comparisons=(
            ComparisonRule("category", "Transit Days across Freight Lanes", ("origin", "destination", "lane"), ("transit_days", "duration_days")),
        ),
        trends=(
            TrendRule(("freight_cost", "shipment_id"), ("ship_date", "date"), "Tracking seasonal freight rate and cargo volume surges"),
        ),
        risks=(
            RiskRule("demurrage_spike", "Demurrage / Detention Surcharge Surge", "spike", metric_patterns=("demurrage", "penalties"), threshold=1000.0, label="Requires investigation", recommended_action="Improve port customs clearance coordination to avoid container detention fees."),
        ),
        recommendations=(
            RecommendationRule("cost_reduction", "total_freight_cost", "high_carrier_rates", "Consolidate freight volume with core preferred carriers to negotiate tiered rate discounts.", "Subject to lane capacity availability."),
        ),
    ),

    # 42. Supply Chain
    DomainBlueprint(
        id="supply_chain",
        name="Supply Chain",
        description="Vendor performance, purchase orders, safety stock, lead times, order fill rate, and inventory turnover.",
        keywords=("supply_chain", "vendor", "purchase_order", "po_number", "safety_stock", "lead_time", "fill_rate", "supplier", "on_time_delivery", "otif", "inventory_turnover"),
        alternative_domains=("Logistics", "Manufacturing", "Retail Operations"),
        entities=(
            EntityRule("supplier", "Supplier / Vendor", ("supplier_id", "vendor_id", "vendor_name", "supplier")),
            EntityRule("purchase_order", "Purchase Order (PO)", ("po_number", "po_id", "order_id")),
        ),
        kpis=(
            KpiRule("otif_rate", "On-Time In-Full (OTIF) Rate", "Percentage of vendor deliveries meeting both delivery date and complete quantity", ("numeric", "boolean"), metric_patterns=("otif", "is_on_time", "on_time_delivery"), formula="mean", format="percentage", business_meaning="Supplier reliability and fulfillment accuracy"),
            KpiRule("avg_lead_time", "Average Supplier Lead Time (Days)", "Mean days from purchase order placement to receipt at warehouse", ("numeric",), metric_patterns=("lead_time", "lead_days", "procurement_days"), formula="mean", format="duration", business_meaning="Procurement lead time vulnerability"),
        ),
        charts=(
            ChartRule("otif_by_supplier", "OTIF Performance by Supplier", "bar", dimension_patterns=("supplier_name", "vendor_name"), metric_patterns=("otif", "is_on_time"), aggregation="mean", business_question="Which suppliers reliably deliver orders on time and in full?"),
        ),
        comparisons=(
            ComparisonRule("category", "Lead Times across Material Categories", ("category", "commodity"), ("lead_time", "lead_days")),
        ),
        trends=(
            TrendRule(("po_number", "spend"), ("po_date", "date"), "Tracking procurement commitment velocity across quarters"),
        ),
        risks=(
            RiskRule("supplier_lead_delay", "Supplier Lead Time Escalation", "spike", metric_patterns=("lead_time", "lead_days"), threshold=30.0, label="Requires investigation", recommended_action="Increase safety stock thresholds and identify secondary qualified vendors for delayed materials."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "otif_rate", "low_otif", "Institute supplier service level penalties and quarterly operational reviews for bottom-tier vendors.", "Dependent on vendor contract terms."),
        ),
    ),

    # 43. Delivery and Courier
    DomainBlueprint(
        id="delivery_courier",
        name="Delivery and Courier",
        description="Last-mile delivery, package couriers, parcel dispatch, delivery attempts, proof of delivery (POD), and route stops.",
        keywords=("courier", "parcel", "last_mile", "pod", "delivery_attempt", "package", "waybill", "tracking_number", "stop", "manifest", "dropoff"),
        alternative_domains=("Logistics", "Food Delivery", "Quick Commerce"),
        entities=(
            EntityRule("parcel", "Parcel / Package", ("tracking_number", "waybill_no", "package_id")),
            EntityRule("courier", "Delivery Courier / Driver", ("courier_id", "driver_name", "driver_id")),
        ),
        kpis=(
            KpiRule("first_attempt_delivery_rate", "First Attempt Delivery Rate", "Percentage of parcels successfully delivered on first stop", ("numeric", "boolean"), metric_patterns=("first_attempt", "success_first_try"), formula="mean", format="percentage", business_meaning="Last-mile delivery efficiency"),
            KpiRule("avg_stops_per_hour", "Average Stops Completed per Hour", "Mean delivery drops executed per driver hour", ("numeric",), metric_patterns=("stops_per_hour", "drop_rate"), formula="mean", format="number", business_meaning="Driver routing density"),
        ),
        charts=(
            ChartRule("deliveries_by_courier", "Deliveries Completed by Driver", "bar", dimension_patterns=("driver_name", "courier_id"), metric_patterns=("package_id", "tracking_number"), aggregation="count", business_question="Which drivers complete the highest parcel volume?"),
        ),
        comparisons=(
            ComparisonRule("category", "Failed Delivery Rates by Postal Code", ("postal_code", "zip_code", "city"), ("is_failed", "delivery_attempt")),
        ),
        trends=(
            TrendRule(("tracking_number", "package_id"), ("dispatch_date", "date"), "Monitoring holiday parcel surge volumes"),
        ),
        risks=(
            RiskRule("failed_attempt_surge", "Delivery Failure Surge", "spike", metric_patterns=("failed_delivery", "attempt_count"), threshold=0.15, label="Requires investigation", recommended_action="Implement recipient SMS time-window confirmation prior to vehicle dispatch."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "first_attempt_delivery_rate", "low_first_attempt", "Route deliveries using real-time recipient geocoding and customer delivery instructions.", "Requires GPS mobile app integration."),
        ),
    ),

    # 44. Transportation
    DomainBlueprint(
        id="transportation",
        name="Transportation",
        description="Commercial fleet management, vehicle mileage, fuel consumption, maintenance schedules, freight routes, and drivers.",
        keywords=("fleet", "vehicle", "mileage", "fuel_consumption", "odometer", "route", "truck", "driver", "freight_miles", "maintenance_cost", "gallons", "liters"),
        alternative_domains=("Logistics", "Public Transport", "Automotive"),
        entities=(
            EntityRule("fleet_vehicle", "Commercial Vehicle / Truck", ("vehicle_id", "truck_id", "vin", "license_plate")),
            EntityRule("driver", "Fleet Driver", ("driver_id", "operator_id", "driver_name")),
        ),
        kpis=(
            KpiRule("total_fleet_miles", "Total Fleet Miles Driven", "Aggregate miles or kilometers logged by vehicle fleet", ("numeric",), metric_patterns=("miles", "distance", "kilometers", "km"), formula="sum", format="number", business_meaning="Fleet asset utilization volume"),
            KpiRule("avg_fuel_economy", "Fleet Fuel Economy (MPG / L per 100km)", "Mean fuel efficiency across vehicle fleet", ("numeric",), metric_patterns=("mpg", "fuel_economy", "km_per_liter"), formula="mean", format="number", business_meaning="Operational energy efficiency"),
            KpiRule("total_fuel_cost", "Total Fuel Expenditure", "Gross monetary cost incurred on vehicle fuel", ("numeric",), metric_patterns=("fuel_cost", "fuel_expense", "diesel_cost"), formula="sum", format="currency", business_meaning="Direct operational fleet expense"),
        ),
        charts=(
            ChartRule("miles_by_vehicle", "Miles Logged by Vehicle", "bar", dimension_patterns=("vehicle_id", "truck_id", "model"), metric_patterns=("miles", "distance"), aggregation="sum", business_question="Which fleet vehicles experience the heaviest usage?"),
        ),
        comparisons=(
            ComparisonRule("category", "Fuel Economy across Vehicle Makes / Models", ("vehicle_model", "fleet_type"), ("mpg", "fuel_economy")),
        ),
        trends=(
            TrendRule(("miles", "fuel_cost"), ("date", "month"), "Tracking fleet fuel expenses against global oil price trends"),
        ),
        risks=(
            RiskRule("fuel_theft_outlier", "Fuel Consumption Anomaly", "outlier", metric_patterns=("fuel_consumption", "gallons"), threshold=3.0, label="Requires investigation", recommended_action="Cross-reference fuel card purchase logs against telematics GPS odometer data."),
        ),
        recommendations=(
            RecommendationRule("cost_reduction", "total_fuel_cost", "high_fuel_spend", "Optimize inter-city route planning and enforce vehicle speed-governing policies.", "Assumes telematics devices installed in cabs."),
        ),
    ),

    # 45. Public Transport
    DomainBlueprint(
        id="public_transport",
        name="Public Transport",
        description="Buses, metros, trains, passenger ridership, schedule adherence, transit stops, farebox revenue, and line delays.",
        keywords=("transit", "bus", "metro", "subway", "train", "ridership", "farebox", "schedule_adherence", "station", "stop", "transit_line", "delay_minutes"),
        alternative_domains=("Transportation", "Airlines and Aviation", "Government and Public Data"),
        entities=(
            EntityRule("transit_vehicle", "Transit Vehicle (Bus/Train)", ("vehicle_id", "bus_no", "train_id")),
            EntityRule("station_stop", "Transit Station / Stop", ("station_id", "stop_name", "terminal")),
            EntityRule("transit_line", "Transit Line / Route", ("route_id", "line_name", "corridor")),
        ),
        kpis=(
            KpiRule("total_ridership", "Total Transit Ridership", "Total passenger journeys completed across transit system", ("numeric",), metric_patterns=("ridership", "passengers", "tap_ins", "boardings"), formula="sum", format="number", business_meaning="Public mass transit mobility volume"),
            KpiRule("on_time_adherence", "Schedule On-Time Adherence", "Percentage of transit vehicle arrivals within 5 mins of schedule", ("numeric", "boolean"), metric_patterns=("on_time", "schedule_adherence"), formula="mean", format="percentage", business_meaning="Transit reliability for commuters"),
        ),
        charts=(
            ChartRule("ridership_by_line", "Ridership by Transit Line", "bar", dimension_patterns=("line_name", "route_id", "corridor"), metric_patterns=("ridership", "boardings"), aggregation="sum", business_question="Which transit corridors experience the highest commuter congestion?"),
        ),
        comparisons=(
            ComparisonRule("category", "On-Time Performance across Transit Lines", ("line_name", "route_id"), ("on_time", "delay_minutes")),
        ),
        trends=(
            TrendRule(("ridership", "boardings"), ("date", "hour"), "Measuring peak morning and evening commuter rush curves"),
        ),
        risks=(
            RiskRule("transit_delay_spike", "Severe Line Delay Surge", "spike", metric_patterns=("delay_minutes", "delay_time"), threshold=15.0, label="Requires investigation", recommended_action="Dispatch reserve buses to relieve stalled transit corridors."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "on_time_adherence", "low_adherence", "Adjust scheduled headway frequencies based on historical signal delay bottlenecks.", "Subject to municipal transit authority budgets."),
        ),
    ),

    # 46. Travel
    DomainBlueprint(
        id="travel",
        name="Travel",
        description="Travel agencies, itineraries, travel bookings, holiday packages, destinations, travelers, and travel insurance.",
        keywords=("travel", "itinerary", "booking", "destination", "traveler", "vacation", "package", "tour", "departure_date", "return_date", "travel_cost"),
        alternative_domains=("Tourism", "Airlines and Aviation", "Hospitality and Hotels"),
        entities=(
            EntityRule("booking", "Travel Booking / Package", ("booking_id", "reservation_id", "itinerary_id")),
            EntityRule("destination", "Travel Destination", ("destination", "city", "country", "resort")),
        ),
        kpis=(
            KpiRule("total_travel_bookings", "Total Travel Bookings", "Gross travel reservations processed", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("booking_id", "reservation_id"), formula="count_distinct", format="number", business_meaning="Travel business volume"),
            KpiRule("avg_package_price", "Average Trip / Package Price", "Mean expenditure per booked travel itinerary", ("numeric",), metric_patterns=("price", "cost", "total_price", "booking_amount"), formula="mean", format="currency", business_meaning="Average consumer travel spend"),
        ),
        charts=(
            ChartRule("bookings_by_destination", "Bookings by Travel Destination", "bar", dimension_patterns=("destination", "country", "city"), metric_patterns=("booking_id", "price"), aggregation="count", business_question="What are the top trending travel destinations?"),
        ),
        comparisons=(
            ComparisonRule("category", "Package Prices across Destinations", ("destination", "region"), ("price", "total_price")),
        ),
        trends=(
            TrendRule(("booking_id", "price"), ("departure_date", "booking_date"), "Capturing seasonal summer and holiday vacation booking surges"),
        ),
        risks=(
            RiskRule("destination_cancellation", "Destination Cancellation Spike", "spike", metric_patterns=("cancelled", "is_cancelled"), threshold=0.20, label="Requires investigation", recommended_action="Verify local travel advisories and weather alerts for affected destination routes."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "avg_package_price", "popular_destinations", "Package curated excursions and premium hotel upgrades on top holiday routes.", "Requires local partner agreements."),
        ),
    ),

    # 47. Tourism
    DomainBlueprint(
        id="tourism",
        name="Tourism",
        description="Tourist attractions, museum admissions, visitor numbers, tour guides, ticketing revenue, and tourist demographics.",
        keywords=("tourism", "tourist", "attraction", "museum", "visitor", "ticket_sales", "guided_tour", "souvenir", "monument", "heritage_site"),
        alternative_domains=("Travel", "Hospitality and Hotels"),
        entities=(
            EntityRule("attraction", "Tourist Attraction / Site", ("attraction_id", "site_name", "monument", "venue")),
            EntityRule("ticket", "Admission Ticket", ("ticket_id", "admission_no", "pass_id")),
        ),
        kpis=(
            KpiRule("total_visitors", "Total Tourist Visitors", "Total admissions logged across cultural and heritage sites", ("numeric",), metric_patterns=("visitors", "attendance", "ticket_count"), formula="sum", format="number", business_meaning="Tourism destination footfall"),
            KpiRule("total_ticket_revenue", "Total Ticketing Revenue", "Gross revenue generated from attraction admissions", ("numeric",), metric_patterns=("revenue", "sales", "ticket_revenue"), formula="sum", format="currency", business_meaning="Direct cultural tourism receipts"),
        ),
        charts=(
            ChartRule("visitors_by_attraction", "Visitors by Attraction Site", "bar", dimension_patterns=("site_name", "attraction_name"), metric_patterns=("visitors", "attendance"), aggregation="sum", business_question="Which tourist sites generate the highest attendance?"),
        ),
        comparisons=(
            ComparisonRule("category", "Visitor Origin Demographics", ("country_of_origin", "nationality"), ("visitors", "ticket_count")),
        ),
        trends=(
            TrendRule(("visitors", "ticket_revenue"), ("date", "month"), "Tracking annual tourism seasonality peaks"),
        ),
        risks=(
            RiskRule("visitor_drop_anomaly", "Sudden Tourist Influx Drop", "drop", metric_patterns=("visitors", "attendance"), threshold=0.35, label="Potential anomaly", recommended_action="Review international travel restrictions or localized weather disruptions."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "total_ticket_revenue", "peak_season", "Introduce timed-entry premium passes to reduce queue congestion at marquee sites.", "Assumes digital turnstile capability."),
        ),
    ),

    # 48. Airlines and Aviation
    DomainBlueprint(
        id="aviation",
        name="Airlines and Aviation",
        description="Commercial flights, passenger load factor, available seat miles (ASM), flight delays, routes, airports, and fuel burn.",
        keywords=("flight", "airline", "aircraft", "load_factor", "departure_delay", "arrival_delay", "tail_number", "origin_airport", "dest_airport", "pax", "fuel_burn", "airfare"),
        alternative_domains=("Travel", "Transportation", "Public Transport"),
        entities=(
            EntityRule("flight", "Commercial Flight", ("flight_number", "flight_id", "flight_no")),
            EntityRule("aircraft", "Aircraft / Tail", ("tail_number", "aircraft_type", "registration")),
            EntityRule("airport", "Airport", ("origin", "destination", "airport_code", "iata")),
        ),
        kpis=(
            KpiRule("passenger_load_factor", "Passenger Load Factor", "Percentage of available aircraft seats occupied by paying passengers", ("numeric",), metric_patterns=("load_factor", "occupancy", "seat_factor"), formula="mean", format="percentage", business_meaning="Aircraft seat capacity utilization"),
            KpiRule("avg_departure_delay", "Average Departure Delay (mins)", "Mean minutes commercial flights depart behind published schedule", ("numeric",), metric_patterns=("departure_delay", "dep_delay", "delay_minutes"), formula="mean", format="duration", business_meaning="Airline operational on-time performance"),
            KpiRule("total_passengers_flown", "Total Passengers Carried", "Sum of all passengers transported across flight network", ("numeric",), metric_patterns=("passengers", "pax", "passengers_count"), formula="sum", format="number", business_meaning="Airline passenger throughput"),
        ),
        charts=(
            ChartRule("delays_by_airline", "Average Delay by Airline Carrier", "bar", dimension_patterns=("airline", "carrier", "airline_name"), metric_patterns=("departure_delay", "arr_delay"), aggregation="mean", business_question="Which airlines suffer the longest operational flight delays?"),
            ChartRule("traffic_by_route", "Passenger Volume by Route", "bar", dimension_patterns=("route", "city_pair"), metric_patterns=("passengers", "pax"), aggregation="sum", business_question="Which city-pair flight corridors carry the highest passenger volume?"),
        ),
        comparisons=(
            ComparisonRule("category", "Load Factors across Flight Routes", ("route", "origin", "destination"), ("load_factor", "passengers")),
        ),
        trends=(
            TrendRule(("passengers", "flights"), ("flight_date", "date"), "Tracking seasonal holiday and business travel flight volume"),
        ),
        risks=(
            RiskRule("extreme_delay_wave", "Network Flight Delay Spike", "spike", metric_patterns=("departure_delay", "delay_minutes"), threshold=45.0, label="Requires investigation", recommended_action="Activate irregular operations (IROPS) crew re-pairing and aircraft turnaround buffers."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "avg_departure_delay", "delay_prone_routes", "Pad scheduled block times on historically congested airport arrival gates.", "Subject to gate slot availability."),
        ),
    ),

    # 49. Hospitality and Hotels
    DomainBlueprint(
        id="hospitality_hotels",
        name="Hospitality and Hotels",
        description="Hotels, resorts, room bookings, occupancy rates, average daily rate (ADR), RevPAR, guest stays, and room types.",
        keywords=("hotel", "resort", "adr", "revpar", "occupancy_rate", "room_type", "guest", "check_in", "check_out", "nightly_rate", "folio", "room_revenue"),
        alternative_domains=("Travel", "Tourism", "Food and Restaurant"),
        entities=(
            EntityRule("hotel_property", "Hotel Property / Resort", ("hotel_id", "property_name", "resort_id")),
            EntityRule("room_booking", "Room Reservation / Stay", ("reservation_id", "booking_id", "folio_no")),
            EntityRule("hotel_guest", "Hotel Guest", ("guest_id", "guest_name", "customer_id")),
        ),
        kpis=(
            KpiRule("adr", "Average Daily Rate (ADR)", "Mean rental revenue earned per occupied hotel room per day", ("numeric",), metric_patterns=("adr", "average_daily_rate", "room_rate"), formula="mean", format="currency", business_meaning="Hotel pricing power metric"),
            KpiRule("hotel_occupancy", "Hotel Room Occupancy Rate", "Percentage of available rooms occupied across the period", ("numeric",), metric_patterns=("occupancy", "occupancy_rate", "is_occupied"), formula="mean", format="percentage", business_meaning="Hotel capacity utilization"),
            KpiRule("revpar", "Revenue Per Available Room (RevPAR)", "Total room revenue divided by total available rooms", ("numeric",), metric_patterns=("revpar", "rev_par"), formula="mean", format="currency", business_meaning="Core hotel operational profitability efficiency"),
        ),
        charts=(
            ChartRule("revpar_by_property", "RevPAR by Hotel Property", "bar", dimension_patterns=("property_name", "hotel_name", "city"), metric_patterns=("revpar", "adr"), aggregation="mean", business_question="Which hotel properties generate the highest revenue per available room?"),
            ChartRule("occupancy_trend_hotel", "Occupancy Rate Over Time", "line", dimension_patterns=("date", "check_in_date"), metric_patterns=("occupancy", "occupancy_rate"), aggregation="mean", business_question="How does hotel room occupancy track across weekdays and weekends?"),
        ),
        comparisons=(
            ComparisonRule("category", "ADR Comparison across Room Types", ("room_type", "suite_type"), ("adr", "room_rate")),
        ),
        trends=(
            TrendRule(("occupancy", "revpar"), ("date", "month"), "Tracking annual tourist and convention seasonality"),
        ),
        risks=(
            RiskRule("low_occupancy_dip", "Severe Occupancy Contraction", "drop", metric_patterns=("occupancy", "occupancy_rate"), threshold=0.40, label="Requires investigation", recommended_action="Implement dynamic pricing discounts on online travel agencies (OTAs) for unbooked nights."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "revpar", "low_revpar", "Implement dynamic weekend yield management to capture leisure booking rate premiums.", "Requires dynamic pricing engine calibration."),
        ),
    ),

    # 50. Automotive
    DomainBlueprint(
        id="automotive",
        name="Automotive",
        description="Automotive dealerships, vehicle sales, car models, trim levels, warranties, test drives, and financing options.",
        keywords=("automotive", "dealership", "vehicle_sale", "car_model", "trim", "vin", "dealer", "test_drive", "financing", "warranty", "trade_in", "msrp"),
        alternative_domains=("Retail", "Manufacturing", "Transportation"),
        entities=(
            EntityRule("car_vehicle", "Vehicle / Model", ("vin", "vehicle_id", "model", "car_id")),
            EntityRule("dealership", "Dealership / Showroom", ("dealership_id", "dealer_name", "store_id")),
        ),
        kpis=(
            KpiRule("total_vehicles_sold", "Total Vehicles Sold", "Count of completed vehicle retail deliveries", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("vin", "sale_id"), formula="count_distinct", format="number", business_meaning="Automotive sales volume"),
            KpiRule("avg_vehicle_sale_price", "Average Vehicle Sale Price", "Mean transaction price realized per sold vehicle", ("numeric",), metric_patterns=("sale_price", "price", "amount", "transaction_price"), formula="mean", format="currency", business_meaning="Average vehicle unit monetization"),
        ),
        charts=(
            ChartRule("sales_by_model", "Vehicle Sales by Car Model", "bar", dimension_patterns=("model", "make_model", "car_name"), metric_patterns=("sale_price", "vin"), aggregation="sum", business_question="Which vehicle models drive the majority of dealership revenue?"),
        ),
        comparisons=(
            ComparisonRule("category", "Sales Performance across Dealership Locations", ("dealership_id", "dealer_name"), ("sale_price", "vin")),
        ),
        trends=(
            TrendRule(("vin", "sale_price"), ("sale_date", "date"), "Monitoring quarterly automotive sales incentives and delivery pushes"),
        ),
        risks=(
            RiskRule("dealer_inventory_stagnation", "Excess Lot Days on Market", "spike", metric_patterns=("days_in_inventory", "lot_days"), threshold=90.0, label="Requires investigation", recommended_action="Offer dealer cash rebates and promotional financing on aging lot inventory."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "total_vehicles_sold", "popular_trims", "Shift dealer inventory orders toward high-margin vehicle trim packages.", "Dependent on OEM factory production allocations."),
        ),
    ),
]
