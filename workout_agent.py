#!/usr/bin/env python3
"""
Workout Helper Agent (CLI)
==========================
Extracts structured workout routines from YouTube Shorts or Instagram Reels
and generates a mobile-first standalone HTML workout page, auto-syncing to docs/.

Usage:
    python workout_agent.py <video_url>
    python workout_agent.py https://www.youtube.com/shorts/abc123
    python workout_agent.py https://www.instagram.com/reel/abc123/
"""

import os
import sys
import re
import json
import base64
import shutil
import tempfile
import subprocess
import urllib.request
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types
import cv2

# ─────────────────────────────────────────────
# Environment & Paths
# ─────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
DATA_FILE = ROOT_DIR / "data" / "workouts.json"
DOCS_DIR = ROOT_DIR / "docs"
TEMPLATE_DIR = ROOT_DIR / "template"

load_dotenv(ROOT_DIR / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ No GEMINI_API_KEY found in .env file.")
    print("   Create a .env file with: GEMINI_API_KEY=your_key_here")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

WORKOUT_PROMPT = """
You are a certified master fitness trainer and workout analyst.
I will give you the transcript, title, description, or video visual stream of a workout video (Reel / Short).
Extract ALL workout information and return it as a valid JSON object with EXACTLY this structure:

{
  "workout_name": "Title of the workout (e.g. Day 25 Full Body Challenge)",
  "category": "Full Body | Upper Body | Lower Body | Core | HIIT | Mobility",
  "difficulty": "Beginner | Intermediate | Advanced",
  "estimated_duration": "Estimated time (e.g. 20–30 min, 15 min)",
  "blocks_count": "e.g. 4 Blocks, 3 Circuits, or 1 Flow",
  "description": "2-3 concise sentences summarizing this workout session and target goals.",
  "equipment": ["Yoga Mat", "Dumbbells", "Chair", "Bodyweight / None"],
  "exercises": [
    {
      "step_number": 1,
      "title": "Exercise Name (e.g. Push-ups)",
      "dose": "Dose or reps (e.g. 1 × 10 reps, 3 × 12 reps, or 40s work / 20s rest)",
      "target_muscles": ["Chest", "Triceps", "Shoulders"],
      "cues": [
        "Concise cue 1 on technique",
        "Concise cue 2 on form"
      ],
      "why": "Brief 1-sentence explanation of benefit or target",
      "timestamp_percent": 15
    }
  ],
  "tips": [
    "Actionable trainer tip 1",
    "Actionable trainer tip 2"
  ],
  "tags": ["Full Body", "Home Workout", "Bodyweight"]
}

Rules:
- Be thorough and precise. Extract every distinct exercise performed.
- If reps/duration are explicitly shown on screen or spoken, use them. If unspecified, provide an accurate trainer recommendation and note it.
- Provide accurate timestamp_percent (0 to 100) indicating where this exercise is demonstrated in the video clip.
- Return ONLY the raw JSON object. No markdown code blocks, no explanation.

Video Title: __TITLE__
Transcript/Notes:
__TRANSCRIPT__
"""


def detect_platform(url: str) -> str:
    url_l = url.lower()
    if "youtube.com/shorts" in url_l or "youtu.be" in url_l or "youtube.com/watch" in url_l:
        return "YouTube"
    elif "instagram.com" in url_l:
        return "Instagram"
    return "Video"


def parse_vtt_text(content: str) -> str:
    lines = content.split("\n")
    clean_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:") or line.startswith("NOTE"):
            continue
        if re.match(r"^\d{2}:\d{2}", line) or re.match(r"^\d+$", line) or "-->" in line:
            continue
        line = re.sub(r"<[^>]+>", "", line).strip()
        if line and (not clean_lines or clean_lines[-1] != line):
            clean_lines.append(line)
    return " ".join(clean_lines)


def extract_captions_from_info(info: dict) -> str:
    subs_sources = [info.get("subtitles") or {}, info.get("automatic_captions") or {}]
    preferred_langs = ["en-orig", "en", "hi-orig", "hi", "en-US", "en-GB"]

    for source in subs_sources:
        if not source:
            continue
        ordered_keys = [k for k in preferred_langs if k in source] + [k for k in source if k not in preferred_langs]
        for lang in ordered_keys:
            formats = source.get(lang) or []
            vtt_fmts = [f for f in formats if f.get("ext") == "vtt"]
            target = vtt_fmts[0] if vtt_fmts else (formats[0] if formats else None)
            if not target or not target.get("url"):
                continue
            try:
                req = urllib.request.Request(
                    target["url"],
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")
                    cleaned = parse_vtt_text(raw)
                    if len(cleaned.strip()) > 25:
                        return cleaned
            except Exception:
                pass
    return ""


def get_yt_dlp_bin() -> str:
    local_bin = ROOT_DIR / ".venv" / "bin" / "yt-dlp"
    if local_bin.exists():
        return str(local_bin)
    system_bin = shutil.which("yt-dlp")
    return system_bin if system_bin else "yt-dlp"


def fetch_video_info(url: str, tmpdir: str) -> dict:
    yt_dlp_bin = get_yt_dlp_bin()

    print("📥 Fetching video metadata with yt-dlp...")
    cmd_meta = [yt_dlp_bin, "--dump-json", "--no-warnings", url]
    res_meta = subprocess.run(cmd_meta, capture_output=True, text=True, timeout=30)
    info = {}
    if res_meta.returncode == 0 and res_meta.stdout.strip():
        try:
            info = json.loads(res_meta.stdout)
        except Exception:
            pass

    title = info.get("title", "Workout Routine")
    description = info.get("description", "")

    thumbnail_url = ""
    thumbs = info.get("thumbnails", [])
    if thumbs:
        best = max(thumbs, key=lambda t: (t.get("width") or 0) * (t.get("height") or 0), default={})
        thumbnail_url = best.get("url", "")
    if not thumbnail_url:
        thumbnail_url = info.get("thumbnail", "")

    transcript = extract_captions_from_info(info)
    if not transcript or len(transcript.strip()) < 30:
        if description:
            transcript = description
    elif description and len(description) > len(transcript):
        transcript = transcript + "\n\n" + description

    # Download MP4 video stream
    print("🎬 Downloading video stream for frame extraction...")
    cmd_vid = [
        yt_dlp_bin,
        "--no-playlist",
        "--no-warnings",
        "-f", "best[ext=mp4]/bestvideo[height<=1280][ext=mp4]/bestvideo[width<=1280][ext=mp4]/best[height<=720]/best",
        "-o", f"{tmpdir}/video.%(ext)s",
        url,
    ]
    subprocess.run(cmd_vid, capture_output=True, text=True, timeout=50)

    video_files = [
        str(p) for p in Path(tmpdir).glob("video.*")
        if p.suffix.lower() in [".mp4", ".mkv", ".webm", ".mov"]
    ]
    video_path = video_files[0] if video_files else None

    return {
        "title": title,
        "description": description,
        "transcript": transcript,
        "thumbnail_url": thumbnail_url,
        "video_path": video_path,
        "source_url": url,
        "platform": detect_platform(url),
    }


def extract_workout_with_gemini(video_info: dict) -> dict:
    import time
    transcript = (video_info.get("transcript") or "").strip()
    video_path = video_info.get("video_path")
    file_ref = None

    if len(transcript) >= 30:
        print(f"🤖 Sending transcript ({len(transcript)} chars) to Gemini...")
        prompt = (
            WORKOUT_PROMPT
            .replace("__TITLE__", str(video_info.get("title", "Workout")))
            .replace("__TRANSCRIPT__", transcript[:12000])
        )
        content_payload = prompt
    elif video_path and os.path.exists(video_path):
        print("🤖 Uploading video to Gemini for multimodal video analysis...")
        try:
            file_ref = client.files.upload(file=video_path)
            print(f"   Video uploaded: {file_ref.name}")
        except Exception as e:
            print(f"   Upload error: {e}")
            file_ref = None

        prompt = (
            WORKOUT_PROMPT
            .replace("__TITLE__", str(video_info.get("title", "Workout")))
            .replace("__TRANSCRIPT__", "Observe the video visuals, on-screen text, and exercise movements to extract the routine.")
        )
        content_payload = [file_ref, prompt] if file_ref else prompt
    else:
        prompt = (
            WORKOUT_PROMPT
            .replace("__TITLE__", str(video_info.get("title", "Workout")))
            .replace("__TRANSCRIPT__", f"Video Title: {video_info.get('title')}. Extract standard workout exercises.")
        )
        content_payload = prompt

    raw = None
    last_error = None
    for model in GEMINI_MODELS:
        try:
            print(f"   Querying Gemini ({model})...")
            resp = client.models.generate_content(
                model=model,
                contents=content_payload,
            )
            raw = resp.text.strip()
            print("   Gemini response received!")
            break
        except Exception as e:
            last_error = e
            time.sleep(1)

    if file_ref:
        try:
            client.files.delete(name=file_ref.name)
        except Exception:
            pass

    if not raw:
        raise RuntimeError(f"All Gemini models failed: {last_error}")

    cleaned = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    cleaned = re.sub(r"\n?```$", "", cleaned).strip()
    json_match = re.search(r'\{[\s\S]+\}', cleaned)
    if json_match:
        cleaned = json_match.group(0)

    return json.loads(cleaned)


def extract_visual_frames(video_path: str, workout_data: dict) -> dict:
    if not video_path or not os.path.exists(video_path):
        return workout_data

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return workout_data

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0 or fps <= 0:
            cap.release()
            return workout_data

        duration = total_frames / fps
        print(f"📸 Extracting sharpest keyframes via OpenCV (Duration: {duration:.1f}s)...")

        def get_sharpest_frame_b64(target_sec, max_w=640, quality=75):
            center_frame = int(target_sec * fps)
            best_frame = None
            best_score = -1

            # Sample 5 neighboring frames to eliminate motion blur
            for off in [-4, -2, 0, 2, 4]:
                idx = max(0, min(total_frames - 1, center_frame + off))
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                score = cv2.Laplacian(gray, cv2.CV_64F).var()
                if score > best_score:
                    best_score = score
                    best_frame = frame

            if best_frame is None:
                return None

            h, w = best_frame.shape[:2]
            if w > max_w:
                new_h = int(h * (max_w / w))
                best_frame = cv2.resize(best_frame, (max_w, new_h), interpolation=cv2.INTER_AREA)

            _, buf = cv2.imencode('.jpg', best_frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            b64 = base64.b64encode(buf).decode('utf-8')
            return f"data:image/jpeg;base64,{b64}"

        exercises = workout_data.get("exercises", [])
        num_ex = len(exercises)
        for i, ex in enumerate(exercises):
            pct = ex.get("timestamp_percent")
            if pct is not None and isinstance(pct, (int, float)) and 5 <= pct <= 95:
                sec = duration * (pct / 100.0)
            else:
                sec = duration * ((i + 1) / (num_ex + 1))

            b64_img = get_sharpest_frame_b64(sec)
            if b64_img:
                ex["image"] = b64_img

        cap.release()
    except Exception as e:
        print(f"⚠️ OpenCV frame extraction warning: {e}")

    return workout_data


def save_and_export(workout_data: dict, video_info: dict) -> Path:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    # Generate slug ID
    title_slug = re.sub(r"[^a-z0-9]+", "-", workout_data.get("workout_name", "workout").lower()).strip("-")
    short_hash = hex(abs(hash(video_info.get("source_url", ""))))[2:8]
    workout_id = f"{title_slug[:30]}-{short_hash}"

    workout_entry = {
        "id": workout_id,
        "title": workout_data.get("workout_name", "Untitled Workout"),
        "category": workout_data.get("category", "Full Body"),
        "difficulty": workout_data.get("difficulty", "Intermediate"),
        "estimated_duration": workout_data.get("estimated_duration", "20–30 min"),
        "blocks_count": workout_data.get("blocks_count", "1 Circuit"),
        "description": workout_data.get("description", ""),
        "equipment": workout_data.get("equipment", []),
        "exercises": workout_data.get("exercises", []),
        "tips": workout_data.get("tips", []),
        "source_url": video_info.get("source_url", ""),
        "platform": video_info.get("platform", "Video"),
        "thumbnail_url": video_info.get("thumbnail_url", ""),
        "generated_at": datetime.now().isoformat(),
    }

    # Deduplicate or prepend
    existing = [w for w in existing if w.get("id") != workout_id and w.get("source_url") != workout_entry["source_url"]]
    existing.insert(0, workout_entry)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to {DATA_FILE} (Total: {len(existing)} workouts)")

    # Trigger export_static.py
    from export_static import generate_static_site, auto_sync_github
    generate_static_site()
    sync_result = auto_sync_github()
    print(f"🚀 GitHub Pages sync status: {sync_result.get('message', 'done')}")

    out_file = DOCS_DIR / "workouts" / f"{workout_id}.html"
    return out_file


def process_url(url: str) -> Path:
    with tempfile.TemporaryDirectory() as tmpdir:
        info = fetch_video_info(url, tmpdir)
        workout_data = extract_workout_with_gemini(info)
        workout_data = extract_visual_frames(info.get("video_path"), workout_data)
        out_html = save_and_export(workout_data, info)
        return out_html


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python workout_agent.py <youtube_or_instagram_url>")
        sys.exit(1)

    target_url = sys.argv[1].strip()
    print(f"\n🏋️ Starting Workout Extraction for: {target_url}\n")
    try:
        out_page = process_url(target_url)
        print(f"\n🎉 SUCCESS! Generated standalone mobile workout:")
        print(f"👉 File: {out_page}\n")
    except Exception as e:
        print(f"\n❌ Error processing workout: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
