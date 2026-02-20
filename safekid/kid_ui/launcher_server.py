"""
SafeKid Flash — Launcher Server v2
=====================================
Flask mini-server dengan fitur lengkap:
  - Kid UI  : http://localhost:5556/
  - Parent  : http://localhost:5556/parent
  - API     : http://localhost:5556/api/...

Jalankan:
    python launcher_server.py --demo --child-name "Budi" --total-minutes 90

Opsi lengkap:
    python launcher_server.py --help
"""

import argparse
import configparser
import hashlib
import json
import logging
import os
import secrets
import sys
import threading
import time
from datetime import datetime, date
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

# ── Path setup ────────────────────────────────────
HERE         = Path(__file__).parent
SAFEKID_ROOT = HERE.parent.parent          # E:\SafeKidFlash\
APPS_DIR     = SAFEKID_ROOT / "safekid" / "apps"
CATALOG_PATH = APPS_DIR / "apps_catalog.json"
INTEGRATION_DIR = SAFEKID_ROOT / "safekid" / "integration"

# ── Add integration to path ───────────────────────
sys.path.insert(0, str(SAFEKID_ROOT))

# ── Import internal modules ───────────────────────
try:
    from safekid.apps.apps_launcher import AppsLauncher
    HAS_LAUNCHER = True
except ImportError:
    HAS_LAUNCHER = False
    logger.warning("AppsLauncher not found — using basic mode")

try:
    import requests as req_lib
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Logging: dual handler (file + console) ────────────────────
LOG_FILE = SAFEKID_ROOT / "safekid.log"

_log_handlers = [logging.StreamHandler()]
try:
    _log_handlers.append(logging.FileHandler(str(LOG_FILE), encoding="utf-8"))
except Exception:
    pass  # Bukan masalah fatal jika file log tidak bisa dibuat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=_log_handlers,
)
logger = logging.getLogger("safekid.server")

# ── Import i18n & updater ─────────────────────────────────────
try:
    from safekid.i18n import t, set_lang
    HAS_I18N = True
except ImportError:
    HAS_I18N = False
    def t(key, **kwargs): return key  # no-op fallback
    def set_lang(lang): pass

try:
    from safekid.updater import check_update, CURRENT_VERSION
    HAS_UPDATER = True
except ImportError:
    HAS_UPDATER = False
    CURRENT_VERSION = "0.6.0"
    def check_update(**kw): return {"update_available": False, "message": "updater N/A"}

# ── Flask App ─────────────────────────────────────
app = Flask(__name__, static_folder=str(HERE))
app.secret_key = os.environ.get("SAFEKID_SECRET", "safekid-dev-key-change-me")

# ────────────────────────────────────────────────────
#  Global State
# ────────────────────────────────────────────────────
class AppState:
    def __init__(self):
        self.child_name     = "Anak"
        self.child_age      = 0
        self.total_minutes  = 90
        self.used_seconds   = 0     # track in seconds for precision
        self.streak_days    = 1
        self.stars          = 0
        self.lb_url         = "http://localhost:5555"
        self.demo_mode      = True
        # SHA256 of "1234"
        self.admin_pin_hash = "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"
        self.activity_log   = []    # [{icon, name, time, app_id}]
        self._lock          = threading.Lock()
        self._start_time    = time.time()

    @property
    def used_minutes(self):
        return int(self.used_seconds // 60)

    @property
    def remaining_seconds(self):
        total_s = self.total_minutes * 60
        return max(0, total_s - int(self.used_seconds))

    @property
    def total_seconds(self):
        return self.total_minutes * 60

    @property
    def progress_pct(self):
        if self.total_seconds == 0:
            return 100
        return min(100, round((int(self.used_seconds) / self.total_seconds) * 100, 1))

    def to_dict(self):
        with self._lock:
            return {
                "child_name":        self.child_name,
                "child_age":         self.child_age,
                "remaining_seconds": self.remaining_seconds,
                "total_seconds":     self.total_seconds,
                "used_minutes":      self.used_minutes,
                "total_minutes":     self.total_minutes,
                "progress_pct":      self.progress_pct,
                "streak_days":       self.streak_days,
                "stars":             self.stars,
                "demo_mode":        self.demo_mode,
                "timestamp":         datetime.now().isoformat(),
                "date":              date.today().isoformat(),
                "server_uptime_s":   int(time.time() - self._start_time),
            }

STATE   = AppState()

def hash_pin(pin_text: str) -> str:
    """Return SHA256 hash of the PIN."""
    return hashlib.sha256(pin_text.encode("utf-8")).hexdigest()

def verify_pin(input_pin: str) -> bool:
    """Check input PIN against stored hash."""
    if not input_pin: return False
    return hash_pin(input_pin) == STATE.admin_pin_hash
LAUNCHER = None   # AppsLauncher instance — set in main()

# ────────────────────────────────────────────────────
#  Background threads
# ────────────────────────────────────────────────────
def demo_ticker():
    """Demo: waktu berjalan secara real-time (1 detik = 1 detik)."""
    while True:
        time.sleep(1)
        if STATE.demo_mode and STATE.used_seconds < STATE.total_seconds:
            with STATE._lock:
                STATE.used_seconds += 1

def lb_poller():
    """Poll Little Brother API tiap 60 detik."""
    while True:
        time.sleep(60)
        if STATE.demo_mode or not HAS_REQUESTS:
            continue
        try:
            r = req_lib.get(
                f"{STATE.lb_url}/api/v1/user-status",
                timeout=5
            )
            if r.ok:
                data = r.json()
                user_data = (data.get(STATE.child_name)
                             or data.get(STATE.child_name.lower()))
                if user_data:
                    with STATE._lock:
                        mins = int(user_data.get("minutes_today", STATE.used_minutes))
                        STATE.used_seconds = mins * 60
                        total = int(user_data.get("max_time_per_day", STATE.total_minutes))
                        STATE.total_minutes = total
                    logger.info(f"[LB] Synced: {STATE.used_minutes}/{STATE.total_minutes} min")
        except Exception as e:
            logger.debug(f"[LB] Poll error: {e}")

# ────────────────────────────────────────────────────
#  Kid UI Routes
# ────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the kid launcher HTML."""
    html_path = HERE / "launcher.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>launcher.html not found</h1>", 404


@app.route("/api/status")
def api_status():
    """Status waktu anak."""
    return jsonify(STATE.to_dict())


@app.route("/api/apps")
def api_apps():
    """Daftar app dari catalog."""
    if LAUNCHER:
        age       = request.args.get("age", STATE.child_age, type=int)
        category  = request.args.get("cat", None)
        if category:
            apps = [a.to_dict() for a in LAUNCHER.get_apps_by_category(category)]
        else:
            apps = LAUNCHER.apps_as_dict(age=age)
        categories = LAUNCHER.get_categories()
    else:
        # Fallback: baca catalog langsung
        try:
            with open(CATALOG_PATH, encoding="utf-8") as f:
                data = json.load(f)
            apps_data  = [a for a in data.get("apps", []) if a.get("enabled", True)]
            categories = data.get("categories", {})
            
            # Manual filtering
            if category:
                apps_data = [a for a in apps_data if a.get("category") == category]
                
            apps = apps_data  # they are already dicts
        except Exception:
            apps, categories = [], {}

    return jsonify({"apps": apps, "categories": categories, "count": len(apps)})


@app.route("/api/launch", methods=["POST"])
def api_launch():
    """Launch sebuah app."""
    data   = request.get_json(silent=True) or {}
    app_id = data.get("app_id", "")

    if not app_id:
        return jsonify({"ok": False, "message": "app_id required"}), 400

    # Tambah bintang
    with STATE._lock:
        STATE.stars = min(STATE.stars + 1, 9999)

    # Log activity
    icon = data.get("icon", "🔵")
    name = data.get("name", app_id)
    now  = datetime.now()
    with STATE._lock:
        STATE.activity_log.insert(0, {
            "app_id":    app_id,
            "name":      name,
            "icon":      icon,
            "time_str":  now.strftime("%H:%M"),
            "timestamp": now.isoformat(),
        })
        STATE.activity_log = STATE.activity_log[:20]

    # Launch app
    if LAUNCHER:
        result = LAUNCHER.launch(app_id)
        logger.info(f"[LAUNCH] {app_id}: {result.message}")
        return jsonify({
            "ok":      result.success,
            "message": result.message,
            "pid":     result.pid,
            "stars":   STATE.stars,
        })
    else:
        logger.info(f"[LAUNCH-BASIC] {app_id} (no launcher module)")
        return jsonify({
            "ok":      True,
            "message": f"Membuka {name}...",
            "stars":   STATE.stars,
        })


@app.route("/api/activity")
def api_activity():
    return jsonify(STATE.activity_log)

# ────────────────────────────────────────────────────
#  Parent Dashboard
# ────────────────────────────────────────────────────

PARENT_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>SafeKid Flash — Orang Tua</title>
  <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Fredoka+One&display=swap" rel="stylesheet"/>
  <style>
    :root {
      --bg: #0d1117; --card: #161b22; --border: #30363d;
      --text: #e6edf3; --muted: #8b949e; --accent: #58a6ff;
      --green: #3fb950; --red: #f85149; --yellow: #d29922;
      --purple: #bc8cff; --radius: 12px;
    }
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family:'Nunito',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; }
    .topbar { background:var(--card); border-bottom:1px solid var(--border); padding:16px 32px; display:flex; align-items:center; justify-content:space-between; }
    .logo { font-family:'Fredoka One',cursive; font-size:20px; color:var(--accent); display:flex; align-items:center; gap:10px; }
    .badge { background:rgba(88,166,255,0.15); border:1px solid rgba(88,166,255,0.3); border-radius:100px; padding:4px 12px; font-size:12px; font-weight:700; color:var(--accent); }
    .kid-link { text-decoration:none; background:rgba(63,185,80,0.15); border:1px solid rgba(63,185,80,0.3); border-radius:8px; padding:8px 16px; font-size:13px; font-weight:700; color:var(--green); }
    .container { max-width:1100px; margin:0 auto; padding:28px 24px; display:flex; flex-direction:column; gap:20px; }
    h2 { font-family:'Fredoka One',cursive; font-size:22px; margin-bottom:2px; }
    .subtitle { font-size:13px; color:var(--muted); }
    .grid-3 { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    .card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:20px; }
    .stat-card { text-align:center; }
    .stat-val { font-family:'Fredoka One',cursive; font-size:40px; margin:8px 0 4px; }
    .stat-lbl { font-size:12px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:1px; }
    .prog-wrap { background:rgba(255,255,255,0.08); border-radius:100px; height:10px; margin-top:12px; overflow:hidden; }
    .prog-bar  { height:100%; border-radius:100px; transition:width 0.5s; }
    .section-title { font-size:12px; font-weight:800; letter-spacing:2px; text-transform:uppercase; color:var(--muted); margin-bottom:14px; }
    .input-row { display:flex; gap:10px; align-items:center; margin-top:14px; flex-wrap:wrap; }
    .input-field { background:rgba(255,255,255,0.06); border:1px solid var(--border); border-radius:8px; padding:10px 14px; color:var(--text); font-size:14px; font-family:'Nunito',sans-serif; flex:1; min-width:100px; }
    .input-field:focus { outline:none; border-color:var(--accent); }
    .btn { padding:10px 20px; border-radius:8px; border:none; cursor:pointer; font-size:14px; font-weight:700; font-family:'Nunito',sans-serif; transition:all 0.2s; }
    .btn-green { background:rgba(63,185,80,0.2); border:1px solid rgba(63,185,80,0.4); color:var(--green); }
    .btn-green:hover { background:rgba(63,185,80,0.35); transform:translateY(-2px); }
    .btn-blue { background:rgba(88,166,255,0.2); border:1px solid rgba(88,166,255,0.4); color:var(--accent); }
    .btn-blue:hover { background:rgba(88,166,255,0.35); transform:translateY(-2px); }
    .btn-red { background:rgba(248,81,73,0.15); border:1px solid rgba(248,81,73,0.3); color:var(--red); }
    .btn-red:hover { background:rgba(248,81,73,0.3); }
    .msg { padding:10px 14px; border-radius:8px; font-size:13px; font-weight:700; margin-top:10px; display:none; }
    .msg-ok  { background:rgba(63,185,80,0.15); border:1px solid rgba(63,185,80,0.3); color:var(--green); }
    .msg-err { background:rgba(248,81,73,0.15); border:1px solid rgba(248,81,73,0.3); color:var(--red); }
    .app-row { display:flex; align-items:center; gap:12px; padding:10px 14px; border-radius:10px; background:rgba(255,255,255,0.03); border:1px solid transparent; margin-bottom:6px; transition:border-color 0.2s; }
    .app-row:hover { border-color:var(--border); }
    .app-icon-sm { font-size:22px; width:32px; text-align:center; }
    .app-info { flex:1; }
    .app-name-sm { font-size:14px; font-weight:700; }
    .app-cat { font-size:11px; color:var(--muted); font-weight:600; text-transform:uppercase; }
    .toggle { position:relative; display:inline-block; width:44px; height:24px; }
    .toggle input { opacity:0; width:0; height:0; }
    .slider { position:absolute; cursor:pointer; top:0;left:0;right:0;bottom:0; background:#30363d; border-radius:24px; transition:0.3s; }
    .slider:before { position:absolute; content:""; height:18px; width:18px; left:3px; bottom:3px; background:white; border-radius:50%; transition:0.3s; }
    input:checked + .slider { background:var(--green); }
    input:checked + .slider:before { transform:translateX(20px); }
    .activity-row { display:flex; gap:12px; align-items:center; padding:8px 12px; border-radius:8px; background:rgba(255,255,255,0.03); margin-bottom:5px; }
    .activity-time-sm { font-size:11px; color:var(--muted); font-weight:700; }
    .dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; background:var(--green); }
    .pin-locked { display:flex; flex-direction:column; align-items:center; gap:14px; padding:24px; text-align:center; }
    .pin-locked h3 { font-family:'Fredoka One',cursive; font-size:24px; }
    .pin-locked p { color:var(--muted); font-size:14px; }
    #pinSection, #mainContent { }
  </style>
</head>
<body>

<div class="topbar">
  <div class="logo">🛡️ SafeKid Flash <span class="badge">Orang Tua</span></div>
  <a href="/" class="kid-link">👦 Buka Tampilan Anak</a>
</div>

<!-- PIN Gate -->
<div class="container" id="pinSection">
  <div class="card" style="max-width:400px;margin:40px auto;">
    <div class="pin-locked">
      <div style="font-size:48px">🔑</div>
      <h3>Area Orang Tua</h3>
      <p>Masukkan PIN untuk mengakses dashboard pengaturan</p>
      <div style="display:flex;gap:8px;width:100%;">
        <input class="input-field" type="password" id="pinInput" placeholder="Masukkan PIN..." maxlength="10" onkeydown="if(event.key==='Enter') checkPin()"/>
        <button class="btn btn-blue" onclick="checkPin()">Masuk</button>
      </div>
      <div class="msg" id="pinMsg"></div>
      <p style="font-size:11px;color:var(--muted);margin-top:4px;">Default PIN: <code>1234</code></p>
    </div>
  </div>
</div>

<!-- MAIN DASHBOARD -->
<div class="container" id="mainContent" style="display:none;">

  <!-- Header -->
  <div>
    <h2>👋 Dashboard Orang Tua</h2>
    <div class="subtitle" id="dashSubtitle">Mengelola sesi anak</div>
  </div>

  <!-- Stats Row -->
  <div class="grid-3">
    <div class="card stat-card">
      <div class="stat-lbl">⏰ Sisa Waktu</div>
      <div class="stat-val" id="statRemain" style="color:#3fb950">—</div>
      <div class="stat-lbl">menit</div>
      <div class="prog-wrap"><div class="prog-bar" id="progBar" style="background:#3fb950;width:50%"></div></div>
    </div>
    <div class="card stat-card">
      <div class="stat-lbl">📅 Sudah Dipakai</div>
      <div class="stat-val" id="statUsed" style="color:#d29922">—</div>
      <div class="stat-lbl">dari <span id="statTotal">—</span> menit</div>
    </div>
    <div class="card stat-card">
      <div class="stat-lbl">⭐ Bintang</div>
      <div class="stat-val" id="statStars" style="color:#bc8cff">—</div>
      <div class="stat-lbl">dikumpulkan hari ini</div>
    </div>
  </div>

  <!-- Controls + Apps -->
  <div class="grid-2">

    <!-- Time Control -->
    <div class="card">
      <div class="section-title">⏱️ Kontrol Waktu</div>

      <p style="font-size:13px;color:var(--muted);margin-bottom:10px;">Tambah waktu bermain untuk <strong id="kidNameCtrl" style="color:var(--text)">anak</strong>:</p>
      <div class="input-row">
        <input class="input-field" type="number" id="addMins" value="15" min="1" max="120" placeholder="Menit"/>
        <button class="btn btn-green" onclick="addTime()">➕ Tambah Waktu</button>
      </div>
      <div class="msg" id="addTimeMsg"></div>

      <hr style="border:none;border-top:1px solid var(--border);margin:18px 0"/>

      <p style="font-size:13px;color:var(--muted);margin-bottom:10px;">Atur total waktu harian:</p>
      <div class="input-row">
        <input class="input-field" type="number" id="setTotal" value="90" min="10" max="480" placeholder="Menit"/>
        <button class="btn btn-blue" onclick="setTotalTime()">✏️ Simpan</button>
      </div>
      <div class="msg" id="setTimeMsg"></div>

      <hr style="border:none;border-top:1px solid var(--border);margin:18px 0"/>
      <button class="btn btn-red" onclick="if(confirm('Habiskan waktu sekarang?')) endSession()" style="width:100%">
        ⛔ Akhiri Sesi Sekarang
      </button>
    </div>

    <!-- App Manager -->
    <div class="card">
      <div class="section-title">📱 Aplikasi Tersedia</div>
      <div id="appListAdmin" style="max-height:280px;overflow-y:auto;">
        <div style="color:var(--muted);font-size:13px;">Memuat...</div>
      </div>
    </div>

  </div>

  <!-- Activity Log -->
  <div class="card">
    <div class="section-title">📋 Aktivitas Hari Ini</div>
    <div id="activityAdmin" style="max-height:200px;overflow-y:auto;">
      <div style="color:var(--muted);font-size:13px;">Belum ada aktivitas</div>
    </div>
  </div>

  <!-- Info -->
  <div class="card" style="background:rgba(88,166,255,0.05);border-color:rgba(88,166,255,0.2);">
    <div class="section-title">ℹ️ Informasi Server</div>
    <div id="serverInfo" style="font-size:13px;color:var(--muted);line-height:2;">Memuat...</div>
  </div>

</div><!-- end mainContent -->

<script>
  const PIN_KEY = 'safekid_pin_ok';
  let savedPin  = '';

  // ── PIN ─────────────────────────────────────
  function checkPin() {
    const pin = document.getElementById('pinInput').value;
    fetch('/api/admin/status', {
      headers: { 'X-SafeKid-PIN': pin }
    }).then(r => {
      if (r.ok) {
        savedPin = pin;
        document.getElementById('pinSection').style.display = 'none';
        document.getElementById('mainContent').style.display = 'flex';
        loadAll();
        setInterval(loadAll, 10000);
      } else {
        showMsg('pinMsg', '❌ PIN salah!', false);
      }
    }).catch(() => showMsg('pinMsg', '❌ Server tidak merespons', false));
  }

  // Auto-check if pin stored
  window.addEventListener('load', () => {
    document.getElementById('pinInput').addEventListener('keydown', e => {
      if (e.key === 'Enter') checkPin();
    });
  });

  // ── Load Data ────────────────────────────────
  function loadAll() {
    loadStatus();
    loadApps();
    loadActivity();
  }

  function loadStatus() {
    fetch('/api/admin/status', { headers: { 'X-SafeKid-PIN': savedPin } })
      .then(r => r.json())
      .then(d => {
        const rem = Math.floor(d.remaining_seconds / 60);
        document.getElementById('statRemain').textContent = rem;
        document.getElementById('statUsed').textContent   = d.used_minutes;
        document.getElementById('statTotal').textContent  = d.total_minutes;
        document.getElementById('statStars').textContent  = d.stars;
        document.getElementById('kidNameCtrl').textContent = d.child_name;
        document.getElementById('dashSubtitle').textContent =
          `Mengelola sesi ${d.child_name} — ${d.date} | Mode: ${d.demo_mode ? '🎭 Demo' : '🔗 Little Brother'}`;
        document.getElementById('setTotal').value = d.total_minutes;

        const pct = d.total_seconds ? Math.round((d.remaining_seconds / d.total_seconds)*100) : 0;
        const progEl = document.getElementById('progBar');
        progEl.style.width = pct + '%';
        progEl.style.background = pct > 50 ? '#3fb950' : pct > 25 ? '#d29922' : '#f85149';

        document.getElementById('serverInfo').innerHTML =
          `<b>Child:</b> ${d.child_name} (usia ${d.child_age || '?'}) &nbsp;|&nbsp;`+
          `<b>Uptime:</b> ${Math.floor(d.server_uptime_s/60)} menit &nbsp;|&nbsp;`+
          `<b>Date:</b> ${d.date} &nbsp;|&nbsp;`+
          `<b>Demo Mode:</b> ${d.demo_mode} &nbsp;|&nbsp;`+
          `<b>Version:</b> SafeKid Flash 2.0`;
      }).catch(console.warn);
  }

  function loadApps() {
    fetch('/api/apps').then(r=>r.json()).then(d => {
      const el = document.getElementById('appListAdmin');
      if (!d.apps || !d.apps.length) {
        el.innerHTML = '<div style="color:var(--muted);font-size:13px;">Tidak ada app</div>';
        return;
      }
      el.innerHTML = d.apps.map(a => `
        <div class="app-row">
          <div class="app-icon-sm">${a.icon}</div>
          <div class="app-info">
            <div class="app-name-sm">${a.name}</div>
            <div class="app-cat">${a.category} · usia ${a.min_age}–${a.max_age}</div>
          </div>
          <label class="toggle">
            <input type="checkbox" ${a.enabled ? 'checked' : ''}
              onchange="toggleApp('${a.id}', this.checked)"/>
            <span class="slider"></span>
          </label>
        </div>
      `).join('');
    }).catch(console.warn);
  }

  function loadActivity() {
    fetch('/api/activity').then(r=>r.json()).then(log => {
      const el = document.getElementById('activityAdmin');
      if (!log.length) {
        el.innerHTML = '<div style="color:var(--muted);font-size:13px;">Belum ada aktivitas</div>';
        return;
      }
      const colors = ['#3fb950','#58a6ff','#bc8cff','#d29922'];
      el.innerHTML = log.slice(0,10).map((a,i) => `
        <div class="activity-row">
          <div class="dot" style="background:${colors[i%4]}"></div>
          <span style="font-size:18px">${a.icon||'🔵'}</span>
          <div style="flex:1;font-size:13px;font-weight:700;">${a.name}</div>
          <div class="activity-time-sm">${a.time_str}</div>
        </div>
      `).join('');
    }).catch(console.warn);
  }

  // ── Actions ──────────────────────────────────
  function addTime() {
    const mins = parseInt(document.getElementById('addMins').value) || 15;
    apiPost('/api/admin/set-time', { pin: savedPin, add_minutes: mins })
      .then(d => showMsg('addTimeMsg', d.ok ? `✅ ${d.message}` : `❌ ${d.error}`, d.ok))
      .then(() => setTimeout(loadStatus, 500));
  }

  function setTotalTime() {
    const mins = parseInt(document.getElementById('setTotal').value) || 90;
    apiPost('/api/admin/set-time', { pin: savedPin, set_total_minutes: mins })
      .then(d => showMsg('setTimeMsg', d.ok ? `✅ ${d.message}` : `❌ ${d.error}`, d.ok))
      .then(() => setTimeout(loadStatus, 500));
  }

  function endSession() {
    apiPost('/api/admin/set-time', { pin: savedPin, set_used_seconds: 999999 })
      .then(d => showMsg('addTimeMsg', d.ok ? '⛔ Sesi diakhiri' : `❌ ${d.error}`, d.ok));
  }

  function toggleApp(appId, enabled) {
    fetch('/api/admin/toggle-app', {
      method: 'POST',
      headers: { 'Content-Type':'application/json', 'X-SafeKid-PIN': savedPin },
      body: JSON.stringify({ app_id: appId, enabled })
    }).then(r=>r.json()).then(d => {
      if (!d.ok) alert('Gagal: ' + d.error);
    });
  }

  function apiPost(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type':'application/json', 'X-SafeKid-PIN': savedPin },
      body: JSON.stringify(body)
    }).then(r => r.json());
  }

  function showMsg(id, text, ok) {
    const el = document.getElementById(id);
    el.textContent = text;
    el.className = 'msg ' + (ok ? 'msg-ok' : 'msg-err');
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3000);
  }
</script>
</body>
</html>
"""


@app.route("/parent")
def parent_dashboard():
    """Serve parent dashboard HTML."""
    return PARENT_HTML


@app.route("/api/admin/status")
def api_admin_status():
    """Extended status for parent dashboard (PIN protected)."""
    pin = request.headers.get("X-SafeKid-PIN") or (request.get_json(silent=True) or {}).get("pin")
    if not verify_pin(pin):
        return jsonify({"error": "Wrong PIN"}), 403
    return jsonify({
        **STATE.to_dict(),
        "activity_log": STATE.activity_log[:10],
        "server_version": "2.0.0",
        "safekid_version": "SafeKid Flash 2.0",
    })


@app.route("/api/admin/set-time", methods=["POST"])
def api_admin_set_time():
    """Parent: kontrol waktu (add / set total / end session)."""
    data = request.get_json(silent=True) or {}
    pin  = data.get("pin") or request.headers.get("X-SafeKid-PIN")
    if not verify_pin(pin):
        return jsonify({"error": "Wrong PIN"}), 403

    with STATE._lock:
        if "add_minutes" in data:
            add = max(0, int(data["add_minutes"]))
            STATE.used_seconds = max(0, STATE.used_seconds - add * 60)
            return jsonify({"ok": True, "message": f"Ditambah {add} menit! 🎉"})

        if "set_total_minutes" in data:
            STATE.total_minutes = max(1, int(data["set_total_minutes"]))
            return jsonify({"ok": True, "message": f"Total diubah ke {STATE.total_minutes} menit"})

        if "set_used_seconds" in data:  # end session
            STATE.used_seconds = STATE.total_seconds + 1
            return jsonify({"ok": True, "message": "Sesi diakhiri"})

    return jsonify({"error": "No action specified"}), 400


@app.route("/api/admin/toggle-app", methods=["POST"])
def api_admin_toggle_app():
    """Parent: enable/disable an app."""
    data    = request.get_json(silent=True) or {}
    pin     = data.get("pin") or request.headers.get("X-SafeKid-PIN")
    if not verify_pin(pin):
        return jsonify({"error": "Wrong PIN"}), 403

    app_id  = data.get("app_id")
    enabled = data.get("enabled", True)

    if LAUNCHER and app_id:
        ok = LAUNCHER.toggle_app(app_id, bool(enabled))
        return jsonify({"ok": ok, "app_id": app_id, "enabled": enabled})
    return jsonify({"ok": False, "error": "Launcher not available"}), 500


@app.route("/themes/<path:filename>")
def serve_theme(filename):
    return send_from_directory(str(HERE / "themes"), filename)


@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 Not Found: {request.method} {request.url}")
    return jsonify({
        "error": "Endpoint tidak ditemukan",
        "hint":  "Coba: / atau /parent atau /api/status",
        "code":  404,
    }), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"500 Internal Server Error: {e}", exc_info=True)
    return jsonify({
        "error":   "Terjadi kesalahan di server",
        "detail":  str(e),
        "code":    500,
    }), 500


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        "error": "Method tidak diizinkan",
        "hint":  f"Gunakan {', '.join(e.valid_methods or [])}",
        "code":  405,
    }), 405


@app.route("/api/update-check")
def api_update_check():
    """Check GitHub for a newer version."""
    force = request.args.get("force", "false").lower() == "true"
    if HAS_UPDATER:
        result = check_update(force=force)
        result["server_version"] = CURRENT_VERSION
        return jsonify(result)
    return jsonify({
        "update_available": False,
        "message": "Updater module tidak tersedia.",
        "current_version": CURRENT_VERSION,
    })


@app.route("/api/i18n")
def api_i18n():
    """Return translation strings for the current language (for frontend use)."""
    if not HAS_I18N:
        return jsonify({"lang": "id", "strings": {}})
    from safekid.i18n import TRANSLATIONS, _CURRENT_LANG
    lang = request.args.get("lang", _CURRENT_LANG)
    strings = TRANSLATIONS.get(lang, TRANSLATIONS["id"])
    return jsonify({"lang": lang, "strings": strings})




# ────────────────────────────────────────────────────
#  Setup Wizard
# ────────────────────────────────────────────────────
def run_setup(config_path):
    """Interactive setup wizard to set secure PIN."""
    print("🔐 SafeKid Flash — Security Setup")
    print("====================================")
    
    while True:
        try:
            line1 = input("Masukkan PIN Orang Tua baru (4-8 digit): ")
            new_pin = line1.strip()
        except EOFError:
            return

        if not new_pin.isdigit() or len(new_pin) < 4:
            print("❌ PIN harus berupa angka minimal 4 digit.")
            continue
            
        try:
            line2 = input("Konfirmasi PIN: ")
            confirm = line2.strip()
        except EOFError:
            return

        if new_pin != confirm:
            print("❌ PIN tidak cocok. Coba lagi.")
            continue
            
        break
    
    # Calculate hash
    p_hash = hash_pin(new_pin)
    
    # Save to config
    conf = configparser.ConfigParser()
    if os.path.exists(config_path):
        conf.read(config_path)
    
    if not conf.has_section("general"):
        conf.add_section("general")
        
    conf.set("general", "admin_pin_hash", p_hash)
    # Remove plain pin if exists
    if conf.has_option("general", "admin_pin"):
        conf.remove_option("general", "admin_pin")
        
    try:    
        with open(config_path, "w") as f:
            conf.write(f)
        print(f"✅ PIN berhasil disimpan! Hash: {p_hash[:8]}...")
    except Exception as e:
        print(f"❌ Gagal menyimpan config: {e}")


# ────────────────────────────────────────────────────
#  Main
# ────────────────────────────────────────────────────

def main():
    global LAUNCHER

    parser = argparse.ArgumentParser(description="SafeKid Flash Launcher Server v2")
    parser.add_argument("--config",         default=str(SAFEKID_ROOT / "config" / "safekid_default.conf"))
    parser.add_argument("--setup",          action="store_true", help="Run initial setup wizard")
    parser.add_argument("--child-name",     default=None)
    parser.add_argument("--child-age",      type=int, default=None)
    parser.add_argument("--port",           type=int, default=None)
    parser.add_argument("--total-minutes",  type=int, default=None)
    parser.add_argument("--used-minutes",   type=int, default=0)
    parser.add_argument("--lb-url",         default=None)
    parser.add_argument("--demo",           action="store_true")
    # --pin removed from CLI for security, use config or setup
    args = parser.parse_args()

    # 0. Setup Mode
    if args.setup:
        run_setup(args.config)
        return


    # 1. Load defaults from config file
    conf = configparser.ConfigParser()
    if Path(args.config).exists():
        conf.read(args.config)
        logger.info(f"Loaded config from {args.config}")
    
    # helper for config fallback
    def get_conf(section, key, fallback):
        return conf.get(section, key, fallback=fallback)
        
    def get_int(section, key, fallback):
        try:
            val = get_conf(section, key, str(fallback))
            return int(val)
        except (ValueError, TypeError, configparser.Error):
            logger.warning(f"Config error [{section}] {key}. Using default {fallback}.")
            return fallback

    # 2. State precedence: CLI arg > Config file > Default hardcoded
    STATE.child_name    = args.child_name or get_conf("general", "child_name", "Anak")
    STATE.child_age     = args.child_age  if args.child_age is not None else get_int("general", "child_age", 0)
    
    port                = args.port       if args.port is not None else get_int("general", "launcher_port", 5556)
    
    # Time limits config
    STATE.total_minutes = args.total_minutes if args.total_minutes is not None else get_int("time_limits", "weekday_limit_minutes", 90)
    STATE.used_seconds  = args.used_minutes * 60
    
    STATE.lb_url        = args.lb_url     or get_conf("little_brother", "server_url", "http://localhost:5555")
    STATE.demo_mode     = args.demo or not HAS_REQUESTS

    # Load PIN Hash (Priority: Config > Default Hash of "1234")
    STATE.admin_pin_hash = get_conf("general", "admin_pin_hash", STATE.admin_pin_hash)

    # Set language from config
    lang = get_conf("general", "language", "id")
    set_lang(lang)
    logger.info(f"Language set to: {lang}")

    # Background Update Check (non-blocking)
    if HAS_UPDATER:
        def _bg_update_check():
            res = check_update()
            if res.get("update_available"):
                logger.info(f"[UPDATE] {res['message']}")
        threading.Thread(target=_bg_update_check, daemon=True).start()


    # Init launcher
    if HAS_LAUNCHER and CATALOG_PATH.exists():
        global LAUNCHER
        LAUNCHER = AppsLauncher(CATALOG_PATH, child_age=STATE.child_age)
        logger.info(f"AppsLauncher: {LAUNCHER}")
    else:
        logger.warning("AppsLauncher not available — using catalog fallback")

    # ASCII-safe banner (avoids UnicodeEncodeError on Windows console)
    sep = "=" * 55
    def _p(msg=""):
        try: print(msg)
        except UnicodeEncodeError: print(msg.encode("ascii", "replace").decode())

    _p("\n" + sep)
    _p("  [*] SafeKid Flash Launcher Server v2")
    _p(sep)
    _p(f"  [>] Child          : {STATE.child_name} (usia {STATE.child_age})")
    _p(f"  [>] Time Today     : {STATE.used_minutes}/{STATE.total_minutes} menit")
    _p(f"  [>] Little Brother : {STATE.lb_url}")
    _p(f"  [>] Demo Mode      : {STATE.demo_mode}")
    _p(f"  [>] Admin PIN Hash : {STATE.admin_pin_hash[:12]}...  (use --setup to change)")
    _p(f"  [>] Apps Catalog   : {CATALOG_PATH.exists()}")
    _p(sep)
    _p(f"\n  [URL] Kid UI  -> http://localhost:{port}/")
    _p(f"  [URL] Parent  -> http://localhost:{port}/parent")
    _p(f"  [URL] API     -> http://localhost:{port}/api/status")
    _p(sep + "\n")

    # Background threads
    if STATE.demo_mode:
        threading.Thread(target=demo_ticker, daemon=True).start()
        logger.info("Demo ticker started")
    else:
        threading.Thread(target=lb_poller, daemon=True).start()
        logger.info("Little Brother poller started")

    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    import argparse
    main()
