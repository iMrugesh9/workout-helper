# ⚡ Workout Helper Agent

Extract structured, interactive workout routines from **YouTube Shorts** and **Instagram Reels** — with exercise checklists, form cues, rest timers, and sharp keyframe guides — automatically extracted by AI and hosted for **100% free on GitHub Pages**.

---

## ✨ Features

- 🎬 Works with **YouTube Shorts** and **public Instagram Reels**
- 🔄 **Instagram Carousel & Multi-Index Auto-Looping** — automatically loops up to 15 indexes for multi-video posts/reels (`?img_index=`, `?index=`), stitches clips with FFmpeg, and analyzes the full routine as a unified whole
- 🤖 **Multimodal Gemini AI Video Scanning** — uploads and evaluates full video streams to identify all distinct exercises and precise start/end timestamps
- ✂️ **Automatic Video Snippet Trimming (FFmpeg)** — cuts compact, mobile-optimized looping H.264 MP4 clips for each exercise
- 📸 **OpenCV Keyframe Extraction** — selects the sharpest demonstration frames using Laplacian variance scoring for video poster frames and fallback guides
- 📱 **Mobile-First Workout App Design** (optimized for iPhone 14 & Safari)
  - Looping exercise video demonstration guides directly inside the checklist
  - Interactive exercise checklist with progress bar (persisted via `localStorage`)
  - Sticky bottom rest timer (presets: 30s, 45s, 60s, stopwatch + completion vibration)
  - Dark & Light mode athletic styling with Barlow Condensed typography
  - Safe-area inset support for modern mobile screens
- 🌐 **Free Forever GitHub Pages Hosting**
  - Standalone Static Hub in `docs/` (`docs/index.html` with real-time search & filters)
  - Individual standalone workout pages in `docs/workouts/<id>.html`
  - Automated dual-sync on save / delete / edit directly via Git SSH
- 🖥️ **Dual Interfaces**:
  - **CLI Tool** (`workout_agent.py` & `batch_agent.py`)
  - **Local Web App** (`server.py` on port 8081) with dynamic LAN IP detection for phone testing

---

## 🚀 Quick Start

### 1. Set Up Your Gemini API Key

Create `.env` in the project root:
```bash
cp .env.example .env
```

Add your Gemini API Key:
```env
GEMINI_API_KEY=your_key_here
```

### 2. Activate the Environment

```bash
source .venv/bin/activate
```

### 3. Extract a Workout (CLI)

```bash
# YouTube Shorts:
python workout_agent.py https://www.youtube.com/shorts/YOUR_VIDEO_ID

# Instagram Reel:
python workout_agent.py https://www.instagram.com/reel/YOUR_REEL_ID/
```

The standalone workout page will be compiled to `docs/workouts/<id>.html` and synced to `docs/`.

---

## 🌐 Run the Local Web App

```bash
python server.py
# Or use the helper:
./manage_server.sh
```

Console will display:
```
⚡ Workout Helper Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐  Local:   http://localhost:8081
📱  Mobile:  http://192.168.x.x:8081
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
Open `http://localhost:8081` on your computer or `http://<LAN_IP>:8081` on your phone (same Wi-Fi) to paste links and run workouts!

---

## 📦 Batch Extraction

Process multiple workout URLs from arguments or a CSV/text file:
```bash
python batch_agent.py https://instagram.com/reel/1 https://youtube.com/shorts/2
# Or from a file:
python batch_agent.py workout_links.csv
```

---

## 🚀 GitHub Pages Setup (Free Public Hosting)

1. **Create a new repository on GitHub** (e.g. `workout-helper`).
2. **Add the remote origin**:
   ```bash
   git remote add origin git@github.com:iMrugesh9/workout-helper.git
   git push -u origin main
   ```
3. **Enable GitHub Pages**:
   - Go to your repository on GitHub → **Settings** → **Pages**
   - Source: **Deploy from a branch**
   - Branch: **`main`**, Folder: **`/docs`**
   - Click **Save**
4. Your workout hub is live at:
   `https://<username>.github.io/<repo>/`

Every new workout you extract or edit will auto-compile to `docs/` and automatically push to GitHub Pages!

---

## 📁 Project Structure

```
workout/
├── workout_agent.py        # CLI extraction engine (URL -> Multimodal AI -> FFmpeg snippets + OpenCV frames -> HTML)
├── server.py               # Local Flask server & REST API (port 8081)
├── export_static.py        # Compiles docs/ static hub and auto-syncs to GitHub
├── batch_agent.py          # Batch processor for multiple URLs/files
├── manage_server.sh        # Background service manager (start/stop/logs)
├── requirements.txt        # Python dependencies
├── .env                    # Secret credentials (GEMINI_API_KEY)
├── .env.example
├── template/
│   └── workout.html.jinja  # Jinja template for phone-ready standalone workout apps
├── data/
│   └── workouts.json       # Canonical database of saved workouts
├── docs/                   # GitHub Pages root (branch: main, path: /docs)
│   ├── index.html          # Workout Hub dashboard with search & filters
│   ├── workouts.json       # JSON feed of all workouts
│   └── workouts/           # Standalone phone-ready workout HTML pages
│       └── day25-full-body.html
└── static/                 # Web app frontend assets
    └── index.html          # Local dashboard UI
```
