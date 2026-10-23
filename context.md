# Project Context: Workout Helper & Video-to-App Pipeline

## 1. Executive Summary
Workout Helper is a full-stack, AI-powered fitness routine extractor inspired by the `recipe-builder` architecture in `personal-ai`. It processes workout videos from **YouTube Shorts** and **Instagram Reels**, uses Google Gemini AI to extract structured exercise sets, reps, muscle targets, and technique cues, extracts sharpest keyframes via OpenCV Laplacian variance scoring, and compiles a standalone mobile-first workout site hosted for **100% free on GitHub Pages**.

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
│  • OpenCV Keyframe Extraction (Laplacian variance sharpness filtering) │
│  • Google Gemini AI Client (gemini-flash-lite-latest / 3.5-flash)      │
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
