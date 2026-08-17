from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.dataset import DatasetSummary
from app.services import dataset_service
from app.services.dataset_exceptions import DatasetError

router = APIRouter(tags=["dataset"])


@router.post("/dataset/upload", response_model=DatasetSummary)
async def upload_dataset(file: UploadFile = File(...)) -> dict:
    """Validate, read, and summarize an uploaded CSV/Excel dataset.

    The file is processed entirely in memory and is never written to
    disk or persisted between requests.
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
