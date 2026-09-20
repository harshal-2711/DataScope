"""Healthcare, Hospital Management, Pharmaceuticals, and Clinical Research domain blueprints (Domains 23, 24, 25, 26, 27)."""
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
    # 23. Healthcare
    DomainBlueprint(
        id="healthcare",
        name="Healthcare",
        description="General healthcare, clinical encounters, diagnostic codes, patient admissions, treatments, and outpatient consultations.",
        keywords=("healthcare", "patient", "diagnosis", "icd", "treatment", "doctor", "physician", "clinic", "prescription", "vital_signs", "medical_record", "consultation"),
        alternative_domains=("Hospital Management", "Healthcare Operations", "Clinical Research"),
        entities=(
            EntityRule("patient", "Patient", ("patient_id", "mrn", "patient_name", "subject_id")),
            EntityRule("doctor", "Physician / Doctor", ("doctor_id", "physician_id", "provider_id", "clinician")),
            EntityRule("diagnosis", "Diagnosis / ICD Code", ("diagnosis", "icd_code", "condition", "primary_diagnosis")),
        ),
        kpis=(
            KpiRule("total_patients", "Total Patient Volume", "Count of distinct patients seen across clinical encounters", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("patient_id", "mrn"), formula="count_distinct", format="number", business_meaning="Clinical patient reach"),
            KpiRule("avg_treatment_cost", "Average Treatment / Encounter Cost", "Mean financial cost or charges per medical encounter", ("numeric",), metric_patterns=("cost", "charges", "billed_amount"), formula="mean", format="currency", business_meaning="Average clinical encounter expense"),
        ),
        charts=(
            ChartRule("patients_by_diagnosis", "Encounter Volume by Primary Diagnosis", "bar", dimension_patterns=("diagnosis", "condition", "department"), metric_patterns=("patient_id", "encounter_id"), aggregation="count", business_question="What are the most frequent diagnoses treated?"),
        ),
        comparisons=(
            ComparisonRule("category", "Encounter Costs across Medical Specialties", ("department", "specialty"), ("cost", "charges")),
        ),
        trends=(
            TrendRule(("patient_id", "encounter_id"), ("encounter_date", "date"), "Tracking seasonal outpatient volume surges"),
        ),
        risks=(
            RiskRule("cost_outlier_treatment", "Encounter Cost Anomaly", "outlier", metric_patterns=("cost", "charges"), threshold=3.5, label="Requires investigation", recommended_action="Audit medical billing line items against clinical treatment logs."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "total_patients", "high_volume_specialties", "Expand clinical staffing capacity in high-demand outpatient specialties.", "Subject to medical provider credentialing."),
        ),
    ),

    # 24. Hospital Management
    DomainBlueprint(
        id="hospital_management",
        name="Hospital Management",
        description="Inpatient wards, bed occupancy rates, length of stay (LOS), admissions, discharges, ICU capacity, and ER throughput.",
        keywords=("hospital", "bed_occupancy", "los", "length_of_stay", "admission", "discharge", "ward", "icu", "emergency_room", "nurse", "triage", "readmission"),
        alternative_domains=("Healthcare", "Healthcare Operations"),
        entities=(
            EntityRule("hospital_bed", "Hospital Bed / Ward", ("bed_id", "ward_id", "room_no", "unit")),
            EntityRule("inpatient_stay", "Inpatient Stay / Admission", ("admission_id", "encounter_id", "stay_id")),
        ),
        kpis=(
            KpiRule("avg_los", "Average Length of Stay (ALOS)", "Mean inpatient stay duration in days", ("numeric",), metric_patterns=("los", "length_of_stay", "days_admitted"), formula="mean", format="number", business_meaning="Inpatient bed turnover efficiency"),
            KpiRule("bed_occupancy_rate", "Bed Occupancy Rate", "Percentage of licensed hospital beds occupied", ("numeric",), metric_patterns=("occupancy", "bed_occupancy", "is_occupied"), formula="mean", format="percentage", business_meaning="Hospital capacity utilization"),
            KpiRule("readmission_rate", "30-Day Readmission Rate", "Proportion of discharged patients readmitted within 30 days", ("numeric", "boolean"), metric_patterns=("is_readmitted", "readmission"), formula="mean", format="percentage", business_meaning="Post-discharge care quality indicator"),
        ),
        charts=(
            ChartRule("los_by_ward", "Length of Stay by Ward / Unit", "bar", dimension_patterns=("ward", "unit", "department"), metric_patterns=("los", "length_of_stay"), aggregation="mean", business_question="Which hospital units experience the longest patient stays?"),
            ChartRule("occupancy_trend", "Bed Occupancy Trend", "line", dimension_patterns=("date", "admission_date"), metric_patterns=("occupancy", "beds_occupied"), aggregation="mean", business_question="How does hospital bed demand fluctuate over the week?"),
        ),
        comparisons=(
            ComparisonRule("category", "Readmission Rates across Departments", ("department", "ward"), ("is_readmitted", "readmission")),
        ),
        trends=(
            TrendRule(("occupancy", "admissions"), ("date", "admission_date"), "Monitoring acute care bed capacity pressures"),
        ),
        risks=(
            RiskRule("bed_capacity_strain", "Bed Capacity Saturation", "spike", metric_patterns=("occupancy", "bed_occupancy"), threshold=0.90, label="Requires investigation", recommended_action="Implement accelerated discharge coordination to free acute care beds."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "avg_los", "long_stays", "Establish multidisciplinary discharge planning on day 1 of admission to reduce ALOS.", "Must preserve patient clinical safety."),
        ),
    ),

    # 25. Healthcare Operations
    DomainBlueprint(
        id="healthcare_ops",
        name="Healthcare Operations",
        description="Operating room (OR) scheduling, clinic wait times, appointment no-shows, medical equipment utilization, and staffing ratios.",
        keywords=("operating_room", "wait_time", "no_show", "clinic_appointment", "or_utilization", "equipment_usage", "turnover_time", "nurse_ratio", "scheduling"),
        alternative_domains=("Hospital Management", "Healthcare"),
        entities=(
            EntityRule("appointment", "Clinic Appointment", ("appointment_id", "booking_id", "visit_id")),
            EntityRule("operating_room", "Operating Suite / Facility", ("or_id", "theatre_id", "room_id")),
        ),
        kpis=(
            KpiRule("no_show_rate", "Appointment No-Show Rate", "Percentage of scheduled patient appointments missed", ("numeric", "boolean"), metric_patterns=("is_no_show", "no_show", "missed"), formula="mean", format="percentage", business_meaning="Outpatient clinic scheduling efficiency"),
            KpiRule("avg_clinic_wait", "Average Patient Wait Time (mins)", "Mean wait time from arrival to clinician consultation", ("numeric",), metric_patterns=("wait_time", "waiting_minutes"), formula="mean", format="duration", business_meaning="Patient service access latency"),
        ),
        charts=(
            ChartRule("no_show_by_clinic", "No-Show Rate by Specialty Clinic", "bar", dimension_patterns=("clinic", "specialty", "department"), metric_patterns=("is_no_show", "no_show"), aggregation="mean", business_question="Which clinics suffer from the highest appointment absenteeism?"),
        ),
        comparisons=(
            ComparisonRule("category", "Wait Times by Appointment Time Slot", ("time_slot", "shift"), ("wait_time", "waiting_minutes")),
        ),
        trends=(
            TrendRule(("wait_time", "no_show"), ("appointment_date", "date"), "Tracking clinic delay patterns across days"),
        ),
        risks=(
            RiskRule("high_no_show", "Excessive No-Show Spike", "spike", metric_patterns=("is_no_show", "no_show"), threshold=0.20, label="Requires investigation", recommended_action="Deploy automated SMS appointment reminders 48 hours in advance."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "no_show_rate", "high_no_show", "Implement predictive double-booking on slots with high historical no-show probabilities.", "Care must be taken to prevent clinic waiting room overcrowding."),
        ),
    ),

    # 26. Pharmaceuticals
    DomainBlueprint(
        id="pharma",
        name="Pharmaceuticals",
        description="Drug manufacturing, pharmaceutical sales, lot numbers, active pharmaceutical ingredients (API), batch yields, and prescription volume.",
        keywords=("pharma", "drug", "medication", "dosage", "lot_number", "batch_yield", "prescription_volume", "rx", "active_ingredient", "api", "formulation", "stability"),
        alternative_domains=("Clinical Research", "Healthcare", "Manufacturing Quality"),
        entities=(
            EntityRule("drug_product", "Drug Product / Formulation", ("drug_id", "ndc", "medication_name", "product_code")),
            EntityRule("batch_lot", "Production Lot / Batch", ("lot_number", "batch_id", "lot_id")),
        ),
        kpis=(
            KpiRule("rx_sales_volume", "Total Prescription Volume (TRx)", "Total prescriptions dispensed or shipped", ("numeric",), metric_patterns=("rx_count", "prescriptions", "volume", "units"), formula="sum", format="number", business_meaning="Total commercial prescription demand"),
            KpiRule("avg_batch_yield", "Average Formulation Batch Yield", "Mean chemical yield percentage across manufacturing lots", ("numeric",), metric_patterns=("yield", "batch_yield", "yield_pct"), formula="mean", format="percentage", business_meaning="Pharmaceutical manufacturing process efficiency"),
        ),
        charts=(
            ChartRule("volume_by_medication", "Prescription Volume by Drug", "bar", dimension_patterns=("medication_name", "drug_name", "therapeutic_class"), metric_patterns=("rx_count", "volume"), aggregation="sum", business_question="Which medications command the highest prescription share?"),
        ),
        comparisons=(
            ComparisonRule("category", "Batch Yields across Formulation Plants", ("manufacturing_site", "plant"), ("yield", "batch_yield")),
        ),
        trends=(
            TrendRule(("rx_count", "volume"), ("date", "month"), "Monitoring monthly prescription fulfillment growth"),
        ),
        risks=(
            RiskRule("batch_yield_drop", "Subpotent Batch Yield Anomaly", "drop", metric_patterns=("yield", "batch_yield"), threshold=0.85, label="Requires investigation", recommended_action="Halt affected production lots and initiate QA root-cause investigation into raw materials."),
        ),
        recommendations=(
            RecommendationRule("quality_improvement", "avg_batch_yield", "low_yield", "Tighten ambient humidity controls during dry granulation formulation.", "Requires cleanroom climate validation."),
        ),
    ),

    # 27. Clinical Research
    DomainBlueprint(
        id="clinical_research",
        name="Clinical Research",
        description="Clinical trials, trial subjects, study cohorts, adverse events, primary endpoints, placebo vs treatment, and protocol deviations.",
        keywords=("clinical_trial", "subject_id", "cohort", "adverse_event", "placebo", "protocol_deviation", "endpoint", "phase_1", "phase_2", "phase_3", "screening", "randomization"),
        alternative_domains=("Pharmaceuticals", "Healthcare", "Science and Research"),
        entities=(
            EntityRule("study_subject", "Trial Subject / Participant", ("subject_id", "participant_id", "patient_id")),
            EntityRule("adverse_event", "Adverse Event (AE)", ("ae_id", "event_term", "toxicity_grade")),
            EntityRule("trial_arm", "Study Arm / Cohort", ("study_arm", "treatment_group", "cohort")),
        ),
        kpis=(
            KpiRule("enrolled_subjects", "Total Enrolled Subjects", "Count of randomized participants across study arms", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("subject_id", "participant_id"), formula="count_distinct", format="number", business_meaning="Trial recruitment target progress"),
            KpiRule("adverse_event_rate", "Adverse Event Incident Rate", "Average reported adverse events per subject", ("numeric",), metric_patterns=("ae_count", "event_count"), formula="mean", format="number", business_meaning="Investigational product safety profile"),
            KpiRule("protocol_deviations", "Total Protocol Deviations", "Count of protocol violations logged across study sites", ("numeric", "categorical"), metric_patterns=("deviation_count",), dimension_patterns=("deviation_id",), formula="sum", format="number", business_meaning="Trial execution compliance and data integrity"),
        ),
        charts=(
            ChartRule("ae_by_grade", "Adverse Events by Severity Grade", "bar", dimension_patterns=("toxicity_grade", "severity", "ae_term"), metric_patterns=("subject_id", "ae_id"), aggregation="count", business_question="What is the distribution of reported adverse events by severity?"),
            ChartRule("enrollment_by_site", "Subject Enrollment by Study Site", "bar", dimension_patterns=("site_id", "investigator", "country"), metric_patterns=("subject_id", "participant_id"), aggregation="count", business_question="Which clinical sites are leading trial enrollment?"),
        ),
        comparisons=(
            ComparisonRule("category", "Adverse Events between Treatment and Placebo", ("study_arm", "treatment_group"), ("ae_count", "is_adverse_event")),
        ),
        trends=(
            TrendRule(("subject_id", "enrollment"), ("enrollment_date", "date"), "Tracking trial accrual curves toward milestone targets"),
        ),
        risks=(
            RiskRule("serious_ae_spike", "Serious Adverse Event Spike", "spike", metric_patterns=("serious_ae", "sae"), threshold=1.0, label="Requires investigation", recommended_action="Notify Data Safety Monitoring Board (DSMB) and review unblinded safety signals."),
        ),
        recommendations=(
            RecommendationRule("risk_mitigation", "protocol_deviations", "high_deviations", "Conduct site re-training on primary endpoint assessment protocols.", "Assumes site study coordinator availability."),
        ),
    ),
]
