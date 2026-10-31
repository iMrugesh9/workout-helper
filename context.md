# Project Context: Workout Helper & Video-to-App Pipeline

## 1. Executive Summary
Workout Helper is a full-stack, AI-powered fitness routine extractor inspired by the `recipe-builder` architecture in `personal-ai`. It processes workout videos from **YouTube Shorts** and **Instagram Reels**, uses Google Gemini AI (multimodal video understanding) to extract structured exercise sets, reps, muscle targets, and technique cues, generates short looping video snippets for every distinct exercise via FFmpeg, extracts sharpest keyframes via OpenCV Laplacian variance scoring for video poster frames, and compiles a standalone mobile-first workout site hosted for **100% free on GitHub Pages**.

- **Repository**: [https://github.com/iMrugesh9/workout-helper](https://github.com/iMrugesh9/workout-helper)
- **Live GitHub Pages Hub**: [https://imrugesh9.github.io/workout-helper/](https://imrugesh9.github.io/workout-helper/)
- **Live Port (Local)**: `http://localhost:8081` & `http://<LAN_IP>:8081`

---

## 2. Core Architecture & Hybrid Model

```
                    LOCAL WORKSPACE (Extraction & Heavy Work)
┌────────────────────────────────────────────────────────────────────────┐
│  • Flask Web Server (http://localhost:8081 & http://<LAN_IP>:8081)     │
│  • Desktop Launcher & Zenity Control Menu (~/Desktop/workout-server)  │
│  • yt-dlp Video & Subtitle Extractor (Direct signed URL parsing)       │
│  • Multi-Index Carousel Handler (auto-loops up to 15 index videos)    │
│  • FFmpeg Video Stitcher & Concat Demuxer (unified compilation timeline)│
│  • Multimodal Gemini Video Scanner (gemini-3.5-flash / 3.7 / 3.8)      │
│  • FFmpeg Exercise Snipper (Looping H.264 MP4 clips per exercise)     │
│  • OpenCV Keyframe Extraction (Laplacian variance sharpness filtering) │
│  • Local Storage (data/workouts.json)                                  │
│  • Standalone HTML Generator (template/workout.html.jinja)             │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Auto-syncs on save/extract/delete
                                   ▼
                    GITHUB PAGES (Public Static Hosting)
┌────────────────────────────────────────────────────────────────────────┐
│  • Free forever global CDN (https://imrugesh9.github.io/workout-helper/)│
│  • Standalone Static Site in docs/ (docs/index.html & docs/workouts/) │
│  • Fully Mobile-Responsive (iPhone 14 viewport & safe-area insets)     │
│  • Real-time search & Category filters (Full Body, Upper, Lower, HIIT) │
│  • Standalone workout pages (docs/workouts/<id>.html) with:            │
│    - Looping embedded video snippets for each exercise                 │
│    - Dynamic exercise checklist with progress bar (localStorage)       │
│    - Built-in sticky rest timer (30s, 45s, 60s, stopwatch + vibration)│
│    - Visual exercise guides (sharpest keyframes) & form cues           │
│    - Dark / Light mode athletic styling (Barlow Condensed typography)  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Files & Structure

```
workout/
├── workout_agent.py        # CLI interface for single URL extraction (auto-venv)
├── batch_agent.py          # Batch extraction from files/lists of URLs (auto-venv)
├── server.py               # Flask backend & REST API on port 8081 (auto-venv)
├── manage_server.sh        # Background daemon manager (start/stop/restart/zenity/logs)
├── export_static.py        # Compiles data/workouts.json into docs/ & auto-pushes via Git SSH
├── requirements.txt        # Python dependencies
├── .env                    # Secret credentials (GEMINI_API_KEY) — NEVER COMMITTED
├── .env.example            # Environment variable template
├── .gitignore              # Ignores .venv, *.mp4, .env, __pycache__, logs
├── template/
│   └── workout.html.jinja  # Jinja2 template capturing phone-ready app design
├── data/
│   └── workouts.json       # Canonical database of extracted workouts
├── docs/                   # GitHub Pages root folder (branch: main, path: /docs)
│   ├── index.html          # Workout Hub portal with live search and category filters
│   ├── workouts.json       # Static JSON feed
│   └── workouts/           # Standalone phone-ready workout HTML pages
│       ├── day25-full-body.html
│       └── fix-bad-posture-tone-arms-work-2c4dbe.html
├── static/
│   ├── index.html          # Local web app dashboard for pasting URLs & managing workouts
│   ├── workout-icon.svg    # Custom athletic terracotta & gold lightning vector icon
│   └── videos/             # Downloaded stream storage for local player
└── ~/Desktop/
    └── workout-server.desktop # Double-clickable desktop shortcut with Zenity GUI controls
```

---

## 4. Key Engineering Discoveries & Solutions

1. **Reusing and Extending the Recipe Builder Engine**:
   - Borrowed proven subsystems from `personal-ai`: signed-URL subtitle extraction (bypassing YouTube 429 errors), multimodal video fallback, and OpenCV Laplacian sharpness filtering.
2. **Mobile-First iPhone 14 UX Preserved**:
   - Replicated the layout from `day25-workout-mobile.html`: `Barlow` & `Barlow Condensed` fonts, warm terracotta palette (`#E05338`), `viewport-fit=cover`, safe-area bottom padding.
   - Built-in sticky rest timer bar (presets 30s, 45s, 60s, Stopwatch, audio alert & `navigator.vibrate([200, 100, 200])`).
   - `localStorage` persistence per workout ID so user progress is never lost on refresh.
3. **Gemini 2026 Model Deprecation & Compatibility**:
   - **Problem**: Earlier models (`gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-2.5-flash`) threw `404 NOT_FOUND` as they were retired in the v1beta API.
   - **Solution**: Configured `GEMINI_MODELS` to use active generation models:
     `["gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]`.
4. **Seamless Auto-Venv Execution**:
   - Scripts (`workout_agent.py`, `server.py`, `export_static.py`, `batch_agent.py`) check `sys.prefix == getattr(sys, "base_prefix", sys.prefix)` and auto-re-exec into the project's `.venv/bin/python` if launched from global Python.
5. **Background Process Management via `setsid`**:
   - In `manage_server.sh`, switched from `nohup` to `setsid` to ensure the server process detaches completely from subshell sessions.
6. **Desktop Shortcut & System Notifications**:
   - Created `~/Desktop/workout-server.desktop` and registered in `~/.local/share/applications/`.
   - Single/double clicking opens a Zenity menu dialog (Stop, Start, Open Local Web App, Open Live GitHub Pages, Restart, View Logs) and triggers desktop notifications via `notify-send`.
7. **Free GitHub Pages Isolation & Verification**:
   - Confirmed multiple GitHub Pages sites can coexist on a single account without conflict:
     - `recipe-helper`: `https://imrugesh9.github.io/recipe-helper/`
     - `workout-helper`: `https://imrugesh9.github.io/workout-helper/`
   - Verified that `.env` is completely excluded from git and repository is public.
   - First live tested extraction: `https://www.instagram.com/p/DbGuEMmoLko/` was automatically analyzed, keyframed, compiled, committed, and pushed to GitHub Pages.
8. **Multimodal Visual Scanning over Caption Heuristics**:
   - **Problem**: If a video description was $\ge 30$ characters, earlier code treated it as a transcript and bypassed sending the video file to Gemini. Instagram Reels often have long boilerplate captions (call-to-actions, hashtags) without mentioning any exercise names, causing Gemini to hallucinate a single generic exercise.
   - **Solution**: Video visuals are always uploaded and passed to Gemini whenever `video_path` exists. The video is uploaded via the Gemini Files API, polled until `ACTIVE`, and evaluated multimodally so every distinct exercise and its exact timestamps (`start_sec`, `end_sec`) are extracted.
9. **Automated Short Video Snippet Trimming via FFmpeg**:
   - Integrated `imageio-ffmpeg` static binary for consistent, system-independent video processing.
   - Slices each exercise into a lightweight 4–10 second looping MP4 clip (`scale=min(360,iw):-2`, H.264, AAC 48k mono audio with auto-fallback to `-an`).
   - Pairs each video snippet with an OpenCV Laplacian variance sharpness keyframe serving as the video `poster` frame.
   - Rendered with `controls playsinline loop preload="metadata"` in `template/workout.html.jinja`.
10. **Hub Feed Performance vs Self-Contained Standalone Pages**:
   - In `export_static.py`, heavy base64 video streams and raw images are omitted from `docs/workouts.json` and inlined `const WORKOUTS` in `docs/index.html`.
   - The Workout Hub index loads instantaneously (< 20 KB), while each standalone workout page (`docs/workouts/<id>.html`) remains 100% portable and self-contained with embedded video snippets.
11. **Instagram Multi-Index / Carousel Auto-Looping & Bifurcation (Max 15 Indexes)**:
   - **Problem**: Multi-video Instagram posts/reels containing query parameters like `index={num}` or `img_index={num}` (e.g. `?img_index=1`) represent multi-slide carousels where each slide typically features a distinct exercise. Earlier logic used `--no-playlist` and `-o video.mp4`, and `json.loads` failed on multi-line metadata dumps. As a result, only the very first slide was downloaded, truncating complete multi-exercise routines (such as 5-part dumbbell curls) into a single exercise.
   - **Two-Phase Index Fetching Strategy**:
     - *Detection*: Matches any Instagram URL containing `[?&](?:[a-zA-Z0-9_]*index)=\d+` or where `yt-dlp` dumps $> 1$ JSON metadata entries.
     - *Phase 1 (Batch Playlist Extraction)*: Requests `--playlist-items 1-15` via `yt-dlp` to pull all available carousel items in parallel (~10s).
     - *Phase 2 (Sequential Index Looping Fallback)*: If batch extraction yields $\le 1$ clip but an index parameter is present, loops sequentially from `idx = 1` to `15`, rewriting the URL parameter (`img_index={idx}` / `index={idx}`) and downloading each slide individually. Stops immediately when a 404/empty response or duplicate MD5 file hash is encountered.
   - **Video Stitching & Unified Compilation Timeline**:
     - Measures exact frame counts and FPS for every downloaded clip via OpenCV (`cv2.VideoCapture`).
     - Concatenates the clips into a single continuous video (`merged_video.mp4`) using the high-performance FFmpeg concat demuxer (`-f concat -safe 0 -c copy`). If streams differ in codec or dimensions, automatically falls back to `-filter_complex` scale-and-pad re-encoding at 720x1280 30fps.
     - Builds an internal segment map (`clip_segments`) tracking exact start and end seconds for each clip within the unified timeline:
       e.g., Clip 1 (0.0s–14.6s), Clip 2 (14.6s–30.1s), Clip 3 (30.1s–45.4s), etc.
   - **Multimodal Prompt Guidance & Bifurcation**:
     - Uploads the merged video to the Gemini Files API and passes the compilation breakdown directly in the prompt.
     - Instructs Gemini to evaluate the video as a unified whole and bifurcate exercises cleanly using the clip boundaries as reference points, while explicitly cautioning *not* to assume every clip is always strictly one exercise (allowing multiple exercises or variations within a single clip, or multi-clip progressions).
     - Requires start/end timestamps to be absolute seconds across the full compilation video timeline (0.0s to total duration).
   - **Automated Timestamp Validation & Offset Adjustment**:
     - If the model returns local relative timestamps (e.g., starting at 0s for each exercise), the engine detects this condition (`all_near_zero`) and automatically rebases each exercise's timestamps by adding `segment['start_sec']`.
     - Validates and clamps all timestamps to video boundaries, falling back to segment boundaries if any timestamps are missing.
   - **FFmpeg Exercise Snipping & OpenCV Keyframes**:
     - Slices individual looping video snippets (max 12s, centered on exercise midpoint) directly from the merged video for each exercise.
     - Computes the sharpest keyframe using Laplacian variance scoring around each exercise's midpoint for poster frames.
   - **Stale HTML Purge on Re-Extraction**:
     - When re-extracting an existing workout URL, any previous HTML file with a different slug ID is automatically unlinked from `docs/workouts/` to eliminate orphaned files on GitHub Pages.
