# Project Context: Workout Helper & Video-to-App Pipeline

## 1. Executive Summary
Workout Helper is a full-stack, AI-powered fitness routine extractor inspired by the `recipe-builder` architecture in `personal-ai`. It processes workout videos from **YouTube Shorts** and **Instagram Reels**, uses Google Gemini AI to extract structured exercise sets, reps, muscle targets, and technique cues, extracts sharpest keyframes via OpenCV Laplacian variance scoring, and compiles a standalone mobile-first workout site hosted for **100% free on GitHub Pages**.

---

## 2. Core Architecture & Hybrid Model

```
                    LOCAL WORKSPACE (Extraction & Heavy Work)
┌────────────────────────────────────────────────────────────────────────┐
│  • Flask Web Server (http://localhost:8081 & http://<LAN_IP>:8081)     │
│  • yt-dlp Video & Subtitle Extractor (Direct signed URL parsing)       │
│  • OpenCV Keyframe Extraction (Laplacian variance sharpness filtering) │
│  • Google Gemini AI Client (Multimodal video fallback)                 │
│  • Local Storage (data/workouts.json)                                  │
│  • Standalone HTML Generator (template/workout.html.jinja)             │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Auto-syncs on save/extract/delete
                                   ▼
                    GITHUB PAGES (Public Static Hosting)
┌────────────────────────────────────────────────────────────────────────┐
│  • Free forever global CDN (https://<username>.github.io/<repo>/)      │
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
├── workout_agent.py        # CLI interface for single URL extraction
├── batch_agent.py          # Batch extraction from files/lists of URLs
├── server.py               # Flask backend & REST API (port 8081)
├── manage_server.sh        # Background service manager (start/stop/logs)
├── export_static.py        # Compiles data/workouts.json into docs/ & auto-pushes
├── requirements.txt        # Python dependencies
├── .env                    # Secret credentials (GEMINI_API_KEY) — NEVER COMMITTED
├── .env.example            # Environment variable template
├── .gitignore              # Ignores .venv, *.mp4, .env, __pycache__, logs
├── template/
│   └── workout.html.jinja  # Jinja2 template capturing phone-ready app design
├── data/
│   └── workouts.json       # Canonical database of extracted workouts
├── docs/                   # GitHub Pages root folder (branch: main, path: /docs)
│   ├── index.html          # Workout Hub portal with search and category filters
│   ├── workouts.json       # Static JSON feed
│   └── workouts/           # Standalone phone-ready workout HTML pages
│       └── day25-full-body.html
└── static/
    └── index.html          # Local web app dashboard for pasting URLs & managing workouts
```

---

## 4. Engineering Decisions & Solutions

1. **Reusing the Battle-Tested Recipe Engine**:
   - Built on the core innovations from `personal-ai`: yt-dlp signed URL caption parsing, Gemini multimodal fallback for caption-less videos, and OpenCV Laplacian variance filtering for motion-blur free keyframes.
2. **Mobile-First iPhone 14 UI Preserved**:
   - Uses `Barlow` and `Barlow Condensed` typography.
   - Built-in sticky rest timer with presets (30s, 45s, 60s, stopwatch) and vibration on completion.
   - Viewport meta with `viewport-fit=cover` and safe area insets.
   - Persistent `localStorage` check-off progress so users can train without losing progress if Safari refreshes.
3. **Dual Execution Interfaces**:
   - **CLI**: `python workout_agent.py <url>`
   - **Local Web UI**: `python server.py` (running on port 8081 with dynamic LAN IP detection for phone testing).
4. **Initial Data Seeding**:
   - Converted the original `day25-workout-mobile.html` into the first canonical workout entry in `data/workouts.json`.
5. **Zero-Cost GitHub Pages Static Delivery**:
   - Standalone static pages in `docs/workouts/<id>.html` and hub in `docs/index.html`.
   - `auto_sync_github()` commits and pushes updates automatically via SSH whenever a workout is extracted, updated, or removed.
