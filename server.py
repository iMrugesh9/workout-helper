#!/usr/bin/env python3
"""
Workout Helper Web Server & Local API
=====================================
Hosts the local workout extraction dashboard, manages saved workouts,
and auto-syncs static HTML pages to docs/ for GitHub Pages.
"""

import os
import sys
import re
import json
import base64
import shutil
import socket
import tempfile
import threading
import subprocess
import traceback
from pathlib import Path
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

# Import core extraction logic from workout_agent
from workout_agent import (
    fetch_video_info,
    extract_workout_with_gemini,
    extract_visual_frames,
    ROOT_DIR,
    DATA_FILE,
    DOCS_DIR,
)
from export_static import generate_static_site, auto_sync_github

load_dotenv(ROOT_DIR / ".env")

app = Flask(__name__, static_folder="static")

VIDEOS_DIR = ROOT_DIR / "static" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


def load_workouts() -> list:
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[storage] Error loading workouts: {e}")
        return []


def save_workouts(workouts: list):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(workouts, f, ensure_ascii=False, indent=2)


def trigger_github_sync_async():
    """Run export_static and git push in background thread."""
    def _worker():
        try:
            generate_static_site()
            res = auto_sync_github()
            print(f"[auto-sync] {res.get('message', 'Completed')}")
        except Exception as e:
            print(f"[auto-sync error]: {e}")
    threading.Thread(target=_worker, daemon=True).start()


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/workouts/<workout_id>")
def view_workout_page(workout_id):
    """Serve standalone mobile workout page from docs/workouts/."""
    filename = f"{workout_id}.html" if not workout_id.endswith(".html") else workout_id
    page_path = DOCS_DIR / "workouts" / filename
    if page_path.exists():
        return send_from_directory(str(DOCS_DIR / "workouts"), filename)
    return "Workout not found", 404


@app.route("/api/workouts", methods=["GET"])
def get_workouts():
    return jsonify(load_workouts())


@app.route("/api/workouts/<workout_id>", methods=["GET"])
def get_workout(workout_id):
    workouts = load_workouts()
    for w in workouts:
        if w.get("id") == workout_id:
            return jsonify(w)
    return jsonify({"error": "Workout not found"}), 404


@app.route("/api/workouts/<workout_id>", methods=["PATCH"])
def update_workout(workout_id):
    data = request.get_json() or {}
    workouts = load_workouts()
    updated = False
    for w in workouts:
        if w.get("id") == workout_id:
            for k, v in data.items():
                if k not in ["id", "generated_at"]:
                    w[k] = v
            updated = True
            break
    if updated:
        save_workouts(workouts)
        trigger_github_sync_async()
        return jsonify({"success": True})
    return jsonify({"error": "Workout not found"}), 404


@app.route("/api/workouts/<workout_id>", methods=["DELETE"])
def delete_workout(workout_id):
    workouts = load_workouts()
    new_list = [w for w in workouts if w.get("id") != workout_id]
    if len(new_list) < len(workouts):
        save_workouts(new_list)
        trigger_github_sync_async()
        return jsonify({"success": True})
    return jsonify({"error": "Workout not found"}), 404


@app.route("/api/extract", methods=["POST"])
def extract_workout():
    data = request.get_json() or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    url_l = url.lower()
    is_yt = "youtube.com" in url_l or "youtu.be" in url_l
    is_ig = "instagram.com" in url_l
    if not is_yt and not is_ig:
        return jsonify({"error": "Please provide a valid YouTube Shorts/Video or Instagram Reel URL"}), 400

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            info = fetch_video_info(url, tmpdir)
            if not info.get("transcript") and not info.get("video_path"):
                return jsonify({"error": "Could not access video or audio content. Make sure video is public."}), 422

            workout_data = extract_workout_with_gemini(info)
            if info.get("video_path"):
                workout_data = extract_visual_frames(info["video_path"], workout_data)

            # Generate unique ID
            title_slug = re.sub(r"[^a-z0-9]+", "-", workout_data.get("workout_name", "workout").lower()).strip("-")
            short_hash = hex(abs(hash(url)))[2:8]
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
                "source_url": url,
                "platform": info.get("platform", "Video"),
                "thumbnail_url": info.get("thumbnail_url", ""),
                "generated_at": datetime.now().isoformat(),
            }

            workouts = load_workouts()
            workouts = [w for w in workouts if w.get("id") != workout_id and w.get("source_url") != url]
            workouts.insert(0, workout_entry)
            save_workouts(workouts)

            # Sync and generate static pages
            generate_static_site()
            trigger_github_sync_async()

            return jsonify(workout_entry)

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Video download timed out. Please try again."}), 504
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500


@app.route("/api/sync", methods=["POST"])
def sync_github():
    try:
        generate_static_site()
        res = auto_sync_github()
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    local_ip = get_local_ip()
    print("\n⚡ Workout Helper Agent")
    print("━" * 45)
    print(f"🌐  Local:   http://localhost:{port}")
    print(f"📱  Mobile:  http://{local_ip}:{port}")
    print("━" * 45)
    try:
        generate_static_site()
        print("📄  Static GitHub Pages site compiled in docs/")
    except Exception as e:
        print(f"⚠️  Static site generation warning: {e}")
    print("━" * 45 + "\n")
    app.run(debug=False, host="0.0.0.0", port=port)
