import json

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.schemas.dataset import DatasetSummary, DrilldownResponse, RecommendationsResponse
from app.schemas.domain_blueprint import DecisionDashboardResponse, DomainIntelligenceResponse
from app.services import dataset_service
from app.services.dataset_exceptions import DatasetError

router = APIRouter(tags=["dataset"])


@router.post("/dataset/upload", response_model=DatasetSummary)
async def upload_dataset(file: UploadFile = File(...)) -> dict:
    """Validate, read, summarize, and store an uploaded CSV/Excel dataset.

    The file is parsed entirely in memory. The parsed DataFrame is then
    kept in the in-memory dataset store (see app/services/dataset_store.py)
    -- never written to disk -- so it can be aggregated by the
    recommendations endpoint without re-uploading. The response carries a
    dataset_id the frontend uses to refer back to it.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")

    try:
        contents = await file.read()
        return dataset_service.process_upload(
            filename=file.filename,
            contents=contents,
            content_type=file.content_type,
        )
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    finally:
        await file.close()


@router.get(
    "/dataset/{dataset_id}/recommendations", response_model=RecommendationsResponse
)
def get_dataset_recommendations(dataset_id: str) -> dict:
    """Return auto-generated, backend-aggregated chart recommendations.

    No axes, columns, or aggregations are selected by the caller -- the
    column profiler and recommendation engine derive everything from the
    dataset itself. All aggregation happens here over the full stored
    dataset; only the resulting chart-sized data is returned.
    """
    try:
        return dataset_service.get_recommendations(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/drilldown", response_model=DrilldownResponse
)
def get_dataset_drilldown(
    dataset_id: str,
    dimension: str = Query(
        None, description="Raw column name to filter by, e.g. 'Product'. "
        "Used for a single-level drill-down; ignored if `filters` is provided."
    ),
    value: str = Query(
        None, description="The selected value within that column, e.g. 'T-Shirts'. "
        "Used for a single-level drill-down; ignored if `filters` is provided."
    ),
    filters: str = Query(
        None,
        description=(
            "JSON-encoded list of {\"dimension\": ..., \"value\": ...} objects, "
            "applied in order, for a multi-level drill-down (e.g. Category="
            "Clothing then Product=T-Shirts). Takes precedence over "
            "`dimension`/`value` when provided."
        ),
    ),
) -> dict:
    """Data-driven drill-down for one or more stacked (dimension, value)
    filters.

    Recomputes KPIs, a trend-over-time chart (if a date column exists),
    and a secondary breakdown -- all server-side, over just the subset of
    the stored dataset matching every filter. Generic: works for any
    categorical column(s) and value(s) present in the dataset, in any
    order and to any depth, never hard-coded to a specific dataset's
    schema. A single (dimension, value) pair is a first-level drill-down;
    two or more is a second-level (or deeper) drill-down within the first.
    """
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
def get_dataset_domain_intelligence(dataset_id: str) -> dict:
    """Return comprehensive domain intelligence, entities, KPIs, charts, trends,
    comparisons, risks, and recommendations for a stored dataset."""
    try:
        return dataset_service.get_domain_intelligence(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/dataset/{dataset_id}/validation")
def get_dataset_validation(dataset_id: str) -> dict:
    """Return analysis validation and quality report (Valid, Needs Review, Unsupported)."""
    try:
        return dataset_service.get_validation_report(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/dataset/{dataset_id}/statistics")
def get_dataset_statistics(dataset_id: str) -> dict:
    """Return universal parametric and non-parametric statistics for any tabular dataset."""
    try:
        return dataset_service.get_universal_statistics(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/dataset/{dataset_id}/decision_dashboard",
    response_model=DecisionDashboardResponse,
)
def get_dataset_decision_dashboard(dataset_id: str) -> dict:
    """Return real-world, decision-oriented executive dashboard."""
    try:
        return dataset_service.get_decision_dashboard(dataset_id)
    except DatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
