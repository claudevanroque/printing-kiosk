import html

from fastapi import (
    APIRouter,
    File,
    UploadFile,
)

from fastapi.responses import HTMLResponse

from app.core.config import settings

from app.schemas.upload_session import (
    UploadSessionResponse,
)

from app.services.upload_session_service import (
    create_upload_session,
    get_session_by_token,
    get_upload_session,
    upload_to_session,
)


router = APIRouter(
    tags=["Upload Sessions"],
)


@router.post("/api/upload-sessions",response_model=UploadSessionResponse,)
def create_session():
    return create_upload_session()


@router.get("/api/upload-sessions/{session_id}",response_model=UploadSessionResponse,)
def session_status(session_id: str,):
    return get_upload_session(session_id)

@router.post("/api/upload-sessions/public/{token}/upload", response_model=UploadSessionResponse)
async def upload_document(token: str, file: UploadFile = File(...),):
    return await upload_to_session(token, file)

@router.get("/upload/{token}", response_class=HTMLResponse)
def mobile_upload_page(token: str,):
    get_session_by_token(token)
    safe_token = html.escape(token,quote=True,)
    max_size = (settings.max_file_size_mb)

    return HTMLResponse(
        content=f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>Kiosk Upload</title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            padding: 20px;

            min-height: 100vh;

            display: flex;
            align-items: center;
            justify-content: center;

            background: #f4f4f4;

            font-family:
                Arial,
                sans-serif;
        }}

        .card {{
            width: 100%;
            max-width: 420px;

            background: white;

            padding: 28px;

            border-radius: 18px;

            box-shadow:
                0 8px 30px
                rgba(0, 0, 0, 0.10);
        }}

        h1 {{
            margin-top: 0;
        }}

        input {{
            width: 100%;
            margin: 20px 0 10px;

            font-size: 16px;

            color: transparent;
        }}

        #fileName {{
            margin-bottom: 20px;

            font-size: 15px;
            color: #444;

            word-break: break-all;
        }}

        input::file-selector-button {{
            padding: 18px 26px;
            margin-right: 14px;

            border: 1.5px solid #d9d9d9;
            border-radius: 14px;

            font-size: 17px;
            font-weight: 600;
            letter-spacing: 0.3px;

            cursor: pointer;

            background: #fafafa;
            color: #111;

            box-shadow:
                0 2px 8px
                rgba(0, 0, 0, 0.06);

            transition:
                background 0.2s,
                border-color 0.2s;
        }}

        input::file-selector-button:hover {{
            background: #f0f0f0;
            border-color: #111;
        }}

        button {{
            width: 100%;

            padding: 15px;

            border: none;
            border-radius: 10px;

            font-size: 17px;

            cursor: pointer;

            background: #111;
            color: white;
        }}

        button:disabled {{
            opacity: 0.5;
        }}

        #status {{
            margin-top: 20px;
            line-height: 1.5;
        }}
    </style>
</head>

<body>

<div class="card">

    <h1>Upload Document</h1>

    <p>
        Select the document you want
        to print.
    </p>

    <p>
        PDF, JPG or PNG.
        Maximum {max_size} MB.
    </p>

    <input
        id="file"
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        onchange="showFileName()"
    >

    <div id="fileName"></div>

    <button
        id="uploadButton"
        onclick="uploadFile()"
    >
        Upload Document
    </button>

    <div id="status"></div>

</div>

<script>

function showFileName() {{

    const input =
        document.getElementById("file");

    document.getElementById(
        "fileName"
    ).textContent =
        input.files.length
            ? input.files[0].name
            : "";
}}


async function uploadFile() {{

    const input =
        document.getElementById("file");

    const button =
        document.getElementById(
            "uploadButton"
        );

    const status =
        document.getElementById(
            "status"
        );

    if (!input.files.length) {{
        status.textContent =
            "Please select a document.";

        return;
    }}

    button.disabled = true;

    status.textContent =
        "Uploading document...";

    const formData =
        new FormData();

    formData.append(
        "file",
        input.files[0]
    );

    try {{

        const response =
            await fetch(
                "/api/upload-sessions/public/{safe_token}/upload",
                {{
                    method: "POST",
                    body: formData
                }}
            );

        const data =
            await response.json();

        if (!response.ok) {{
            throw new Error(
                data.detail ||
                "Upload failed."
            );
        }}

        status.innerHTML =
            "<strong>Upload complete.</strong>" +
            "<br>You may return to the kiosk.";

        input.disabled = true;

    }} catch (error) {{

        status.textContent =
            error.message;

        button.disabled = false;
    }}
}}

</script>

</body>
</html>
"""
    )