"""Image upload endpoints."""

from __future__ import annotations

from typing import Literal

import structlog
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.container import deps
from app.domains.images.service import ImageUploadError
from app.domains.images.submission_job_models import SubmissionJobStatusResponse
from app.domains.images.submission_job_service import SubmissionJobService

logger = structlog.get_logger()

router = APIRouter(prefix="/images", tags=["images"])


def _require_code(code: str | None) -> None:
    """Validate the upload secret code."""
    settings = get_settings()
    if not settings.upload_secret_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload secret code is not configured",
        )
    if not code or code != settings.upload_secret_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid upload code",
        )


def _build_upload_form_html(environment: str) -> str:
    """Build the HTML upload form."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VandyGuessr - Upload {environment.title()} Photos</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }}
        .env-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 1rem;
            background: {("#4CAF50" if environment == "outdoor" else "#2196F3")};
            color: white;
        }}
        form {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .file-input-container {{
            margin-bottom: 1rem;
        }}
        label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }}
        input[type="file"] {{
            width: 100%;
            padding: 12px;
            border: 2px dashed #ccc;
            border-radius: 4px;
            cursor: pointer;
        }}
        button {{
            width: 100%;
            padding: 14px;
            background: #D4AF37;
            color: black;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
        }}
        button:hover {{
            background: #C9A227;
        }}
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        .hint {{
            font-size: 0.875rem;
            color: #666;
            margin-top: 1rem;
        }}
    </style>
</head>
<body>
    <h1>VandyGuessr Upload</h1>
    <span class="env-badge">{environment.upper()}</span>

    <form method="POST" enctype="multipart/form-data">
        <div class="file-input-container">
            <label for="files">Select photos with GPS data:</label>
            <input
                type="file"
                id="files"
                name="files"
                accept="image/jpeg,image/png,image/heic,image/heif"
                multiple
                required
            >
        </div>
        <button type="submit" id="submit-btn">Upload Photos</button>
    </form>

    <p class="hint">
        Photos must have GPS location data (EXIF). Most iPhone/Android photos include this automatically.
    </p>

    <script>
        const form = document.querySelector('form');
        const btn = document.getElementById('submit-btn');
        form.addEventListener('submit', () => {{
            btn.disabled = true;
            btn.textContent = 'Queueing...';
        }});
    </script>
</body>
</html>"""


def _build_result_html(
    environment: str,
    *,
    total: int,
    queued_count: int,
    queued_items: list[dict[str, str]],
    failed_items: list[dict[str, str]],
    code: str,
) -> str:
    """Build the HTML result page."""
    success_items = ""
    failed_items_html = ""

    for result in queued_items:
        if result.get("filename"):
            success_items += f"""
            <li class="success">
                <strong>{result["filename"]}</strong>
                <br><small>Queued for background processing</small>
            </li>"""
    for result in failed_items:
        if result.get("filename"):
            failed_items_html += f"""
            <li class="failed">
                <strong>{result["filename"]}</strong>
                <br><small>{result["error"]}</small>
            </li>"""

    success_section = ""
    if queued_count > 0:
        success_section = f"""
        <div class="section success-section">
            <h2>Queued ({queued_count})</h2>
            <ul>{success_items}</ul>
        </div>"""

    failed_section = ""
    if len(failed_items) > 0:
        failed_section = f"""
        <div class="section failed-section">
            <h2>Failed ({len(failed_items)})</h2>
            <ul>{failed_items_html}</ul>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VandyGuessr - Upload Results</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }}
        h2 {{
            font-size: 1.1rem;
            margin: 0 0 0.5rem 0;
        }}
        .summary {{
            background: white;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-text {{
            font-size: 1.25rem;
            font-weight: 600;
        }}
        .section {{
            background: white;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .success-section h2 {{ color: #4CAF50; }}
        .failed-section h2 {{ color: #f44336; }}
        ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        li {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        li:last-child {{ border-bottom: none; }}
        li.success {{ color: #2e7d32; }}
        li.failed {{ color: #c62828; }}
        small {{ color: #666; }}
        .actions {{
            margin-top: 1rem;
        }}
        a.btn {{
            display: block;
            text-align: center;
            padding: 14px;
            background: #D4AF37;
            color: black;
            text-decoration: none;
            border-radius: 4px;
            font-weight: 600;
        }}
        a.btn:hover {{
            background: #C9A227;
        }}
    </style>
</head>
<body>
    <h1>Upload Results</h1>

    <div class="summary">
        <span class="summary-text">
            {queued_count} of {total} photo(s) queued
        </span>
    </div>

    {success_section}
    {failed_section}

    <div class="actions">
        <a href="?code={code}&environment={environment}" class="btn">Upload More Photos</a>
    </div>
</body>
</html>"""


def _build_error_html(error: str, environment: str, code: str) -> str:
    """Build the HTML error page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VandyGuessr - Error</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            font-size: 1.5rem;
            color: #c62828;
        }}
        .error-box {{
            background: #ffebee;
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #ffcdd2;
            margin-bottom: 1rem;
        }}
        a.btn {{
            display: block;
            text-align: center;
            padding: 14px;
            background: #D4AF37;
            color: black;
            text-decoration: none;
            border-radius: 4px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <h1>Error</h1>
    <div class="error-box">{error}</div>
    <a href="?code={code}&environment={environment}" class="btn">Try Again</a>
</body>
</html>"""


@router.get("/upload", response_class=HTMLResponse)
async def get_upload_form(
    code: str | None = Query(default=None),
    environment: Literal["indoor", "outdoor"] | None = Query(default=None),
) -> HTMLResponse:
    """Return HTML form for image upload."""
    # Validate code
    try:
        _require_code(code)
    except HTTPException as e:
        return HTMLResponse(
            content=f"""<!DOCTYPE html>
<html><head><title>Error</title></head>
<body><h1>Unauthorized</h1><p>{e.detail}</p></body></html>""",
            status_code=e.status_code,
        )

    # Validate environment
    if environment is None:
        return HTMLResponse(
            content="""<!DOCTYPE html>
<html><head><title>Error</title></head>
<body><h1>Missing Parameter</h1>
<p>Please specify environment=indoor or environment=outdoor in the URL.</p>
</body></html>""",
            status_code=400,
        )

    return HTMLResponse(content=_build_upload_form_html(environment))


@router.post("/upload", response_class=HTMLResponse)
async def upload_images(
    code: str | None = Query(default=None),
    environment: Literal["indoor", "outdoor"] | None = Query(default=None),
    files: list[UploadFile] = File(...),
    service: SubmissionJobService = deps(SubmissionJobService),
) -> HTMLResponse:
    """Handle multi-file image upload, return HTML response."""
    # Validate code
    try:
        _require_code(code)
    except HTTPException as e:
        return HTMLResponse(
            content=f"""<!DOCTYPE html>
<html><head><title>Error</title></head>
<body><h1>Unauthorized</h1><p>{e.detail}</p></body></html>""",
            status_code=e.status_code,
        )

    # Validate environment
    if environment is None:
        return HTMLResponse(
            content=_build_error_html(
                "Missing environment parameter. Use environment=indoor or environment=outdoor.",
                "outdoor",
                code or "",
            ),
            status_code=400,
        )

    # Validate files
    if not files or len(files) == 0:
        return HTMLResponse(
            content=_build_error_html(
                "No files selected. Please select at least one image.",
                environment,
                code or "",
            ),
            status_code=400,
        )

    queued_items: list[dict[str, str]] = []
    failed_items: list[dict[str, str]] = []
    for file in files:
        file_bytes = await file.read()
        try:
            await service.enqueue_submission(
                file_bytes=file_bytes,
                filename=file.filename,
                content_type=file.content_type,
                environment=environment,
                moderation_status="approved",
                submitted_by_user_id=None,
            )
            queued_items.append({"filename": file.filename or "Unknown"})
        except ImageUploadError as exc:
            failed_items.append(
                {"filename": file.filename or "Unknown", "error": exc.message}
            )
        except Exception:
            failed_items.append(
                {
                    "filename": file.filename or "Unknown",
                    "error": "An unexpected error occurred",
                }
            )

    return HTMLResponse(
        content=_build_result_html(
            environment,
            total=len(files),
            queued_count=len(queued_items),
            queued_items=queued_items,
            failed_items=failed_items,
            code=code or "",
        )
    )


@router.get("/upload/jobs/{job_id}", response_model=SubmissionJobStatusResponse)
async def get_upload_job_status(
    job_id: str,
    code: str | None = Query(default=None),
    service: SubmissionJobService = deps(SubmissionJobService),
) -> SubmissionJobStatusResponse:
    _require_code(code)
    status_payload = await service.get_job_status_by_code(job_id=job_id)
    if status_payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission job not found",
        )
    return status_payload
