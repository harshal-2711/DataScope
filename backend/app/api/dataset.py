from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.schemas.dataset import DatasetSummary, DrilldownResponse, RecommendationsResponse
from app.schemas.report import ComprehensiveReportResponse
from app.schemas.domain_blueprint import (
    CompetitionIntelligenceResponse,
    DataQualityReportResponse,
    DecisionDashboardResponse,
    DomainIntelligenceResponse,
    ForecastResponse,
    MarketBenchmarkPreviewResponse,
    RecommendationsIntelligenceResponse,
    RiskIntelligenceResponse,
    TrendsIntelligenceResponse,
)
from app.services import dataset_service, dataset_store
from app.services.dataset_exceptions import DatasetError

from app.api.dependencies import TenantContext, get_optional_company
from app.db.session import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger("datascope.api.dataset")
logger.setLevel(logging.INFO)

router = APIRouter(tags=["dataset"])


def _verify_tenant_dataset_access(dataset_id: str, tenant: Optional[TenantContext], db: Session) -> None:
    """Ensure user cannot access another company's dataset."""
    if tenant and tenant.company_id:
        from app.models.dataset import Dataset
        ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if ds and ds.company_id and ds.company_id != tenant.company_id:
            raise HTTPException(status_code=404, detail="Dataset not found in this workspace.")


@router.post("/dataset/upload", response_model=DatasetSummary)
async def upload_dataset(
    file: UploadFile = File(...),
    tenant: Optional[TenantContext] = Depends(get_optional_company),
) -> dict:
    """Validate, read, summarize, and store an uploaded CSV/Excel dataset.

    The file is parsed and stored persistently in Supabase DB & Storage,
    hydrated into memory for calculation responses, and associated with
    the user's company workspace.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")

    try:
        contents = await file.read()
        company_id = tenant.company_id if tenant else None
        user_id = tenant.user_id if tenant else None
        return dataset_service.process_upload(
            filename=file.filename,
            contents=contents,
            content_type=file.content_type,
            company_id=company_id,
            user_id=user_id,
        )
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    finally:
        await file.close()


@router.get(
    "/dataset/{dataset_id}/recommendations", response_model=RecommendationsResponse
)
def get_dataset_recommendations(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return auto-generated, backend-aggregated chart recommendations."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    try:
        return dataset_service.get_recommendations(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/drilldown", response_model=DrilldownResponse
)
def get_dataset_drilldown(
    dataset_id: str,
    dimension: Optional[str] = Query(
        None, description="Raw column name to filter by, e.g. 'Product'. "
        "Used for a single-level drill-down; ignored if `filters` is provided."
    ),
    value: Optional[str] = Query(
        None, description="The selected value within that column, e.g. 'T-Shirts'. "
        "Used for a single-level drill-down; ignored if `filters` is provided."
    ),
    filters: Optional[str] = Query(
        None,
        description=(
            "JSON-encoded list of {\"dimension\": ..., \"value\": ...} objects, "
            "applied in order, for a multi-level drill-down (e.g. Category="
            "Clothing then Product=T-Shirts). Takes precedence over "
            "`dimension`/`value` when provided."
        ),
    ),
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Data-driven drill-down for one or more stacked (dimension, value) filters."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    filter_pairs = []
    if filters:
        try:
            parsed = json.loads(filters)
            filter_pairs = [(str(f["dimension"]), str(f["value"])) for f in parsed]
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(
                status_code=400,
                detail="`filters` must be a JSON list of {\"dimension\", \"value\"} objects.",
            ) from exc
    elif dimension is not None and value is not None:
        filter_pairs = [(dimension, value)]
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either `dimension` and `value`, or `filters`.",
        )

    try:
        return dataset_service.get_drilldown(dataset_id, filter_pairs)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/intelligence", response_model=DomainIntelligenceResponse
)
def get_dataset_domain_intelligence(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return comprehensive domain intelligence, entities, KPIs, charts, trends,
    comparisons, risks, and recommendations for a stored dataset."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    try:
        return dataset_service.get_domain_intelligence(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/dataset/{dataset_id}/validation")
def get_dataset_validation(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return analysis validation and quality report (Valid, Needs Review, Unsupported)."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    try:
        return dataset_service.get_validation_report(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/dataset/{dataset_id}/statistics")
def get_dataset_statistics(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return universal parametric and non-parametric statistics for any tabular dataset."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    try:
        return dataset_service.get_universal_statistics(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/decision_dashboard",
    response_model=DecisionDashboardResponse,
)
def get_dataset_decision_dashboard(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return real-world, decision-oriented executive dashboard."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    try:
        return dataset_service.get_decision_dashboard(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc



@router.get(
    "/dataset/{dataset_id}/trends",
    response_model=TrendsIntelligenceResponse,
)
def get_dataset_trends(
    dataset_id: str,
    granularity: str = Query("auto", description="Time granularity: 'auto', 'D', 'W', 'M', 'Q', or 'Y'"),
    metric: Optional[str] = Query(None, description="Continuous numeric metric to aggregate over time"),
    category_col: Optional[str] = Query(None, description="Categorical dimension for segment breakdown over time"),
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return comprehensive time-series trends intelligence, period comparisons, volatility, and spikes."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    try:
        return dataset_service.get_trends_intelligence(
            dataset_id=dataset_id,
            granularity=granularity,
            metric=metric,
            category_col=category_col,
        )
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/forecast",
    response_model=ForecastResponse,
)
def get_dataset_forecast(
    dataset_id: str,
    horizon: int = Query(7, ge=1, le=60, description="Forecast horizon in time periods (1-60)"),
    metric: Optional[str] = Query(None, description="Continuous numeric metric to forecast"),
    granularity: Optional[str] = Query(None, description="Time aggregation granularity ('D', 'W', 'M', 'Q', 'Y')"),
    method: Optional[str] = Query("auto", description="Forecasting method ('auto', 'holt_linear', 'linear_trend', 'moving_average', 'naive')"),
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return statistical time-series forecast with confidence intervals and limitations."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    try:
        return dataset_service.get_forecast(
            dataset_id=dataset_id,
            horizon=horizon,
            metric=metric,
            granularity=granularity,
            method=method,
        )
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/data_quality",
    response_model=DataQualityReportResponse,
)
def get_dataset_data_quality(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return comprehensive data quality and hygiene validation report."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    try:
        return dataset_service.get_data_quality_report(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/risk",
    response_model=RiskIntelligenceResponse,
)
def get_dataset_risk_intelligence(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return universal, domain-aware risk intelligence and statistical anomaly detections."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    logger.info("[ROUTE-HIT] GET /api/dataset/%s/risk received", dataset_id)
    try:
        res = dataset_service.get_risk_intelligence(dataset_id)
        logger.info("[ROUTE-SUCCESS] GET /api/dataset/%s/risk completed", dataset_id)
        return res
    except DatasetError as exc:
        logger.warning(
            "[APPLICATION-404] Dataset '%s' failed in risk endpoint: %s (Status: %d, Store entries: %d)",
            dataset_id,
            exc.message,
            exc.status_code,
            len(dataset_store._store),
        )
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/competition",
    response_model=CompetitionIntelligenceResponse,
)
def get_dataset_competition_intelligence(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return universal, domain-aware competition intelligence and comparative benchmarks."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    logger.info("[ROUTE-HIT] GET /api/dataset/%s/competition received", dataset_id)
    try:
        res = dataset_service.get_competition_intelligence(dataset_id)
        logger.info("[ROUTE-SUCCESS] GET /api/dataset/%s/competition completed", dataset_id)
        return res
    except DatasetError as exc:
        logger.warning(
            "[APPLICATION-404] Dataset '%s' failed in competition endpoint: %s (Status: %d, Store entries: %d)",
            dataset_id,
            exc.message,
            exc.status_code,
            len(dataset_store._store),
        )
@router.post(
    "/dataset/{dataset_id}/benchmark/preview",
    response_model=MarketBenchmarkPreviewResponse,
)
async def preview_market_benchmark_file(
    dataset_id: str,
    file: UploadFile = File(...),
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Validate an uploaded market benchmark file and return metadata preview & quality warnings."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    if not file.filename:
        raise HTTPException(status_code=400, detail="No benchmark file was provided.")

    from pathlib import Path
    from app.core.config import settings
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS.keys())}.",
        )
    file_type = settings.ALLOWED_EXTENSIONS[ext]

    try:
        contents = await file.read()
        return dataset_service.preview_market_benchmark(
            dataset_id=dataset_id,
            file_bytes=contents,
            filename=file.filename,
            file_type=file_type,
        )
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/dataset/{dataset_id}/benchmark/apply",
    response_model=CompetitionIntelligenceResponse,
)
async def apply_market_benchmark_file(
    dataset_id: str,
    file: UploadFile = File(...),
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Validate and attach an external market benchmark dataset to the active session."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    if not file.filename:
        raise HTTPException(status_code=400, detail="No benchmark file was provided.")

    from pathlib import Path
    from app.core.config import settings
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS.keys())}.",
        )
    file_type = settings.ALLOWED_EXTENSIONS[ext]

    try:
        contents = await file.read()
        return dataset_service.apply_market_benchmark(
            dataset_id=dataset_id,
            file_bytes=contents,
            filename=file.filename,
            file_type=file_type,
        )
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/dataset/{dataset_id}/benchmark",
    response_model=CompetitionIntelligenceResponse,
)
def remove_market_benchmark_file(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Detach external market benchmark dataset and restore default competition state."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    try:
        return dataset_service.remove_market_benchmark(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/recommendations_intelligence",
    response_model=RecommendationsIntelligenceResponse,
    operation_id="get_dataset_recommendations_intelligence",
)
def get_dataset_recommendations_intelligence(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return universal, domain-aware evidence-based strategic recommendations."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    logger.info("[ROUTE-HIT] GET /api/dataset/%s/recommendations_intelligence received", dataset_id)
    try:
        res = dataset_service.get_recommendations_intelligence(dataset_id)
        logger.info("[ROUTE-SUCCESS] GET /api/dataset/%s/recommendations_intelligence completed", dataset_id)
        return res
    except DatasetError as exc:
        logger.warning(
            "[APPLICATION-404] Dataset '%s' failed in recommendations endpoint: %s (Status: %d, Store entries: %d)",
            dataset_id,
            exc.message,
            exc.status_code,
            len(dataset_store._store),
        )
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/recommendations-intelligence",
    response_model=RecommendationsIntelligenceResponse,
    operation_id="get_dataset_recommendations_intelligence_alias",
)
def get_dataset_recommendations_intelligence_alias(
    dataset_id: str,
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Alias for recommendations_intelligence endpoint."""
    return get_dataset_recommendations_intelligence(dataset_id, tenant=tenant, db=db)


@router.get(
    "/dataset/{dataset_id}/report",
    response_model=ComprehensiveReportResponse,
    operation_id="get_dataset_comprehensive_report",
)
def get_dataset_comprehensive_report(
    dataset_id: str,
    sections: Optional[str] = Query(None, description="Comma-separated list of section IDs to filter"),
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
) -> dict:
    """Return unified, multi-module executive business report for dataset."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    logger.info("[ROUTE-HIT] GET /api/dataset/%s/report received", dataset_id)
    sec_list = [s.strip() for s in sections.split(",")] if sections else None
    try:
        res = dataset_service.get_comprehensive_report(dataset_id, sections=sec_list)
        logger.info("[ROUTE-SUCCESS] GET /api/dataset/%s/report completed", dataset_id)
        return res
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/report/docx",
    operation_id="download_dataset_report_docx",
)
def download_dataset_report_docx(
    dataset_id: str,
    sections: Optional[str] = Query(None, description="Comma-separated list of section IDs to include"),
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
):
    """Generate and stream formatted Word (.docx) document for the executive report."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    logger.info("[ROUTE-HIT] GET /api/dataset/%s/report/docx received", dataset_id)
    sec_list = [s.strip() for s in sections.split(",")] if sections else None
    try:
        buf, filename = dataset_service.export_report_docx(dataset_id, sections=sec_list)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/report/pdf",
    operation_id="download_dataset_report_pdf",
)
def download_dataset_report_pdf(
    dataset_id: str,
    sections: Optional[str] = Query(None, description="Comma-separated list of section IDs to include"),
    tenant: Optional[TenantContext] = Depends(get_optional_company),
    db: Session = Depends(get_db),
):
    """Generate and stream formatted PDF (.pdf) document for the executive report."""
    _verify_tenant_dataset_access(dataset_id, tenant, db)
    logger.info("[ROUTE-HIT] GET /api/dataset/%s/report/pdf received", dataset_id)
    sec_list = [s.strip() for s in sections.split(",")] if sections else None
    try:
        buf, filename = dataset_service.export_report_pdf(dataset_id, sections=sec_list)
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc







