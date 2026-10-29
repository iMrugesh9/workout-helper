#!/usr/bin/env python3
"""
Static Workout Hub Generator & GitHub Auto-Sync
===============================================
Compiles saved workouts from data/workouts.json into a standalone static site
in the docs/ folder for 100% free hosting on GitHub Pages.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent
DATA_FILE = ROOT_DIR / "data" / "workouts.json"
DOCS_DIR = ROOT_DIR / "docs"
TEMPLATE_DIR = ROOT_DIR / "template"

# Auto-switch to .venv python if not already active
ROOT_DIR = Path(__file__).resolve().parent
if sys.prefix == getattr(sys, "base_prefix", sys.prefix):
    venv_py = ROOT_DIR / ".venv" / "bin" / "python"
    if venv_py.exists():
        os.execv(str(venv_py), [str(venv_py)] + sys.argv)


def load_workouts() -> list:
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[export] Error loading workouts: {e}")
        return []


def generate_static_site() -> Path:
    """Generate docs/index.html, docs/workouts/<id>.html, and docs/workouts.json for GitHub Pages."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    workouts_dir = DOCS_DIR / "workouts"
    workouts_dir.mkdir(parents=True, exist_ok=True)

    workouts = load_workouts()

    # 1. Save docs/workouts.json (omit heavy base64 video streams for fast json loading)
    light_workouts = []
    for w in workouts:
        w_copy = dict(w)
        exs = []
        for ex in w.get("exercises", []):
            e_copy = dict(ex)
            # If video_src is base64, truncate or skip in feed to keep json small
            if e_copy.get("video_src", "").startswith("data:"):
                e_copy["has_video"] = True
                del e_copy["video_src"]
            if e_copy.get("image", "").startswith("data:"):
                del e_copy["image"]
            exs.append(e_copy)
        w_copy["exercises"] = exs
        light_workouts.append(w_copy)

    with open(DOCS_DIR / "workouts.json", "w", encoding="utf-8") as f:
        json.dump(light_workouts, f, ensure_ascii=False, indent=2)

    # 2. Render each standalone workout page into docs/workouts/<id>.html
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("workout.html.jinja")

    for w in workouts:
        w_id = w.get("id") or "workout"
        rendered_html = template.render(workout=w, has_back_link=True)
        out_page = workouts_dir / f"{w_id}.html"
        with open(out_page, "w", encoding="utf-8") as f:
            f.write(rendered_html)

    # 3. Generate docs/index.html (The Workout Hub Dashboard)
    workouts_json_str = json.dumps(light_workouts, ensure_ascii=False)

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover" />
  <meta name="theme-color" content="#12100E" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <title>Workout Hub — Personal Training Programs</title>
  <meta name="description" content="AI-generated interactive workouts extracted from YouTube Shorts and Instagram Reels with form cues, exercise timers, and checklists." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    img, video {{ max-width: 100%; height: auto; }}
    :root {{
      --bg: #12100E;
      --surface: #1B1815;
      --surface2: #26221E;
      --surface3: #332E29;
      --line: #38322B;
      --line2: #4D453C;
      --ink: #F7F3EE;
      --ink2: #B5ACA1;
      --ink3: #7D746A;
      --accent: #E05338;
      --accent-glow: rgba(224, 83, 56, 0.25);
      --accent-soft: rgba(224, 83, 56, 0.12);
      --done: #4EAD71;
      --done-soft: rgba(78, 173, 113, 0.15);
      --font-display: "Barlow Condensed", "Arial Narrow", -apple-system, sans-serif;
      --font-body: "Barlow", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    html {{ -webkit-text-size-adjust: 100%; background: var(--bg); scroll-behavior: smooth; }}
    body {{
      background: var(--bg);
      color: var(--ink);
      font-family: var(--font-body);
      min-height: 100vh;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      padding-bottom: 60px;
    }}
    a {{ color: inherit; text-decoration: none; }}
    .container {{ max-width: 1080px; margin: 0 auto; padding: 0 16px; }}

    /* Header */
    header.hero {{
      padding: 40px 0 24px;
      border-bottom: 1px solid var(--line);
      position: relative;
    }}
    .hero-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 12px;
    }}
    .badge-hub {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .12em;
      text-transform: uppercase;
      color: var(--accent);
      background: var(--accent-soft);
      border: 1px solid var(--accent-glow);
      padding: 4px 10px;
      border-radius: 999px;
    }}
    .stats-summary {{
      display: flex;
      gap: 16px;
      font-size: 13px;
      color: var(--ink3);
    }}
    .stats-summary b {{ color: var(--ink); font-weight: 600; }}
    h1 {{
      font-family: var(--font-display);
      font-size: clamp(34px, 7vw, 54px);
      font-weight: 800;
      line-height: 1.05;
      letter-spacing: -.01em;
      text-transform: uppercase;
      margin-bottom: 8px;
    }}
    .hero-sub {{
      color: var(--ink2);
      font-size: 16px;
      max-width: 600px;
    }}

    /* Controls: Search & Filters */
    .controls {{
      margin: 24px 0 32px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .search-box {{
      position: relative;
    }}
    .search-box svg {{
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--ink3);
      width: 18px;
      height: 18px;
      pointer-events: none;
    }}
    .search-input {{
      width: 100%;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px 14px 12px 42px;
      color: var(--ink);
      font-family: inherit;
      font-size: 15px;
      outline: none;
      transition: border-color .2s, box-shadow .2s;
    }}
    .search-input:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }}
    .filter-row {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
    }}
    .filter-lbl {{
      font-size: 12px;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: var(--ink3);
      font-weight: 600;
      margin-right: 4px;
    }}
    .filter-btn {{
      font-family: inherit;
      font-size: 13px;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 999px;
      background: var(--surface);
      border: 1px solid var(--line);
      color: var(--ink2);
      cursor: pointer;
      transition: all .15s ease;
    }}
    .filter-btn:hover {{
      background: var(--surface2);
      color: var(--ink);
    }}
    .filter-btn.active {{
      background: var(--accent);
      border-color: var(--accent);
      color: #FFFFFF;
    }}

    /* Grid of Workout Cards */
    .workout-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 20px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 16px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: transform .2s, border-color .2s, box-shadow .2s;
      position: relative;
    }}
    .card:hover {{
      transform: translateY(-2px);
      border-color: var(--line2);
      box-shadow: 0 10px 24px rgba(0,0,0,0.3);
    }}
    .card-top {{
      padding: 18px 18px 12px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .card-category {{
      font-size: 12px;
      font-weight: 700;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: var(--accent);
    }}
    .card-diff {{
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 999px;
      background: var(--surface2);
      color: var(--ink2);
    }}
    .card-body {{
      padding: 18px;
      display: flex;
      flex-direction: column;
      flex: 1;
    }}
    .card-title {{
      font-family: var(--font-display);
      font-size: 24px;
      font-weight: 700;
      line-height: 1.15;
      margin-bottom: 8px;
      color: var(--ink);
    }}
    .card-desc {{
      font-size: 14px;
      color: var(--ink2);
      line-height: 1.4;
      margin-bottom: 16px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .card-stats {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
      margin-bottom: 16px;
      background: var(--surface2);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px 10px;
    }}
    .c-stat-val {{
      font-family: var(--font-display);
      font-size: 18px;
      font-weight: 700;
      color: var(--ink);
      line-height: 1;
    }}
    .c-stat-lbl {{
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: var(--ink3);
      margin-top: 3px;
    }}
    .card-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-bottom: 18px;
    }}
    .eq-chip {{
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 6px;
      background: var(--surface3);
      color: var(--ink2);
    }}
    .card-footer {{
      margin-top: auto;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .btn-start {{
      flex: 1;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      background: var(--accent);
      color: #FFFFFF;
      font-weight: 700;
      font-family: var(--font-display);
      font-size: 16px;
      letter-spacing: .04em;
      text-transform: uppercase;
      padding: 12px;
      border-radius: 10px;
      transition: background .15s ease;
    }}
    .btn-start:hover {{ background: #f0644a; }}
    .btn-source {{
      width: 42px;
      height: 42px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: var(--surface2);
      border: 1px solid var(--line);
      border-radius: 10px;
      color: var(--ink3);
      transition: all .15s;
    }}
    .btn-source:hover {{
      color: var(--ink);
      border-color: var(--line2);
    }}

    /* Empty state */
    .empty-state {{
      text-align: center;
      padding: 60px 20px;
      color: var(--ink3);
      grid-column: 1 / -1;
    }}

    @media (max-width: 600px) {{
      .hero-top {{ flex-direction: column; align-items: flex-start; }}
      .workout-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<div class="container">
  <header class="hero">
    <div class="hero-top">
      <span class="badge-hub">⚡ WORKOUT HELPER</span>
      <div class="stats-summary">
        <span>Programs: <b id="stat-count">{len(workouts)}</b></span>
        <span>Hosted 100% Free on GitHub Pages</span>
      </div>
    </div>
    <h1>Personal Workout Lab</h1>
    <p class="hero-sub">Interactive training sessions extracted from Instagram Reels & YouTube Shorts — complete with exercise check-offs, rest timers, and form cues.</p>
  </header>

  <div class="controls">
    <div class="search-box">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      <input type="text" id="searchInput" class="search-input" placeholder="Search exercises, workout focus, or equipment (e.g. Squat, Chair, Full Body)..." />
    </div>

    <div class="filter-row">
      <span class="filter-lbl">Category:</span>
      <button class="filter-btn active" data-cat="all">All</button>
      <button class="filter-btn" data-cat="Full Body">Full Body</button>
      <button class="filter-btn" data-cat="Upper Body">Upper Body</button>
      <button class="filter-btn" data-cat="Lower Body">Lower Body</button>
      <button class="filter-btn" data-cat="Core">Core</button>
      <button class="filter-btn" data-cat="HIIT">HIIT</button>
    </div>
  </div>

  <main class="workout-grid" id="grid">
    <!-- Populated by JavaScript -->
  </main>
</div>

<script>
const WORKOUTS = {workouts_json_str};

let activeCategory = 'all';
let searchQuery = '';

function renderWorkouts() {{
  const grid = document.getElementById('grid');
  const query = searchQuery.trim().toLowerCase();

  const filtered = WORKOUTS.filter(w => {{
    // Category match
    if (activeCategory !== 'all' && (!w.category || !w.category.toLowerCase().includes(activeCategory.toLowerCase()))) {{
      return false;
    }}
    // Search match
    if (query) {{
      const text = [
        w.title || '',
        w.description || '',
        w.category || '',
        w.difficulty || '',
        ...(w.equipment || []),
        ...(w.exercises || []).map(e => e.title + ' ' + (e.target_muscles || []).join(' '))
      ].join(' ').toLowerCase();
      if (!text.includes(query)) return false;
    }}
    return true;
  }});

  document.getElementById('stat-count').textContent = filtered.length;

  if (filtered.length === 0) {{
    grid.innerHTML = `
      <div class="empty-state">
        <h3>No workouts found</h3>
        <p style="margin-top:6px;font-size:14px;">Try searching for a different exercise or clear the filter.</p>
      </div>
    `;
    return;
  }}

  grid.innerHTML = filtered.map(w => {{
    const duration = w.estimated_duration || '20-30m';
    const exCount = (w.exercises || []).length;
    const blocks = w.blocks_count || '1 Circuit';
    const chipsHtml = (w.equipment || []).slice(0, 3).map(eq => `<span class="eq-chip">${{eq}}</span>`).join('');
    const pageUrl = `workouts/${{w.id}}.html`;

    return `
      <article class="card">
        <div class="card-top">
          <span class="card-category">${{w.category || 'General'}}</span>
          <span class="card-diff">${{w.difficulty || 'All Levels'}}</span>
        </div>
        <div class="card-body">
          <h2 class="card-title">${{w.title}}</h2>
          <p class="card-desc">${{w.description || 'Interactive guided session with video clips and rest timers.'}}</p>
          
          <div class="card-stats">
            <div><div class="c-stat-val">${{duration}}</div><div class="c-stat-lbl">Duration</div></div>
            <div><div class="c-stat-val">${{exCount}}</div><div class="c-stat-lbl">Exercises</div></div>
            <div><div class="c-stat-val">${{blocks}}</div><div class="c-stat-lbl">Blocks</div></div>
          </div>

          <div class="card-chips">
            ${{chipsHtml}}
          </div>

          <div class="card-footer">
            <a href="${{pageUrl}}" class="btn-start">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              Start Workout
            </a>
            ${{w.source_url ? `
              <a href="${{w.source_url}}" target="_blank" rel="noopener" class="btn-source" title="View Source Video">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              </a>
            ` : ''}}
          </div>
        </div>
      </article>
    `;
  }}).join('');
}}

// Filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeCategory = btn.dataset.cat;
    renderWorkouts();
  }});
}});

// Search input
document.getElementById('searchInput').addEventListener('input', (e) => {{
  searchQuery = e.target.value;
  renderWorkouts();
}});

renderWorkouts();
</script>
</body>
</html>
"""

    with open(DOCS_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"[export] Generated static hub at docs/index.html with {len(workouts)} workouts and {len(workouts)} standalone pages.")
    return DOCS_DIR


def auto_sync_github() -> dict:
    """Stage docs/ and data/workouts.json, commit, and push to GitHub Pages."""
    # Check if inside git work tree
    is_git = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    if is_git.returncode != 0:
        return {
            "exported": True,
            "git_synced": False,
            "message": "Static site generated in docs/. Initialize git and set remote origin to enable auto-push."
        }

    try:
        # Stage docs/ and canonical data
        subprocess.run(["git", "add", "docs/", "data/workouts.json"], check=True)

        # Check for uncommitted changes
        status = subprocess.run(["git", "status", "--porcelain", "docs/", "data/workouts.json"], capture_output=True, text=True)
        if not status.stdout.strip():
            return {
                "exported": True,
                "git_synced": True,
                "message": "Docs are already up to date with git."
            }

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(["git", "commit", "-m", f"Auto-update workout pages [{now_str}]"], check=True)

        # Check for remote origin
        remotes = subprocess.run(["git", "remote"], capture_output=True, text=True)
        if "origin" in remotes.stdout:
            push_res = subprocess.run(["git", "push"], capture_output=True, text=True, timeout=25)
            if push_res.returncode == 0:
                print("[github] Successfully pushed updated docs/ to GitHub!")
                return {
                    "exported": True,
                    "git_synced": True,
                    "message": "Successfully published latest workouts to GitHub Pages!"
                }
            else:
                print(f"[github push warning]: {push_res.stderr}")
                return {
                    "exported": True,
                    "git_synced": False,
                    "message": f"Git commit created. Push failed: {push_res.stderr[:80]}"
                }
        else:
            return {
                "exported": True,
                "git_synced": False,
                "message": "Git commit created. Add remote origin to push automatically."
            }

    except Exception as e:
        print(f"[github sync error]: {e}")
        return {"exported": True, "git_synced": False, "error": str(e)}


if __name__ == "__main__":
    generate_static_site()
    res = auto_sync_github()
    print("Result:", res)
