#!/usr/bin/env python3
"""
Batch Workout Analyzer
======================
Analyzes multiple Instagram Reels / YouTube Shorts in batch.

Usage:
    python batch_agent.py urls.csv
    python batch_agent.py https://instagram.com/reel/1 https://youtube.com/shorts/2
"""

import sys
import os
import csv
import glob
import json
import time
import tempfile
import traceback
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from workout_agent import (
    fetch_video_info,
    extract_workout_with_gemini,
    extract_visual_frames,
    save_and_export,
    DATA_FILE,
)
from export_static import generate_static_site, auto_sync_github


def parse_urls_from_sources(sources: list[str]) -> list[str]:
    """Extract and deduplicate Instagram/YouTube URLs from files or arguments."""
    raw_urls = []
    expanded = []
    for s in sources:
        matching = glob.glob(os.path.expanduser(s))
        if matching:
            expanded.extend(matching)
        else:
            expanded.append(s)

    for item in expanded:
        p = Path(item)
        if p.exists() and p.is_file():
            print(f"📄 Reading URLs from: {p.name}")
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                for row in reader:
                    for cell in row:
                        c = cell.strip().strip('"').strip("'")
                        if "instagram.com" in c or "youtube.com" in c or "youtu.be" in c:
                            raw_urls.append(c)
        else:
            if "instagram.com" in item or "youtube.com" in item or "youtu.be" in item:
                raw_urls.append(item)

    seen = set()
    cleaned = []
    for u in raw_urls:
        clean = u.split("?")[0].strip()
        if clean and clean not in seen:
            seen.add(clean)
            cleaned.append(u.strip())
    return cleaned


def run_batch(sources: list[str]):
    urls = parse_urls_from_sources(sources)
    if not urls:
        print("❌ No valid YouTube or Instagram URLs found.")
        sys.exit(1)

    print(f"\n🚀 Found {len(urls)} unique workout URLs to process:")
    for i, u in enumerate(urls, 1):
        print(f"   {i}. {u}")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{len(urls)}] Processing: {url}")
        t0 = time.time()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                info = fetch_video_info(url, tmpdir)
                workout_data = extract_workout_with_gemini(info)
                workout_data = extract_visual_frames(info.get("video_path"), workout_data)
                out_path = save_and_export(workout_data, info)
                elapsed = time.time() - t0
                print(f"   ✅ Done in {elapsed:.1f}s -> {out_path.name}")
                success_count += 1
        except Exception as e:
            elapsed = time.time() - t0
            print(f"   ❌ Failed in {elapsed:.1f}s: {e}")
            fail_count += 1

    print("\n" + "=" * 60)
    print(f"🏁 Batch complete: {success_count} succeeded, {fail_count} failed out of {len(urls)}.")

    generate_static_site()
    sync_res = auto_sync_github()
    print(f"🚀 Final GitHub Pages sync: {sync_res.get('message', 'done')}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_agent.py <url_or_file1> [url_or_file2 ...]")
        sys.exit(1)
    run_batch(sys.argv[1:])
