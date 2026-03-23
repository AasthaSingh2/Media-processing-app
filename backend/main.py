from __future__ import annotations

import mimetypes
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator


BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

FFMPEG_TIMEOUT_SECONDS = 120
DOWNLOAD_TIMEOUT_SECONDS = 30
CHUNK_SIZE = 1024 * 1024


class ProcessRequest(BaseModel):
    url: str
    operation: Literal["thumbnail", "compress", "extract_audio"]

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parsed = urlparse(value.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("URL must be a valid HTTP or HTTPS address.")
        return value.strip()


class ProcessResponse(BaseModel):
    status: Literal["success"]
    output: str
    operation: Literal["thumbnail", "compress", "extract_audio"]


app = FastAPI(title="Media Processing App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")


def build_ffmpeg_command(operation: str, input_path: Path, output_path: Path) -> list[str]:
    commands: dict[str, list[str]] = {
        "thumbnail": [
            "ffmpeg",
            "-i",
            str(input_path),
            "-ss",
            "00:00:02",
            "-vframes",
            "1",
            str(output_path),
            "-y",
        ],
        "compress": [
            "ffmpeg",
            "-i",
            str(input_path),
            "-vcodec",
            "libx264",
            "-crf",
            "30",
            "-preset",
            "veryfast",
            "-acodec",
            "aac",
            str(output_path),
            "-y",
        ],
        "extract_audio": [
            "ffmpeg",
            "-i",
            str(input_path),
            "-vn",
            "-acodec",
            "libmp3lame",
            str(output_path),
            "-y",
        ],
    }
    return commands[operation]


def infer_input_suffix(content_type: str | None, source_url: str) -> str:
    guessed_from_header = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    guessed_from_path = Path(urlparse(source_url).path).suffix
    if guessed_from_header:
        return guessed_from_header
    if guessed_from_path:
        return guessed_from_path
    return ".mp4"


def download_media(source_url: str, destination: Path) -> None:
    try:
        with requests.get(source_url, stream=True, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if content_type and not content_type.startswith(("video/", "audio/", "application/octet-stream")):
                raise HTTPException(status_code=400, detail="The URL does not point to a supported media file.")

            with destination.open("wb") as temp_file:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        temp_file.write(chunk)
    except requests.exceptions.MissingSchema as exc:
        raise HTTPException(status_code=400, detail="Invalid URL provided.") from exc
    except requests.exceptions.InvalidURL as exc:
        raise HTTPException(status_code=400, detail="Invalid URL provided.") from exc
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=400, detail="Failed to download media from the provided URL.") from exc


def run_ffmpeg(command: list[str]) -> None:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="FFmpeg is not installed or not available in PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="FFmpeg processing timed out.") from exc

    if completed.returncode != 0:
        error_message = completed.stderr.strip() or "Unknown FFmpeg error."
        raise HTTPException(status_code=500, detail=f"FFmpeg processing failed: {error_message}")


@app.get("/")
def health_check() -> dict[str, str]:
    return {"message": "Media Processing App backend is running."}


@app.post("/process", response_model=ProcessResponse)
def process_media(payload: ProcessRequest, request: Request) -> ProcessResponse:
    file_id = uuid.uuid4().hex
    input_suffix = infer_input_suffix(None, payload.url)
    temp_input_path = TEMP_DIR / f"{file_id}{input_suffix}"

    output_suffix = ".jpg" if payload.operation == "thumbnail" else ".mp4" if payload.operation == "compress" else ".mp3"
    output_path = OUTPUT_DIR / f"{file_id}{output_suffix}"

    try:
        download_media(payload.url, temp_input_path)
        ffmpeg_command = build_ffmpeg_command(payload.operation, temp_input_path, output_path)
        run_ffmpeg(ffmpeg_command)

        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Output file was not created.")

        output_url = str(request.base_url).rstrip("/") + f"/outputs/{output_path.name}"
        return ProcessResponse(status="success", output=output_url, operation=payload.operation)
    finally:
        if temp_input_path.exists():
            temp_input_path.unlink(missing_ok=True)


@app.on_event("shutdown")
def cleanup_temp_directory() -> None:
    # Remove any leftover temp files from interrupted requests.
    for temp_file in TEMP_DIR.iterdir():
        if temp_file.is_file():
            temp_file.unlink(missing_ok=True)
        elif temp_file.is_dir():
            shutil.rmtree(temp_file, ignore_errors=True)
