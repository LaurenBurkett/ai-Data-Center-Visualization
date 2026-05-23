#!/usr/bin/env python3
"""Generate AI Frontier Data Centers dashboard (index.html)."""
import csv, json, re, math
from collections import defaultdict
from datetime import datetime

DATA_DIR = "data"

CITY_COORDS = {
    ("Abilene", "TX"):        (32.4487, -99.7331),
    ("Afton", "TX"):          (33.1701, -101.0541),
    ("Barker", "NY"):         (43.3292, -78.5417),
    ("Claude", "TX"):         (34.8834, -101.3648),
    ("Columbus", "OH"):       (39.9612, -82.9988),
    ("Council Bluffs", "IA"): (41.2619, -95.8608),
    ("Cumming", "IA"):        (41.4709, -93.7636),
    ("Denton", "TX"):         (33.2148, -97.1331),
    ("Fairfax", "IA"):        (41.9247, -91.7808),
    ("Fayetteville", "GA"):   (33.4418, -84.4549),
    ("Fort Wayne", "IN"):     (41.0793, -85.1394),
    ("Goodyear", "AZ"):       (33.4353, -112.3576),
    ("Manassas", "VA"):       (38.7509, -77.4753),
    ("Memphis", "TN"):        (35.1495, -90.0490),
    ("Midlothian", "TX"):     (32.4818, -97.0058),
    ("Mount Pleasant", "WI"): (42.7197, -87.8784),
    ("New Albany", "OH"):     (40.0814, -82.7960),
    ("New Carlisle", "IN"):   (41.7056, -86.5014),
    ("Omaha", "NE"):          (41.2565, -95.9345),
    ("Pryor", "OK"):          (36.3042, -95.3169),
    ("Red Oak", "TX"):        (32.5165, -96.8047),
    ("San Antonio", "TX"):    (29.4241, -98.4936),
    ("Sandston", "VA"):       (37.5243, -77.3191),
    ("Temple", "TX"):         (31.0982, -97.3428),
    ("Warren", "OH"):         (41.2373, -80.8184),
}

STATE_CENTROIDS = {
    "AL": (32.806671, -86.791130), "AK": (61.370716, -152.404419),
    "AZ": (33.729759, -111.431221), "AR": (34.969704, -92.373123),
    "CA": (36.116203, -119.681564), "CO": (39.059811, -105.311104),
    "CT": (41.597782, -72.755371), "DE": (39.318523, -75.507141),
    "FL": (27.766279, -81.686783), "GA": (33.040619, -83.643074),
    "HI": (21.094318, -157.498337), "ID": (44.240459, -114.478828),
    "IL": (40.349457, -88.986137), "IN": (39.849426, -86.258278),
    "IA": (42.011539, -93.210526), "KS": (38.526600, -96.726486),
    "KY": (37.668140, -84.670067), "LA": (31.169960, -91.867805),
    "ME": (44.693947, -69.381927), "MD": (39.063946, -76.802101),
    "MA": (42.230171, -71.530106), "MI": (43.326618, -84.536095),
    "MN": (45.694454, -93.900192), "MS": (32.741646, -89.678696),
    "MO": (38.456085, -92.288368), "MT": (46.921925, -110.454353),
    "NE": (41.125370, -98.268082), "NV": (38.313515, -117.055374),
    "NH": (43.452492, -71.563896), "NJ": (40.298904, -74.521011),
    "NM": (34.840515, -106.248482), "NY": (42.165726, -74.948051),
    "NC": (35.630066, -79.806419), "ND": (47.528912, -99.784012),
    "OH": (40.388783, -82.764915), "OK": (35.565342, -96.928917),
    "OR": (44.572021, -122.070938), "PA": (40.590752, -77.209755),
    "RI": (41.680893, -71.511780), "SC": (33.856892, -80.945007),
    "SD": (44.299782, -99.438828), "TN": (35.747845, -86.692345),
    "TX": (31.054487, -97.563461), "UT": (40.150032, -111.862434),
    "VT": (44.045876, -72.710686), "VA": (37.769337, -78.169968),
    "WA": (47.400902, -121.490494), "WV": (38.491226, -80.954453),
    "WI": (44.268543, -89.616508), "WY": (42.755966, -107.302490),
}

OWNER_COLORS = {
    "Google":    "#4285f4",
    "Microsoft": "#00a4ef",
    "Meta":      "#1877f2",
    "Amazon":    "#ff9900",
    "Oracle":    "#f05a22",
    "xAI":       "#c0c0c0",
    "SpaceXAI":  "#c0c0c0",
    "OpenAI":    "#10a37f",
    "CoreWeave": "#7c3aed",
    "Coreweave": "#7c3aed",
    "SoftBank":  "#cc0033",
    "Softbank":  "#cc0033",
    "G42":       "#e67e22",
    "Fluidstack":"#06b6d4",
    "Nscale":    "#84cc16",
    "Alibaba":   "#ff6600",
    "Crusoe":    "#ec4899",
}
DEFAULT_COLOR = "#94a3b8"

def get_owner_clean(raw):
    return raw.split("#")[0].strip()

def get_owner_color(owner):
    for k, v in OWNER_COLORS.items():
        if k.lower() in owner.lower():
            return v
    return DEFAULT_COLOR

def get_coords(row):
    addr = row["Address"].strip()
    country = row["Country"].strip()
    intl = {
        "China":                (41.1000,  114.7000),
        "United Arab Emirates": (23.4241,   53.8478),
        "Portugal":             (38.7169,   -9.1399),
        "Malaysia":             ( 3.1390,  101.6869),
        "Indonesia":            (-6.2088,  106.8456),
    }
    if country in intl:
        return intl[country]
    # city/state from "..., City, ST NNNNN"
    m = re.search(r",\s*([^,]+),\s*([A-Z]{2})\s+\d", addr)
    if m:
        city, state = m.group(1).strip(), m.group(2).strip()
        if (city, state) in CITY_COORDS:
            return CITY_COORDS[(city, state)]
        return STATE_CENTROIDS.get(state, (39.5, -98.35))
    # special patterns
    specials = [
        ("Papillion",    (41.0197, -96.0447)),
        ("Gold Coast",   (41.0197, -96.0447)),
        ("Ridgeland",    (32.4085, -90.1323)),
        ("Litchfield",   (33.4200, -112.3200)),
        ("The Dalles",   (45.5946, -121.1787)),
        ("Cedar Rapids", (41.9779, -91.6656)),
        ("CEDAR RAPIDS", (41.9779, -91.6656)),
        ("Kuna",         (43.4921, -116.4202)),
        ("Madison",      (32.6100,  -90.0400)),
        ("Holly Ridge",  (32.6000,  -91.8700)),
        ("Goodyear",     (33.4353, -112.3576)),
        ("Arizona",      (33.4353, -112.3576)),
    ]
    for kw, coords in specials:
        if kw in addr:
            return coords
    return (39.5, -98.35)

def load_csv(name):
    with open(f"{DATA_DIR}/{name}") as f:
        return list(csv.DictReader(f))

dc_rows       = load_csv("data_centers.csv")
timeline_rows = load_csv("data_center_timelines.csv")

# ── Map data ───────────────────────────────────────────────────────────────────
map_data = []
for r in dc_rows:
    lat, lng = get_coords(r)
    owner = get_owner_clean(r["Owner"])
    def flt(v): return float(v) if v.strip() else 0.0
    map_data.append({
        "name":    r["Name"],
        "owner":   owner,
        "country": r["Country"].strip(),
        "lat":     lat,
        "lng":     lng,
        "power":   flt(r["Current power (MW)"]),
        "h100":    flt(r["Current H100 equivalents"]),
        "cost":    flt(r["Current total capital cost (2025 USD billions)"]),
        "color":   get_owner_color(owner),
        "address": r["Address"].strip(),
    })

# ── Timeline aggregation ───────────────────────────────────────────────────────
dc_events = defaultdict(list)
for r in timeline_rows:
    if not r["Date"].strip() or not r["Data center"].strip():
        continue
    try:
        date = datetime.strptime(r["Date"].strip(), "%Y-%m-%d")
    except ValueError:
        continue
    dc_events[r["Data center"].strip()].append((
        date,
        float(r["H100 equivalents"]) if r["H100 equivalents"].strip() else 0.0,
        float(r["Power (MW)"])       if r["Power (MW)"].strip()        else 0.0,
    ))
for dc in dc_events:
    dc_events[dc].sort()

def val_at(events, target):
    v = 0.0
    for date, h100, _ in events:
        if date <= target:
            v = h100
        else:
            break
    return v

# monthly samples 2020-01 to 2027-06
samples = []
y, mo = 2020, 1
while (y, mo) <= (2027, 6):
    samples.append(datetime(y, mo, 1))
    mo += 1
    if mo > 12:
        mo, y = 1, y + 1

today = datetime(2026, 5, 23)
cutoff_idx = next((i for i, d in enumerate(samples) if d > today), len(samples))
tl_labels  = [d.strftime("%Y-%m") for d in samples]
tl_h100    = [round(sum(val_at(ev, d) for ev in dc_events.values())) for d in samples]

# ── Owner comparison ───────────────────────────────────────────────────────────
owner_agg = defaultdict(lambda: dict(h100=0.0, power=0.0, cost=0.0, count=0))
for item in map_data:
    o = item["owner"] or "Unknown"
    if not o:
            o = "Unknown"
    owner_agg[o]["h100"]  += item["h100"]
    owner_agg[o]["power"] += item["power"]
    owner_agg[o]["cost"]  += item["cost"]
    owner_agg[o]["count"] += 1

top_owners = sorted(owner_agg.items(), key=lambda x: -x[1]["h100"])[:12]
ow_labels = [o[0] for o in top_owners]
ow_h100   = [round(o[1]["h100"])  for o in top_owners]
ow_power  = [round(o[1]["power"]) for o in top_owners]
ow_cost   = [round(o[1]["cost"],1)for o in top_owners]
ow_colors = [get_owner_color(o[0]) for o in top_owners]

# ── Summary stats ──────────────────────────────────────────────────────────────
total_h100  = sum(d["h100"]  for d in map_data)
total_power = sum(d["power"] for d in map_data)
total_cost  = sum(d["cost"]  for d in map_data)
total_count = len(map_data)

def fmt_h100(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.0f}K"
    return str(int(n))

JS_DATA = json.dumps({
    "mapData":       map_data,
    "tlLabels":      tl_labels,
    "tlH100":        tl_h100,
    "tlCutoff":      cutoff_idx,
    "owLabels":      ow_labels,
    "owH100":        ow_h100,
    "owPower":       ow_power,
    "owCost":        ow_cost,
    "owColors":      ow_colors,
    "totalH100":     total_h100,
    "totalPower":    total_power,
    "totalCost":     total_cost,
    "totalCount":    total_count,
}, separators=(",", ":"))

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Frontier Data Centers</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --bg:      #0d1117;
    --surface: #161b22;
    --border:  #30363d;
    --text:    #e6edf3;
    --muted:   #8b949e;
    --accent:  #58a6ff;
  }}
  body {{ background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; min-height: 100vh; }}
  header {{ padding: 2rem 2rem 1rem; border-bottom: 1px solid var(--border); }}
  header h1 {{ font-size: 1.6rem; font-weight: 700; color: var(--text); }}
  header p  {{ color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; padding: 1.25rem 2rem; }}
  .stat-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.25rem; }}
  .stat-card .label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}
  .stat-card .value {{ font-size: 1.75rem; font-weight: 700; color: var(--accent); margin-top: 0.25rem; }}
  .stat-card .sub   {{ font-size: 0.75rem; color: var(--muted); margin-top: 0.15rem; }}
  section {{ padding: 0 2rem 1.5rem; }}
  section h2 {{ font-size: 0.85rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.75rem; }}
  .panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
  #map {{ height: 520px; width: 100%; }}
  .charts-row {{ display: grid; grid-template-columns: 1.6fr 1fr; gap: 1.5rem; }}
  .chart-wrap {{ padding: 1.25rem; }}
  .chart-wrap canvas {{ max-height: 320px; }}
  .table-wrap {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
  thead th {{ background: var(--bg); color: var(--muted); text-align: left; padding: 0.6rem 0.9rem; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border); cursor: pointer; user-select: none; white-space: nowrap; }}
  thead th:hover {{ color: var(--accent); }}
  tbody tr {{ border-bottom: 1px solid var(--border); transition: background 0.1s; }}
  tbody tr:hover {{ background: rgba(88,166,255,0.05); }}
  tbody td {{ padding: 0.55rem 0.9rem; color: var(--text); vertical-align: middle; }}
  .owner-dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }}
  .filter-bar {{ padding: 0.75rem 0.9rem; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.75rem; }}
  .filter-bar input {{ background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 0.4rem 0.7rem; color: var(--text); font-size: 0.82rem; width: 220px; outline: none; }}
  .filter-bar input:focus {{ border-color: var(--accent); }}
  .filter-bar span {{ color: var(--muted); font-size: 0.8rem; }}
  .leaflet-popup-content-wrapper {{ background: #1c2128; border: 1px solid var(--border); color: var(--text); border-radius: 8px; }}
  .leaflet-popup-tip {{ background: #1c2128; }}
  .popup-name {{ font-weight: 600; font-size: 0.9rem; margin-bottom: 0.35rem; }}
  .popup-row {{ font-size: 0.78rem; color: var(--muted); margin: 0.15rem 0; }}
  .popup-row span {{ color: var(--text); }}
  footer {{ padding: 1.5rem 2rem; color: var(--muted); font-size: 0.75rem; border-top: 1px solid var(--border); }}
  footer a {{ color: var(--accent); text-decoration: none; }}
  @media (max-width: 900px) {{
    .stats {{ grid-template-columns: repeat(2, 1fr); }}
    .charts-row {{ grid-template-columns: 1fr; }}
  }}
  @media (max-width: 600px) {{
    .stats {{ grid-template-columns: 1fr 1fr; }}
    header, section {{ padding-left: 1rem; padding-right: 1rem; }}
    .stats {{ padding: 1rem; }}
  }}
</style>
</head>
<body>
<header>
  <h1>AI Frontier Data Centers</h1>
  <p>Epoch AI dataset — frontier AI compute facilities worldwide</p>
</header>

<div class="stats">
  <div class="stat-card">
    <div class="label">Total Facilities</div>
    <div class="value" id="s-count">—</div>
    <div class="sub">data centers tracked</div>
  </div>
  <div class="stat-card">
    <div class="label">Total Compute</div>
    <div class="value" id="s-h100">—</div>
    <div class="sub">H100 GPU equivalents</div>
  </div>
  <div class="stat-card">
    <div class="label">Total Power</div>
    <div class="value" id="s-power">—</div>
    <div class="sub">megawatts deployed</div>
  </div>
  <div class="stat-card">
    <div class="label">Capital Invested</div>
    <div class="value" id="s-cost">—</div>
    <div class="sub">2025 USD billions</div>
  </div>
</div>

<section>
  <h2>Geographic Distribution</h2>
  <div class="panel">
    <div id="map"></div>
  </div>
</section>

<section>
  <div class="charts-row">
    <div>
      <h2>Compute Growth Over Time</h2>
      <div class="panel">
        <div class="chart-wrap">
          <canvas id="timeline-chart"></canvas>
        </div>
      </div>
    </div>
    <div>
      <h2>Compute by Owner</h2>
      <div class="panel">
        <div class="chart-wrap">
          <canvas id="owners-chart"></canvas>
        </div>
      </div>
    </div>
  </div>
</section>

<section>
  <h2>All Facilities</h2>
  <div class="panel">
    <div class="filter-bar">
      <input id="search" type="text" placeholder="Filter by name, owner, or country…">
      <span id="row-count"></span>
    </div>
    <div class="table-wrap">
      <table id="dc-table">
        <thead>
          <tr>
            <th data-col="name">Name ↕</th>
            <th data-col="owner">Owner ↕</th>
            <th data-col="country">Country ↕</th>
            <th data-col="power" style="text-align:right">Power (MW) ↕</th>
            <th data-col="h100"  style="text-align:right">H100 Equiv ↕</th>
            <th data-col="cost"  style="text-align:right">Cost ($B) ↕</th>
          </tr>
        </thead>
        <tbody id="dc-body"></tbody>
      </table>
    </div>
  </div>
</section>

<footer>
  Data: <a href="https://epoch.ai/data/data-centers" target="_blank">Epoch AI — Frontier Data Centers</a> &nbsp;·&nbsp;
  Licensed under <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank">CC BY 4.0</a> &nbsp;·&nbsp;
  Last updated May 2026
</footer>

<script>
const D = {JS_DATA};

// ── Stats ──────────────────────────────────────────────────────────────────────
function fmtH100(n) {{
  if (n >= 1e6) return (n/1e6).toFixed(1) + 'M';
  if (n >= 1e3) return Math.round(n/1e3) + 'K';
  return Math.round(n).toString();
}}
document.getElementById('s-count').textContent = D.totalCount;
document.getElementById('s-h100').textContent  = fmtH100(D.totalH100);
document.getElementById('s-power').textContent = Math.round(D.totalPower).toLocaleString() + ' MW';
document.getElementById('s-cost').textContent  = '$' + D.totalCost.toFixed(0) + 'B';

// ── Map ────────────────────────────────────────────────────────────────────────
const map = L.map('map', {{ zoomControl: true }}).setView([38, -96], 4);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
  subdomains: 'abcd', maxZoom: 19,
}}).addTo(map);

const minR = 5, maxR = 40;
const powers = D.mapData.map(d => d.power).filter(p => p > 0);
const pMax = Math.max(...powers);

D.mapData.forEach(d => {{
  if (!d.lat || !d.lng) return;
  const r = d.power > 0 ? minR + (maxR - minR) * Math.sqrt(d.power / pMax) : minR;
  const circle = L.circleMarker([d.lat, d.lng], {{
    radius: r, color: d.color, fillColor: d.color,
    fillOpacity: 0.6, weight: 1.5,
  }}).addTo(map);
  circle.bindPopup(`
    <div class="popup-name">${{d.name}}</div>
    <div class="popup-row">Owner &nbsp;<span>${{d.owner || '—'}}</span></div>
    <div class="popup-row">Country &nbsp;<span>${{d.country}}</span></div>
    <div class="popup-row">Power &nbsp;<span>${{d.power.toLocaleString()}} MW</span></div>
    <div class="popup-row">H100 equiv &nbsp;<span>${{fmtH100(d.h100)}}</span></div>
    <div class="popup-row">Capital cost &nbsp;<span>$${{d.cost.toFixed(1)}}B</span></div>
    <div class="popup-row" style="margin-top:0.35rem;font-size:0.72rem">${{d.address}}</div>
  `);
}});

// ── Timeline chart ─────────────────────────────────────────────────────────────
const tlCtx = document.getElementById('timeline-chart').getContext('2d');
const cutoff = D.tlCutoff;
const actualH100    = D.tlH100.slice(0, cutoff + 1).concat(D.tlH100.slice(cutoff + 1).map(() => null));
const projectedH100 = D.tlH100.slice(0, cutoff).map(() => null).concat(D.tlH100.slice(cutoff));

new Chart(tlCtx, {{
  type: 'line',
  data: {{
    labels: D.tlLabels,
    datasets: [
      {{
        label: 'Actual compute (H100 eq)',
        data: actualH100,
        borderColor: '#58a6ff',
        backgroundColor: 'rgba(88,166,255,0.08)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
        spanGaps: false,
      }},
      {{
        label: 'Projected',
        data: projectedH100,
        borderColor: '#58a6ff',
        backgroundColor: 'rgba(88,166,255,0.03)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
        borderDash: [6, 4],
        spanGaps: false,
      }},
    ],
  }},
  options: {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ labels: {{ color: '#8b949e', font: {{ size: 11 }} }} }},
      tooltip: {{
        backgroundColor: '#1c2128',
        borderColor: '#30363d',
        borderWidth: 1,
        titleColor: '#e6edf3',
        bodyColor: '#8b949e',
        callbacks: {{
          label: ctx => ' ' + fmtH100(ctx.parsed.y) + ' H100 eq',
        }},
      }},
    }},
    scales: {{
      x: {{
        ticks: {{ color: '#8b949e', maxRotation: 45, font: {{ size: 10 }}, maxTicksLimit: 16 }},
        grid:  {{ color: 'rgba(48,54,61,0.6)' }},
      }},
      y: {{
        ticks: {{ color: '#8b949e', font: {{ size: 10 }}, callback: v => fmtH100(v) }},
        grid:  {{ color: 'rgba(48,54,61,0.6)' }},
      }},
    }},
  }},
}});

// ── Owners chart ───────────────────────────────────────────────────────────────
const owCtx = document.getElementById('owners-chart').getContext('2d');
new Chart(owCtx, {{
  type: 'bar',
  data: {{
    labels: D.owLabels,
    datasets: [{{
      label: 'H100 equivalents',
      data: D.owH100,
      backgroundColor: D.owColors.map(c => c + 'cc'),
      borderColor: D.owColors,
      borderWidth: 1,
      borderRadius: 4,
    }}],
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        backgroundColor: '#1c2128',
        borderColor: '#30363d',
        borderWidth: 1,
        titleColor: '#e6edf3',
        bodyColor: '#8b949e',
        callbacks: {{
          label: ctx => ' ' + fmtH100(ctx.parsed.x) + ' H100 eq',
        }},
      }},
    }},
    scales: {{
      x: {{
        ticks: {{ color: '#8b949e', font: {{ size: 10 }}, callback: v => fmtH100(v) }},
        grid:  {{ color: 'rgba(48,54,61,0.6)' }},
      }},
      y: {{
        ticks: {{ color: '#e6edf3', font: {{ size: 11 }} }},
        grid:  {{ display: false }},
      }},
    }},
  }},
}});

// ── Data table ─────────────────────────────────────────────────────────────────
let tableData = [...D.mapData];
let sortCol = 'h100', sortDir = -1;

function numFmt(n, decimals = 0) {{
  if (!n) return '—';
  return decimals > 0 ? n.toFixed(decimals) : n.toLocaleString();
}}

function renderTable(rows) {{
  const tbody = document.getElementById('dc-body');
  tbody.innerHTML = rows.map(d => `
    <tr>
      <td>${{d.name}}</td>
      <td><span class="owner-dot" style="background:${{d.color}}"></span>${{d.owner || '—'}}</td>
      <td>${{d.country}}</td>
      <td style="text-align:right">${{numFmt(d.power)}}</td>
      <td style="text-align:right">${{fmtH100(d.h100)}}</td>
      <td style="text-align:right">${{d.cost ? '$' + d.cost.toFixed(1) + 'B' : '—'}}</td>
    </tr>
  `).join('');
  document.getElementById('row-count').textContent = rows.length + ' facilities';
}}

function applySort() {{
  tableData.sort((a, b) => {{
    const av = a[sortCol] ?? '', bv = b[sortCol] ?? '';
    if (typeof av === 'number') return sortDir * (av - bv);
    return sortDir * av.toString().localeCompare(bv.toString());
  }});
}}

function refresh() {{
  const q = document.getElementById('search').value.trim().toLowerCase();
  let rows = q
    ? tableData.filter(d =>
        d.name.toLowerCase().includes(q) ||
        (d.owner || '').toLowerCase().includes(q) ||
        d.country.toLowerCase().includes(q)
      )
    : tableData;
  renderTable(rows);
}}

document.querySelectorAll('thead th[data-col]').forEach(th => {{
  th.addEventListener('click', () => {{
    const col = th.dataset.col;
    sortDir = (col === sortCol) ? -sortDir : -1;
    sortCol = col;
    applySort();
    refresh();
  }});
}});

document.getElementById('search').addEventListener('input', refresh);

applySort();
refresh();
</script>
</body>
</html>
"""

# Inject JS data
HTML = HTML.replace("{JS_DATA}", JS_DATA)

with open("index.html", "w") as f:
    f.write(HTML)

print(f"Generated index.html  ({len(HTML):,} bytes)")
print(f"  {total_count} facilities  |  {fmt_h100(total_h100)} H100 eq  |  {total_power:.0f} MW  |  ${total_cost:.0f}B")
