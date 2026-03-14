"""Flask-based MuJoCo trajectory visualizer.

Replays recorded MPPI trajectories through MuJoCo renderer, serving
individual frames via REST API. The browser drives playback with
requestAnimationFrame for smooth, robust rendering.

Usage:
    python visualizer.py [rollout_data.npz]
    # Then open http://127.0.0.1:5000
"""

import json
from pathlib import Path

import flask
import mujoco
import numpy as np
from PIL import Image
import io

_GO2_SCENE = (
    Path(__file__).parent / "assets" / "mujoco_menagerie"
    / "unitree_go2" / "scene.xml"
)


_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Optimal Cycle MPPI — Go2</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#1a1a2e;color:#e0e0e0;display:flex;flex-direction:column;height:100vh}
header{background:#16213e;padding:10px 20px;border-bottom:2px solid #0f3460;display:flex;align-items:center;gap:20px}
header h1{font-size:17px;font-weight:600;color:#e94560}
header .info{font-size:12px;color:#888}
.main{display:flex;flex:1;overflow:hidden}
.viewer{flex:2;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px;position:relative}
.viewer canvas{max-width:100%;max-height:100%;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,0.4)}
.bar{position:absolute;bottom:20px;display:flex;gap:10px;align-items:center;background:rgba(22,33,62,0.92);padding:8px 16px;border-radius:20px;font-size:13px}
.bar button{background:#0f3460;color:#e0e0e0;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px}
.bar button:hover{background:#e94560}
.bar button.active{background:#e94560}
.bar select,.bar input[type=range]{background:#0f3460;color:#e0e0e0;border:1px solid #333;padding:4px 8px;border-radius:6px;font-size:12px}
.bar label{display:flex;align-items:center;gap:6px;font-size:12px;color:#888}
.progress{position:absolute;bottom:65px;left:50%;transform:translateX(-50%);width:60%;height:4px;background:#0f3460;border-radius:2px;cursor:pointer}
.progress .fill{height:100%;background:#e94560;border-radius:2px;transition:width 0.05s}
.sb{flex:1;background:#16213e;border-left:2px solid #0f3460;padding:14px;overflow-y:auto;min-width:300px;max-width:380px}
.sb h2{font-size:13px;color:#e94560;margin:14px 0 6px;text-transform:uppercase;letter-spacing:1px}
.sb h2:first-child{margin-top:0}
.m{display:flex;justify-content:space-between;padding:3px 0;font-size:12px;border-bottom:1px solid rgba(255,255,255,0.04)}
.m .l{color:#888}.m .v{font-family:'SF Mono',monospace;color:#4ecca3}
canvas.ch{width:100%;height:110px;margin:6px 0;background:rgba(0,0,0,0.2);border-radius:6px}
.tbl{max-height:280px;overflow-y:auto;font-size:11px}
.tbl table{width:100%;border-collapse:collapse}
.tbl th{color:#888;text-align:left;padding:2px 4px;position:sticky;top:0;background:#16213e}
.tbl td{padding:2px 4px;border-bottom:1px solid #222}
.tbl tr{cursor:pointer}.tbl tr:hover{background:rgba(233,69,96,0.15)}
.tbl tr.sel{background:rgba(233,69,96,0.25)}
</style>
</head>
<body>
<header>
  <h1>Optimal Cycle MPPI</h1>
  <span class="info" id="info">Loading...</span>
</header>
<div class="main">
  <div class="viewer">
    <canvas id="cv" width="1280" height="720"></canvas>
    <div class="progress" id="prog" onclick="seekFrame(event)">
      <div class="fill" id="progfill" style="width:0%"></div>
    </div>
    <div class="bar">
      <button id="btnPlay" onclick="togglePlay()">▶</button>
      <select id="iterSel" onchange="switchIter(+this.value)"></select>
      <label>Speed
        <input type="range" id="spd" min="0.2" max="4.0" step="0.2" value="1.0" oninput="speed=+this.value;document.getElementById('spdV').textContent=this.value+'x'">
        <span id="spdV">1.0x</span>
      </label>
      <button id="btnLoop" class="active" onclick="looping=!looping;this.classList.toggle('active')">Loop</button>
      <span id="finfo" style="color:#888;font-size:11px;min-width:80px"></span>
    </div>
  </div>
  <div class="sb" id="sb"><h2>Loading...</h2></div>
</div>
<script>
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
let frames = [];
let nFrames = 0;
let fi = 0;
let playing = true;
let looping = true;
let speed = 1.0;
let currentIter = -1;
let nIters = 0;
let diag = null;
let lastT = 0;
const FPS_BASE = 25;

async function loadIter(iter) {
  currentIter = iter;
  const resp = await fetch('/traj_info?iter=' + iter);
  const info = await resp.json();
  nFrames = info.n_frames;
  frames = new Array(nFrames).fill(null);
  fi = 0;
  // Load ALL frames, wait for each
  const promises = [];
  for (let j = 0; j < nFrames; j++) {
    promises.push(loadFrame(iter, j, j));
  }
  await Promise.all(promises);
  document.getElementById('finfo').textContent = nFrames + ' frames loaded';
  console.log('Loaded ' + frames.filter(f=>f).length + '/' + nFrames + ' frames');
  draw();
}

function loadFrame(iter, idx, slot) {
  return new Promise(resolve => {
    const img = new window.Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => { frames[slot] = img; resolve(); };
    img.onerror = (e) => { console.error('frame err', idx, e); resolve(); };
    img.src = '/frame?iter=' + iter + '&f=' + idx;
  });
}

function draw() {
  const idx = Math.floor(fi) % nFrames;
  const f = frames[idx];
  if (f && f.complete && f.naturalWidth > 0) {
    ctx.drawImage(f, 0, 0, cv.width, cv.height);
  }
  document.getElementById('progfill').style.width =
    (nFrames > 1 ? (idx / (nFrames - 1) * 100) : 0) + '%';
}

function animate(ts) {
  if (!lastT) lastT = ts;
  const dt = (ts - lastT) / 1000;
  lastT = ts;
  if (playing && nFrames > 0 && frames.some(f => f)) {
    fi += dt * FPS_BASE * speed;
    if (fi >= nFrames) {
      if (looping) fi = fi % nFrames;
      else { fi = nFrames - 1; playing = false; updatePlayBtn(); }
    }
    draw();
  }
  requestAnimationFrame(animate);
}

function togglePlay() {
  playing = !playing;
  if (playing && Math.floor(fi) >= nFrames - 1) fi = 0;
  updatePlayBtn();
}
function updatePlayBtn() {
  document.getElementById('btnPlay').textContent = playing ? '⏸' : '▶';
}

function switchIter(v) {
  document.getElementById('finfo').textContent = 'loading...';
  loadIter(v);
  document.querySelectorAll('.tbl tr').forEach(r => r.classList.remove('sel'));
  const row = document.getElementById('row-' + v);
  if (row) row.classList.add('sel');
}

function seekFrame(e) {
  const rect = e.currentTarget.getBoundingClientRect();
  fi = Math.floor((e.clientX - rect.left) / rect.width * (nFrames - 1));
  draw();
}

// Load diagnostics and build sidebar
async function init() {
  const resp = await fetch('/diagnostics');
  const data = await resp.json();
  diag = data.diagnostics;
  nIters = data.n_iters;

  // Populate selector
  const sel = document.getElementById('iterSel');
  sel.innerHTML = '<option value="-1">Final</option>';
  for (let i = 0; i < nIters; i++) {
    sel.innerHTML += '<option value="'+i+'">Iter '+i+'</option>';
  }

  document.getElementById('info').textContent =
    nIters + ' iters | N=' + data.N_samples +
    ' | φ*=[' + data.best_phi.map(x=>x.toFixed(3)).join(', ') + ']';

  // Sidebar
  const sb = document.getElementById('sb');
  const L = nIters - 1;
  let h = '<h2>Final State</h2>';
  h += m('Best cost', diag.cost_best[L].toFixed(2));
  h += m('Holonomy H', diag.holonomy[L].toFixed(4));
  h += m('Entropy S', diag.entropy[L].toFixed(2));
  h += m('Temperature ε', diag.epsilon[L].toFixed(4));
  h += m('ESS', diag.ess[L].toFixed(1));
  h += m('Best φ', '['+data.best_phi.map(x=>x.toFixed(3)).join(', ')+']');
  h += m('Mean μ', '['+diag.mu[L].map(x=>x.toFixed(3)).join(', ')+']');

  h += '<h2>Convergence</h2>';
  h += '<canvas class="ch" id="c1"></canvas>';
  h += '<canvas class="ch" id="c2"></canvas>';
  h += '<canvas class="ch" id="c3"></canvas>';

  h += '<h2>Iterations</h2><div class="tbl"><table>';
  h += '<tr><th>k</th><th>cost</th><th>H</th><th>ε</th><th>ESS</th></tr>';
  for (let i = 0; i < nIters; i++) {
    h += '<tr id="row-'+i+'" onclick="switchIter('+i+')">';
    h += '<td>'+i+'</td><td>'+diag.cost_best[i].toFixed(1)+'</td>';
    h += '<td>'+diag.holonomy[i].toFixed(2)+'</td>';
    h += '<td>'+diag.epsilon[i].toFixed(3)+'</td>';
    h += '<td>'+diag.ess[i].toFixed(0)+'</td></tr>';
  }
  h += '</table></div>';
  sb.innerHTML = h;

  setTimeout(() => {
    chart('c1', diag.cost_best, '#e94560', 'Best Cost');
    chart('c2', diag.holonomy, '#4ecca3', 'Holonomy H');
    chart('c3', diag.epsilon, '#e9c46a', 'Temperature ε');
  }, 50);

  // Load final iteration frames
  await loadIter(-1);
  requestAnimationFrame(animate);
}

function m(l,v){return '<div class="m"><span class="l">'+l+'</span><span class="v">'+v+'</span></div>'}

function chart(id, data, color, title) {
  const c = document.getElementById(id);
  if (!c) return;
  const x = c.getContext('2d');
  c.width = c.offsetWidth * 2; c.height = c.offsetHeight * 2;
  x.scale(2,2);
  const w=c.offsetWidth, h=c.offsetHeight, p=8;
  const mn=Math.min(...data), mx=Math.max(...data), rng=mx-mn||1;
  x.fillStyle='#888'; x.font='11px -apple-system,sans-serif';
  x.fillText(title+' ['+mn.toFixed(2)+' → '+data[data.length-1].toFixed(2)+']', p, 13);
  x.beginPath(); x.strokeStyle=color; x.lineWidth=1.5;
  for(let i=0;i<data.length;i++){
    const px=p+(i/(data.length-1))*(w-2*p);
    const py=h-p-((data[i]-mn)/rng)*(h-3*p);
    i===0?x.moveTo(px,py):x.lineTo(px,py);
  }
  x.stroke();
}

init();
</script>
</body>
</html>"""


def create_app(data_path: str = "rollout_data.npz") -> flask.Flask:
    app = flask.Flask(__name__)

    npz_path = Path(data_path)
    json_path = npz_path.with_suffix('.json')

    npz_data = np.load(npz_path)
    final_traj = npz_data['final_trajectory']
    all_trajs = npz_data['all_trajectories']

    with open(json_path) as f:
        meta = json.load(f)

    nq = meta['nq']
    nv = meta['nv']

    # MuJoCo renderer
    model = mujoco.MjModel.from_xml_path(str(_GO2_SCENE))
    model.vis.global_.offwidth = 1280
    model.vis.global_.offheight = 720
    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=720, width=1280)

    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
    cam.trackbodyid = 0
    cam.distance = 1.8
    cam.azimuth = 145
    cam.elevation = -20
    cam.lookat[:] = [0, 0, 0.25]

    def _render(qpos, qvel=None):
        data.qpos[:] = qpos[:nq]
        if qvel is not None:
            data.qvel[:] = qvel[:nv]
        mujoco.mj_forward(model, data)
        renderer.update_scene(data, camera=cam)
        return renderer.render()

    def _jpeg(img, quality=80):
        buf = io.BytesIO()
        Image.fromarray(img).save(buf, format='JPEG', quality=quality)
        return buf.getvalue()

    # Pre-render frame cache (iter -> list of jpeg bytes)
    _cache = {}

    def _get_traj(iter_idx):
        if iter_idx < 0 or iter_idx >= len(all_trajs):
            return final_traj
        return all_trajs[iter_idx]

    def _ensure_cached(iter_idx):
        if iter_idx in _cache:
            return
        traj = _get_traj(iter_idx)
        frames = []
        for i in range(traj.shape[0]):
            qvel = traj[i, nq:nq+nv] if traj.shape[1] > nq else None
            img = _render(traj[i, :nq], qvel)
            frames.append(_jpeg(img))
        _cache[iter_idx] = frames

    # Pre-render final iteration at startup
    import sys
    print("Pre-rendering final trajectory...", file=sys.stderr, flush=True)
    _ensure_cached(-1)
    print(f"  {len(_cache[-1])} frames cached.", file=sys.stderr, flush=True)

    @app.route('/')
    def index():
        return _HTML

    @app.route('/traj_info')
    def traj_info():
        iter_idx = flask.request.args.get('iter', -1, type=int)
        traj = _get_traj(iter_idx)
        _ensure_cached(iter_idx)
        return flask.jsonify({'n_frames': traj.shape[0], 'iter': iter_idx})

    @app.route('/frame')
    def frame():
        iter_idx = flask.request.args.get('iter', -1, type=int)
        frame_idx = flask.request.args.get('f', 0, type=int)
        _ensure_cached(iter_idx)
        frames = _cache.get(iter_idx, [])
        if not frames:
            return "no frames", 404
        frame_idx = max(0, min(frame_idx, len(frames) - 1))
        return flask.Response(frames[frame_idx], mimetype='image/jpeg')

    @app.route('/diagnostics')
    def diagnostics():
        return flask.jsonify({
            'diagnostics': meta['diagnostics'],
            'best_phi': meta['best_phi'],
            'n_iters': meta['n_iters'],
            'N_samples': meta.get('N_samples', 64),
        })

    return app


if __name__ == '__main__':
    import sys
    data_path = sys.argv[1] if len(sys.argv) > 1 else 'rollout_data.npz'
    print(f"Loading: {data_path}")
    app = create_app(data_path)
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
    print(f"http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, threaded=True)
