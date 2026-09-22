"""Dataset processing logic.

Deliberately separate from the API layer (app/api/dataset.py) and from
any UI concerns. Everything here operates on raw bytes and pandas
DataFrames in memory only — nothing is written to disk, and the
original uploaded bytes are never mutated.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.core.config import settings
from app.services import dataset_store
from app.services.dataset_exceptions import (
    DatasetNotFoundError,
    EmptyDatasetError,
    EmptyFileError,
    FileTooLargeError,
    NoChartableColumnsError,
    UnreadableFileError,
    UnsupportedFileTypeError,
)
from app.domains.registry import get_blueprint_by_id, get_fallback_blueprint
from app.schemas.domain_blueprint import DomainIdentitySchema
from app.services.analysis_validator import run_analysis_quality_check
from app.services.chart_engine import generate_domain_charts
from app.services.column_profiler import profile_dataset
from app.services.competition_engine import (
    compute_competition_intelligence,
    validate_and_preview_benchmark,
)
from app.services.comparison_engine import compute_comparisons
from app.services.domain_detector import detect_domain
from app.services.entity_detector import detect_entities
from app.services.field_validator import validate_blueprint_fields
from app.services.insight_engine import generate_evidence_based_recommendations
from app.services.kpi_engine import compute_domain_kpis
from app.services.recommendation_engine import (
    compute_kpis,
    generate_drilldown,
    generate_recommendations,
    rank_columns,
)
from app.services.recommendations_intelligence_engine import compute_recommendations_intelligence
from app.services.risk_engine import compute_full_risk_intelligence, detect_risks_and_anomalies
from app.services.sports_cricket_service import (
    compute_cricket_ball_analytics,
    compute_cricket_match_analytics,
    detect_cricket_dataset_type,
)
from app.services.business_analytics_engine import generate_decision_dashboard
from app.services.data_quality_engine import compute_data_quality_report
from app.services.file_parser import FileDiagnostics, parse_tabular_file
from app.services.forecast_engine import compute_forecast
from app.services.grain_engine import detect_dataset_grain
from app.services.trend_engine import compute_trends, compute_trends_intelligence
from app.services.type_inference import detect_dataset_currency, infer_dataset_types
from app.services.universal_stats import compute_universal_statistics



def get_file_type(filename: str) -> str:
    """Resolve and validate the file extension. Returns a normalized type key."""
    extension = Path(filename).suffix.lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        supported = ", ".join(sorted(settings.ALLOWED_EXTENSIONS))
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension or 'unknown'}'. "
            f"Supported formats: {supported}"
        )
    return settings.ALLOWED_EXTENSIONS[extension]


def validate_content_type(content_type: Optional[str], file_type: str) -> None:
    """Best-effort MIME sniff check.

    Browsers/OSes report inconsistent MIME types for CSV/Excel files
    (text/csv, application/vnd.ms-excel, application/octet-stream, or
    nothing at all are all common and valid). Rather than maintain an
    exact allow-list that will false-positive-reject legitimate files,
    we only reject content types that are obviously wrong for a
    dataset file. The real validation is: can pandas parse it?
    """
    if not content_type:
        return

    obviously_wrong_prefixes = ("image/", "video/", "audio/")
    obviously_wrong_types = {"application/pdf", "text/html", "application/zip"}

    # .xlsx files are zip-based and sometimes reported as application/zip —
    # don't reject that combination.
    if content_type in obviously_wrong_types and not (
        file_type == "xlsx" and content_type == "application/zip"
    ):
        raise UnsupportedFileTypeError(
            f"The file's content type ('{content_type}') does not match a "
            "supported dataset format."
        )

    if content_type.startswith(obviously_wrong_prefixes):
        raise UnsupportedFileTypeError(
            f"The file's content type ('{content_type}') does not match a "
            "supported dataset format."
        )


def validate_size(contents: bytes) -> None:
    """Reject empty files and files over the configured size limit."""
    if len(contents) == 0:
        raise EmptyFileError("The uploaded file is empty.")

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise FileTooLargeError(
            f"File is {size_mb:.1f}MB, which exceeds the "
            f"{settings.MAX_UPLOAD_SIZE_MB}MB upload limit."
        )


def read_dataframe(contents: bytes, file_type: str) -> pd.DataFrame:
    """Parse the uploaded bytes into a DataFrame using robust fallback parser."""
    df, _ = parse_tabular_file(contents, "file", file_type)
    return df


def build_summary(
    df: pd.DataFrame,
    filename: str,
    file_type: str,
    dataset_id: str,
    diagnostics: Optional[FileDiagnostics] = None,
) -> Dict[str, Any]:
    """Build the metadata + preview payload returned to the frontend.

    Uses pandas' own JSON serialization (via to_json) to safely handle
    NaN -> null and numpy scalar types -> native Python types, rather
    than hand-rolling type coercion.
    Computes semantic type inference for all columns.
    """
    dtypes = {str(col): str(df[col].dtype) for col in df.columns}
    inferred = infer_dataset_types(df)
    detected_currency = detect_dataset_currency(df)

    preview_df = df.head(settings.PREVIEW_ROW_COUNT)
    preview: List[Dict[str, Any]] = json.loads(
        preview_df.to_json(orient="records", date_format="iso")
    )

    diag_dict = None
    if diagnostics:
        diag_dict = {
            "encoding_used": diagnostics.encoding_used,
            "delimiter_used": diagnostics.delimiter_used,
            "duplicate_columns_renamed": diagnostics.duplicate_columns_renamed,
            "malformed_rows_skipped": diagnostics.malformed_rows_skipped,
            "warnings": diagnostics.warnings,
        }

    return {
        "dataset_id": dataset_id,
        "filename": filename,
        "file_type": file_type,
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "columns": [str(col) for col in df.columns],
        "dtypes": dtypes,
        "inferred_columns": [c.to_dict() for c in inferred],
        "diagnostics": diag_dict,
        "detected_currency": detected_currency,
        "preview": preview,
    }


def process_upload(
    filename: str, contents: bytes, content_type: Optional[str]
) -> Dict[str, Any]:
    """Full validate -> read -> summarize -> store pipeline for one upload.

    The parsed DataFrame is retained in the in-memory dataset store (see
    app/services/dataset_store.py) so later requests -- chiefly the
    recommendations endpoint -- can aggregate over the full dataset without
    re-uploading the file. Only the dataset_id is handed back to the client.
    """
    file_type = get_file_type(filename)
    validate_content_type(content_type, file_type)
    validate_size(contents)
    df, diagnostics = parse_tabular_file(contents, filename, file_type)
    dataset_id = dataset_store.save_dataset(filename, file_type, df)
    return build_summary(df, filename, file_type, dataset_id, diagnostics)


def get_recommendations(dataset_id: str) -> Dict[str, Any]:
    """Profile + auto-generate chart recommendations for a stored dataset."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    if "recommendations" in entry.cache:
        return entry.cache["recommendations"]

    df = entry.df

    ranking = rank_columns(df)
    charts = generate_recommendations(df, ranking=ranking)

    if not charts:
        raise NoChartableColumnsError(
            "No columns in this dataset could be visualized automatically "
            "(every column is an identifier, empty, or constant)."
        )

    res = {
        "dataset_id": dataset_id,
        "chart_count": len(charts),
        "charts": [c.to_dict() for c in charts],
        "column_profiles": [
            {
                "name": p.name,
                "role": p.role,
                "dtype": p.dtype,
                "non_null_count": p.non_null_count,
                "null_count": p.null_count,
                "distinct_count": p.distinct_count,
                "reason": p.reason,
            }
            for p in ranking.profiles
        ],
        "kpis": compute_kpis(df, ranking),
    }
    entry.cache["recommendations"] = res
    return res


def get_drilldown(
    dataset_id: str, filters: List[Tuple[str, str]]
) -> Dict[str, Any]:
    """Data-driven drill-down for one or more stacked (dimension, value)
    filters -- KPIs, trend over time, and a secondary breakdown, all
    recomputed over just that slice of the full stored dataset. A single
    filter is a first-level drill-down (e.g. Category=Clothing); two
    filters is a second-level drill-down within the first (e.g.
    Category=Clothing AND Product=T-Shirts)."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    df = entry.df

    for dimension, _ in filters:
        if dimension not in df.columns:
            raise DatasetNotFoundError(
                f"Column '{dimension}' does not exist on this dataset."
            )

    result = generate_drilldown(df, filters)
    if result is None:
        described = " and ".join(f"{d} = '{v}'" for d, v in filters)
        raise NoChartableColumnsError(f"No rows found for {described}.")

    return {"dataset_id": dataset_id, **result}


def get_domain_intelligence(dataset_id: str) -> Dict[str, Any]:
    """Execute the full 15-step domain intelligence pipeline on a stored dataset.

    Returns the domain identity, detected entities, validated factual KPIs,
    domain-tailored charts, comparisons, time trends, risk signals,
    and evidence-based recommendations.
    """
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    if "domain_intelligence" in entry.cache:
        return entry.cache["domain_intelligence"]

    df = entry.df

    # 1. Profile dataset columns
    profiles = entry.cache.get("profiles") or profile_dataset(df)
    entry.cache["profiles"] = profiles

    # 2. Detect Domain Identity
    domain = entry.cache.get("domain") or detect_domain(df, profiles)
    entry.cache["domain"] = domain

    # 2b. Detect Dataset Grain & Analytical Representation
    dataset_grain = detect_dataset_grain(df)

    # 3. Detect Entities
    blueprint = get_blueprint_by_id(domain.domain_id) or get_fallback_blueprint()
    entities = detect_entities(df, profiles, blueprint)

    # 4. Validate Blueprint Fields & Rules
    capabilities = validate_blueprint_fields(df, profiles, blueprint, entities)

    # 5. Compute Factual KPIs
    kpis = compute_domain_kpis(df, capabilities.kpis)

    # 6. Generate Domain Charts
    charts = generate_domain_charts(df, capabilities.charts, dataset_grain.grain_label)

    # 7. Compute Comparisons
    comparisons = compute_comparisons(df, capabilities.comparisons)

    # 8. Compute Trends
    trends = compute_trends(df, capabilities.trends)

    # 9. Detect Statistical Risks & Anomalies
    currency = detect_dataset_currency(df)
    risk_intel = compute_full_risk_intelligence(df, dataset_id, profiles, domain, dataset_currency=currency)
    risks = risk_intel.risks

    # 10. Synthesize Evidence-based Recommendations
    recommendations = generate_evidence_based_recommendations(
        blueprint=blueprint,
        kpis=kpis,
        trends=trends,
        risks=risks,
        comparisons=comparisons,
        entities=entities,
    )

    # Check for specialized Cricket / IPL structure
    cricket_type = detect_cricket_dataset_type(df)
    if cricket_type == "match_level":
        domain = DomainIdentitySchema(
            domain_id="sports",
            name="Cricket / IPL Match Analytics",
            description="IPL and Cricket match-level analytics, toss impact, venue breakdown, and team wins.",
            confidence=0.96,
            evidence=["Detected IPL match-level structure with team, toss, venue, and winner columns"],
            alternative_domains=["Sports", "Sports Performance"],
        )
        cricket_res = compute_cricket_match_analytics(df)
        kpis = cricket_res["kpis"] + kpis
        charts = cricket_res["charts"] + charts
    elif cricket_type == "ball_by_ball":
        domain = DomainIdentitySchema(
            domain_id="sports_performance",
            name="Cricket / IPL Ball-by-Ball Analytics",
            description="Ball-by-ball delivery analytics, batting strike rates, bowling wickets, and over-by-over progression.",
            confidence=0.97,
            evidence=["Detected IPL ball-by-ball structure with batsman, bowler, over, and runs columns"],
            alternative_domains=["Sports", "Sports Performance"],
        )
        cricket_res = compute_cricket_ball_analytics(df)
        kpis = cricket_res["kpis"] + kpis
        charts = cricket_res["charts"] + charts

    # 11. Compute Universal Statistics for the Dataset
    universal_stats = compute_universal_statistics(df)

    # 12. Run Analysis Validation & Quality Checker
    validation_report = run_analysis_quality_check(
        df=df,
        domain=domain,
        kpis=kpis,
        charts=charts,
        trends=trends,
        risks=risks,
        recommendations=recommendations,
        skipped=capabilities.skipped,
    )

    # 13. Generate Real-World Decision-Oriented Dashboard
    decision_dashboard = generate_decision_dashboard(df, domain, profiles)
    decision_dashboard.dataset_id = dataset_id

    # 14. Compute Full Data Quality Report
    data_quality_rep = compute_data_quality_report(df, dataset_id, domain)

    def _to_dict(obj: Any) -> Dict[str, Any]:
        return obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()

    res = {
        "dataset_id": dataset_id,
        "domain": _to_dict(domain),
        "dataset_grain": dataset_grain.to_dict(),
        "entities": [_to_dict(e) for e in entities],
        "kpis": [_to_dict(k) for k in kpis],
        "charts": [_to_dict(c) for c in charts],
        "comparisons": [_to_dict(cp) for cp in comparisons],
        "trends": [_to_dict(t) for t in trends],
        "risks": [_to_dict(r) for r in risks],
        "recommendations": [_to_dict(rc) for rc in recommendations],
        "skipped_analyses": [_to_dict(s) for s in capabilities.skipped],
        "validation_report": validation_report,
        "universal_statistics": universal_stats,
        "decision_dashboard": _to_dict(decision_dashboard),
        "data_quality_report": _to_dict(data_quality_rep),
    }
    entry.cache["domain_intelligence"] = res
    return res


def get_decision_dashboard(dataset_id: str) -> Dict[str, Any]:
    """Return real-world, decision-oriented executive dashboard."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    if "decision_dashboard" in entry.cache:
        return entry.cache["decision_dashboard"]
    profiles = entry.cache.get("profiles") or profile_dataset(entry.df)
    entry.cache["profiles"] = profiles
    domain = entry.cache.get("domain") or detect_domain(entry.df, profiles)
    entry.cache["domain"] = domain
    dashboard = generate_decision_dashboard(entry.df, domain, profiles)
    dashboard.dataset_id = dataset_id
    res = dashboard.model_dump() if hasattr(dashboard, "model_dump") else dashboard.dict()
    entry.cache["decision_dashboard"] = res
    return res


def get_validation_report(dataset_id: str) -> Dict[str, Any]:
    """Return the analysis validation and quality report for a dataset."""
    intel = get_domain_intelligence(dataset_id)
    return intel["validation_report"]


def get_universal_statistics(dataset_id: str) -> Dict[str, Any]:
    """Return comprehensive universal descriptive statistics for a dataset."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    if "universal_statistics" in entry.cache:
        return entry.cache["universal_statistics"]
    res = compute_universal_statistics(entry.df)
    entry.cache["universal_statistics"] = res
    return res


def get_trends_intelligence(
    dataset_id: str,
    granularity: str = "auto",
    metric: Optional[str] = None,
    category_col: Optional[str] = None,
) -> Dict[str, Any]:
    """Return comprehensive time-series trends intelligence with multi-granularity and period comparisons."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    cache_key = f"trends_{granularity}_{metric}_{category_col}"
    if cache_key in entry.cache:
        return entry.cache[cache_key]

    profiles = entry.cache.get("profiles") or profile_dataset(entry.df)
    entry.cache["profiles"] = profiles
    domain = entry.cache.get("domain") or detect_domain(entry.df, profiles)
    entry.cache["domain"] = domain

    res = compute_trends_intelligence(
        df=entry.df,
        dataset_id=dataset_id,
        granularity=granularity,
        metric=metric,
        category_col=category_col,
        domain=domain,
    )
    res_dict = res.model_dump() if hasattr(res, "model_dump") else res.dict()
    entry.cache[cache_key] = res_dict
    return res_dict


def get_forecast(
    dataset_id: str,
    horizon: int = 7,
    metric: Optional[str] = None,
    granularity: Optional[str] = None,
    method: Optional[str] = "auto",
) -> Dict[str, Any]:
    """Return statistical time-series forecast with confidence intervals and limitations."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    cache_key = f"forecast_{horizon}_{metric}_{granularity}_{method}"
    if cache_key in entry.cache:
        return entry.cache[cache_key]

    res = compute_forecast(
        df=entry.df,
        dataset_id=dataset_id,
        horizon=horizon,
        metric=metric,
        granularity=granularity,
        method=method,
    )
    res_dict = res.model_dump() if hasattr(res, "model_dump") else res.dict()
    entry.cache[cache_key] = res_dict
    return res_dict


def get_data_quality_report(dataset_id: str) -> Dict[str, Any]:
    """Return comprehensive data quality and hygiene inspection report."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    if "data_quality" in entry.cache:
        return entry.cache["data_quality"]

    profiles = entry.cache.get("profiles") or profile_dataset(entry.df)
    entry.cache["profiles"] = profiles
    domain = entry.cache.get("domain") or detect_domain(entry.df, profiles)
    entry.cache["domain"] = domain

    rep = compute_data_quality_report(entry.df, dataset_id, domain)
    res_dict = rep.model_dump() if hasattr(rep, "model_dump") else rep.dict()
    entry.cache["data_quality"] = res_dict
    return res_dict


def get_risk_intelligence(dataset_id: str) -> Dict[str, Any]:
    """Return comprehensive domain-aware risk intelligence for a stored dataset."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    if "risk_intelligence" in entry.cache:
        return entry.cache["risk_intelligence"]

    profiles = entry.cache.get("profiles") or profile_dataset(entry.df)
    entry.cache["profiles"] = profiles
    domain = entry.cache.get("domain") or detect_domain(entry.df, profiles)
    entry.cache["domain"] = domain
    currency = detect_dataset_currency(entry.df)

    res = compute_full_risk_intelligence(
        df=entry.df,
        dataset_id=dataset_id,
        profiles=profiles,
        domain=domain,
        dataset_currency=currency,
    )
    res_dict = res.model_dump() if hasattr(res, "model_dump") else res.dict()
    entry.cache["risk_intelligence"] = res_dict
    return res_dict


def get_competition_intelligence(dataset_id: str) -> Dict[str, Any]:
    """Return universal, domain-aware competition and comparative benchmark intelligence."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    if "competition_intelligence" in entry.cache:
        return entry.cache["competition_intelligence"]

    profiles = entry.cache.get("profiles") or profile_dataset(entry.df)
    entry.cache["profiles"] = profiles
    domain = entry.cache.get("domain") or detect_domain(entry.df, profiles)
    entry.cache["domain"] = domain
    currency = detect_dataset_currency(entry.df)

    res = compute_competition_intelligence(
        df=entry.df,
        dataset_id=dataset_id,
        profiles=profiles,
        domain=domain,
        dataset_currency=currency,
        benchmark_df=entry.benchmark_df,
        benchmark_filename=entry.benchmark_filename,
    )
    res_dict = res.model_dump() if hasattr(res, "model_dump") else res.dict()
    entry.cache["competition_intelligence"] = res_dict
    return res_dict


def preview_market_benchmark(
    dataset_id: str,
    file_bytes: bytes,
    filename: str,
    file_type: str,
) -> Dict[str, Any]:
    """Parse benchmark file (CSV/XLSX/JSON) and return schema validation & quality preview without applying."""
    # Ensure dataset_id exists
    dataset_store.get_dataset_or_raise(dataset_id)
    
    benchmark_df, _ = parse_tabular_file(file_bytes, filename, file_type)
    res = validate_and_preview_benchmark(benchmark_df, filename)
    return res.model_dump() if hasattr(res, "model_dump") else res.dict()


def apply_market_benchmark(
    dataset_id: str,
    file_bytes: bytes,
    filename: str,
    file_type: str,
) -> Dict[str, Any]:
    """Parse, validate, and attach external market benchmark DataFrame to dataset entry."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    
    benchmark_df, _ = parse_tabular_file(file_bytes, filename, file_type)
    preview = validate_and_preview_benchmark(benchmark_df, filename)
    if not preview.is_valid:
        raise UnreadableFileError(f"Market benchmark validation failed: {preview.validation_summary}")
    
    dataset_store.attach_benchmark(dataset_id, filename, benchmark_df)
    return get_competition_intelligence(dataset_id)


def remove_market_benchmark(dataset_id: str) -> Dict[str, Any]:
    """Detach external market benchmark DataFrame and restore default competition state."""
    dataset_store.get_dataset_or_raise(dataset_id)
    dataset_store.remove_benchmark(dataset_id)
    return get_competition_intelligence(dataset_id)


def get_recommendations_intelligence(dataset_id: str) -> Dict[str, Any]:
    """Return universal, domain-aware evidence-based strategic recommendations."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    if "recommendations_intelligence" in entry.cache:
        return entry.cache["recommendations_intelligence"]

    profiles = entry.cache.get("profiles") or profile_dataset(entry.df)
    entry.cache["profiles"] = profiles
    domain = entry.cache.get("domain") or detect_domain(entry.df, profiles)
    entry.cache["domain"] = domain
    currency = detect_dataset_currency(entry.df)

    res = compute_recommendations_intelligence(
        df=entry.df,
        dataset_id=dataset_id,
        profiles=profiles,
        domain=domain,
        dataset_currency=currency,
        benchmark_df=entry.benchmark_df,
        benchmark_filename=entry.benchmark_filename,
    )
    res_dict = res.model_dump() if hasattr(res, "model_dump") else res.dict()
    entry.cache["recommendations_intelligence"] = res_dict
    return res_dict





