"""
FastAPI backend for the YouTube Comment Sentiment & Toxicity Analyzer.

Endpoints:
  GET  /          → serves static/index.html
  POST /analyze   → fetches YouTube comments + runs VADER analysis
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel

from src.analyzer import analyze_comments

load_dotenv()

app = FastAPI(title="YT Comment Analyzer API")

# ── Static files ────────────────────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse(STATIC_DIR / "index.html")


# ── Request / Response models ───────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    url: str
    max_comments: int = 200  # up to 200 (2 API pages of 100 each)


# ── Helpers ─────────────────────────────────────────────────────────────────
_VIDEO_ID_RE = re.compile(
    r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})"
)


def extract_video_id(url: str) -> str | None:
    match = _VIDEO_ID_RE.search(url)
    return match.group(1) if match else None


def fetch_video_meta(youtube, video_id: str) -> dict:
    """Return title and thumbnail URL for a video."""
    resp = (
        youtube.videos()
        .list(part="snippet", id=video_id)
        .execute()
    )
    if not resp.get("items"):
        return {"title": "Unknown video", "thumbnail": ""}
    snippet = resp["items"][0]["snippet"]
    thumbnails = snippet.get("thumbnails", {})
    thumb = (
        thumbnails.get("maxres")
        or thumbnails.get("high")
        or thumbnails.get("medium")
        or {}
    )
    return {
        "title": snippet.get("title", ""),
        "thumbnail": thumb.get("url", ""),
        "channel": snippet.get("channelTitle", ""),
    }


def fetch_comments(youtube, video_id: str, max_results: int = 200) -> list[str]:
    """
    Fetch top-level comments from a video using the YouTube Data API v3.
    Returns up to `max_results` comment strings.
    Raises HTTPException on API errors (e.g. comments disabled).
    """
    comments: list[str] = []
    page_token: str | None = None
    per_page = min(100, max_results)

    while len(comments) < max_results:
        try:
            resp = (
                youtube.commentThreads()
                .list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=per_page,
                    pageToken=page_token,
                    textFormat="plainText",
                    order="relevance",
                )
                .execute()
            )
        except HttpError as e:
            if e.resp.status == 403:
                raise HTTPException(
                    status_code=403,
                    detail="Comments are disabled for this video.",
                )
            raise HTTPException(status_code=500, detail=f"YouTube API error: {e}")

        for item in resp.get("items", []):
            text = (
                item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            )
            comments.append(text)

        page_token = resp.get("nextPageToken")
        if not page_token or len(comments) >= max_results:
            break

    return comments[:max_results]


# ── Main endpoint ────────────────────────────────────────────────────────────
@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key or api_key == "your_api_key_here_if_needed":
        raise HTTPException(
            status_code=500,
            detail="YOUTUBE_API_KEY is not set in your .env file.",
        )

    video_id = extract_video_id(req.url)
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Could not extract a video ID from the provided URL.",
        )

    youtube = build("youtube", "v3", developerKey=api_key)

    # Fetch video metadata and comments in parallel-ish (sequential is fine here)
    meta = fetch_video_meta(youtube, video_id)
    raw_comments = fetch_comments(youtube, video_id, req.max_comments)

    if not raw_comments:
        raise HTTPException(
            status_code=404,
            detail="No comments found for this video.",
        )

    results = analyze_comments(raw_comments)

    # Aggregate metrics
    total = len(results)
    positive = sum(1 for r in results if r["sentiment"] == "Positive")
    negative = sum(1 for r in results if r["sentiment"] == "Negative")
    neutral = sum(1 for r in results if r["sentiment"] == "Neutral")
    toxic = sum(1 for r in results if r["toxic"])
    avg_compound = round(sum(r["compound"] for r in results) / total, 4)

    return JSONResponse(
        {
            "video": meta,
            "video_id": video_id,
            "metrics": {
                "total": total,
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "toxic": toxic,
                "avg_compound": avg_compound,
            },
            "comments": results,
        }
    )
