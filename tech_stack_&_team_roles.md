# ThermalTwin (MineFlow AI) — Team Roles & Tech Stack

## Team roles (4 people)

| Role | Owns | Does |
|---|---|---|
| **Data & Simulation** | `simulator.py`, `privacy.py` | Realistic telemetry generation, tamper-injection scenarios, worker-tag hashing |
| **Analytics & Security** | `anomaly.py` | Rolling Z-score, drift/jump classification, worker-risk ranking, cross-sensor validation if time allows |
| **Dashboard & Integration** | `app.py` | Wires everything together, UI/UX, Surface Matchmaker, ICP staging banner |
| **Narrative & Compliance** | `config.py`, slides, rebuttal prep, submission | Keeps deck and code in sync, owns Lean Canvas/SSDLC/Data Privacy slide, mentor liaison, final submission |

`config.py` is deliberately the safest file for the Narrative & Compliance role to edit directly —
it's just data (mine lists, depth bands, the wet-bulb constant), so last-minute wording changes
never risk breaking the app. Everyone else's slides and claims should be checked against it, not
restated from memory, so the deck and the code can't drift apart the way the Mponeng depth issue
did earlier.

## Tech stack — no paid API keys required

### Core (already in use)
- Python 3, `pandas`, `numpy` — data processing
- `streamlit` — the dashboard itself (`st.line_chart` covers the charts; no separate charting
  library needed)

### Surface Engine map (if you want an actual map, not just the revenue calculator)
- `folium` + `geopandas` — free; Folium's default tiles come from OpenStreetMap, no API key needed
  at hackathon scale
- `Nominatim` (OpenStreetMap's free geocoding service) — converts mine/partner names into map
  coordinates automatically

### Real telemetry ingestion (stretch goal, only with spare hours)
- `pymodbus` — simulated Modbus/TCP PLC
- `paho-mqtt` + a local `Mosquitto` broker — the MQTT layer
- `Zeek` — sniffs the simulated traffic for a real protocol log, adds network-monitoring credibility

### Containerization & CI (free, no registry account needed)
- **Docker** — `Dockerfile` + `.dockerignore` at repo root. Builds a `python:3.11-slim` image,
  installs `requirements.txt`, runs `streamlit run app.py`. Identical behavior on Ubuntu, macOS, and
  Windows hosts, since the container always runs Linux underneath regardless of the host OS —
  eliminates "works on my machine" during demo prep.
- **Docker Compose** (`docker-compose.yml`) — collapses `docker build` + `docker run -p -v` into
  one command (`docker compose up --build`); mounts the repo into the container so local `.py` edits
  show up without a rebuild.
- **GitHub Actions** (`.github/workflows/docker-build.yml`, free on public/most private repos) —
  on every push: builds the image, boots it, polls Streamlit's `/_stcore/health` endpoint as a smoke
  test, then tears the container down. Runs on GitHub's hosted `ubuntu-latest` runner — that's just
  where the CI job itself executes, unrelated to what OS any of us develops on locally. Does not yet
  push the image to a registry (Docker Hub / GHCR); that's a stretch add if we want it.

### Collaboration & deployment
- **GitHub** (free) — shared repo instead of passing files by hand
- **Streamlit Community Cloud** (free) — optional one-click hosting for a live demo link; builds
  from `requirements.txt` directly and does not use the Dockerfile

Zero external dependencies require billing setup, a paid tier, or a rate-limited API key under
demo pressure — worth stating explicitly on the Technical Architecture slide as a feasibility
strength.

## Current repo files
- `simulator.py` — telemetry generator, tamper injection
- `anomaly.py` — rolling Z-score, signature classification (DRIFT/JUMP), worker-risk ranking
- `privacy.py` — SHA-256 worker ID hashing, zone occupancy density
- `config.py` — Phase 1/Phase 2 ICP staging, wet-bulb safety constant
- `app.py` — Streamlit dashboard tying it all together
- `requirements.txt` — `streamlit`, `pandas`, `numpy`
- `Dockerfile`, `.dockerignore`, `docker-compose.yml` — containerized run, cross-OS
- `.github/workflows/docker-build.yml` — CI: build + smoke-test the container on every push