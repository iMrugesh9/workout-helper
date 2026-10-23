# Project Handoff: Workout Helper & GitHub Pages Automation

## 1. Goal & Scope
- **Objective**: Build a complete end-to-end workout extraction and publishing tool (matching the architecture of `recipe-builder` in `personal-ai`).
- **Inputs**: YouTube Shorts and Instagram Reels (workout videos).
- **Outputs**:
  - Standalone mobile-first HTML workout apps (exercise checklists, form cues, rest timers, OpenCV keyframes) modeled after `day25-workout-mobile.html`.
  - Static Workout Hub compiled to `docs/` and hosted 100% free on GitHub Pages.

---

## 2. Completed Implementation
1. **Core Engines**:
   - [`workout_agent.py`](file:///home/dex/projects/workout/workout_agent.py): Single-URL CLI extraction engine.
   - [`batch_agent.py`](file:///home/dex/projects/workout/batch_agent.py): Batch processing from files/URLs.
   - [`export_static.py`](file:///home/dex/projects/workout/export_static.py): Compiles `docs/index.html` & `docs/workouts/<id>.html`, and pushes to GitHub Pages.
   - [`server.py`](file:///home/dex/projects/workout/server.py): Flask dashboard on port `8081` with dynamic LAN IP detection.
   - [`manage_server.sh`](file:///home/dex/projects/workout/manage_server.sh): Server background manager.
2. **Templates & Design**:
   - [`template/workout.html.jinja`](file:///home/dex/projects/workout/template/workout.html.jinja): Jinja template capturing the exact mobile layout, sticky rest timer, and check-offs.
   - [`static/index.html`](file:///home/dex/projects/workout/static/index.html): Local web UI for URL extraction and workout management.
   - [`docs/index.html`](file:///home/dex/projects/workout/docs/index.html): Live Workout Hub with instant search and category filtering.
3. **Canonical Data**:
   - [`data/workouts.json`](file:///home/dex/projects/workout/data/workouts.json): Initialized with Day 25 Full Body Challenge (8 exercises with form cues, doses, and embedded videos).

---

## 3. GitHub Pages Setup Step
To host this on GitHub Pages:
1. Create a repository on GitHub (e.g. `workout-helper` under `iMrugesh9`).
2. Add the remote and push:
   ```bash
   git remote add origin git@github.com:iMrugesh9/workout-helper.git
   git push -u origin main
   ```
3. Enable GitHub Pages in repository Settings:
   - Branch: `main`
   - Folder: `/docs`
   - Save.

From then on, every extraction will automatically commit and publish to your GitHub Pages site!
