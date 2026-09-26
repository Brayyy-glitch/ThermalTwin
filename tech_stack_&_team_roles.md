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

### Collaboration & deployment
- **GitHub** (free) — shared repo instead of passing files by hand
- **Streamlit Community Cloud** (free) — optional one-click hosting for a live demo link

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