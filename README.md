# ThermalTwin (MineFlow AI)

**A dual-engine thermodynamic intelligence platform for ultra-deep South African gold mines** —
predicting heat-related safety incidents 25–30 minutes in advance, detecting sensor tampering via
a physics-aware security layer, and turning wasted heat into a community revenue stream.

Built for Geekulcha Annual Hackathon 2026 by Team Totally Spies.

## The problem, in one sentence

Deep-level mines fight heat reactively at huge cost, while the communities right next to them face
documented energy poverty — the same wasted heat sits on both sides of that gap.

## What it does

- **Underground Engine** — predicts localized heat spikes ahead of time so ventilation can be
  redirected proactively instead of reactively.
- **Physics-Aware Security Layer** — reuses the same predictive model as a security baseline: if a
  sensor's reported value diverges from what physics says it should be, that mismatch is flagged as
  possible tampering or hardware failure, and classified as a gradual `DRIFT` (calibration wear) or
  sudden `JUMP` (spoofing signature).
- **Surface Engine** — a fence-line heat exchanger model plus a two-sided digital front door: a
  **Commercial Door** (available heat capacity, discount rate, mandatory local-hiring quota, 1-tap
  tPPA interest) and a **Community Door** (plain-language hydroponic/aquaculture opportunity cards
  for local youth, women, and citizens living with disabilities), proving Social and Labour Plan
  (SLP) value has a visible path to the community — without altering the mine's existing water
  treatment or cooling circuit.
- **Privacy layer** — worker positioning is hashed one-way at ingestion; the platform only ever sees
  an anonymous zone occupancy count, never an identity (POPIA-aligned).

## Two-tier deployment model

Not all mines cool the same way, so the ICP (ideal customer profile) is staged accordingly:

| Phase | Depth band | Target mines | Cooling mechanism |
|---|---|---|---|
| **Phase 1 (this demo)** | 2.5 km – 3.3 km | Driefontein, South Deep, Kusasalethu, Kloof | Closed-loop chilled service water heat exchanger |
| **Phase 2 (roadmap)** | > 3.3 km – 4.0 km | Mponeng, TauTona | Melted ice-brine return flow interface |

Conventional chilled-water cooling stops being practical past ~3,300m (the water heats up too much
on the descent), so the two deepest, best-known mines actually need a different interface — hence
the split. See `config.py` for the single source of truth on this.

## Project structure

```
config.py       # ICP staging data + all detection thresholds (single source of truth)
simulator.py    # Simulated telemetry generator, tamper-injection scenarios
privacy.py      # Worker ID hashing, zone occupancy density
anomaly.py      # Rolling Z-score, DRIFT/JUMP signature classification, worker-risk ranking
app.py          # Streamlit dashboard tying everything together
requirements.txt
```

Each file is owned by a different team role — see `TEAM_AND_STACK.md` for the role split and the
full (free/open-source) tech stack, including stretch-goal options like real MQTT/Modbus ingestion.

## Running it

**Option A — local venv:**
```bash
pip install -r requirements.txt
streamlit run app.py
```

**Option B — Docker (recommended for cross-machine consistency):**
```bash
docker compose up --build
```
Then open `http://localhost:8501`. Works identically on Linux, macOS, and Windows —
the container always runs a Linux base image regardless of host OS, so there's no
"works on my machine" drift between the four of us. Editing any `.py` file locally
picks up live inside the running container (no rebuild needed); only changing
`requirements.txt` requires a `docker compose up --build` re-run. See
`TEAM_AND_STACK.md` for the full Docker/CI setup.

## Access & credentials

The dashboard uses a role-based entry screen. Two paths are available:

| Role | Entry | Credentials |
|---|---|---|
| Community member | "I am with the community" | No login required |
| Mine operator / manager | "I am with the mine" | See below |

**Demo operator credentials (hardcoded for demo — change before production):**

| Field | Value |
|---|---|
| Username | `operator` |
| Password | `thermaltwin2026` |

Credentials are checked by comparing a SHA-256 hash of the entered password against a hardcoded
hash in `app.py`. To change them, update `_OPERATOR_USERNAME` and re-hash a new password:

```python
import hashlib
print(hashlib.sha256("your_new_password".encode()).hexdigest())
```

Replace `_OPERATOR_PASSWORD_HASH` in `app.py` with the output.

**Community form URLs** are placeholders stored in the `COMMUNITY_FORM_URLS` dict near the top of
`app.py`. Replace each `https://forms.google.com/PLACEHOLDER_*` value with the live Google or
Microsoft Forms URL before going live.

## Demo script (~3 minutes)

1. **Landing** — open `http://localhost:8501`, show the two role cards.
2. **Community path** — click "I am with the community", walk through the four opportunity cards,
   show that each Apply button links to the external form (placeholder URLs until live forms are set).
3. **Operator path** — go back, click "I am with the mine", sign in with `operator` / `thermaltwin2026`.
4. **Zone status** — on the Underground Engine tab, show all zones green (stable). Pick a mine from
   the sidebar and note the numbers change per mine.
5. **Inject tamper** — open "Demo controls", toggle "Inject sensor tampering", click Refresh.
   Watch the top banner turn red/amber, the zone table update, and the recommended action appear.
6. **Human fallback** — show that the action is not taken automatically. Click the confirm button
   to demonstrate the human-in-the-loop step.
7. **Commercial Door** — adjust the heat capacity slider, show the live savings/revenue figures,
   and submit an expression of interest.
8. **Status header** — point to the "Available Thermal Output vs Allocated Community Hubs" gauge
   always visible at the top — the live proof of SLP value.

## What's simulated vs. real, stated plainly

- All telemetry is synthetic — there is no live mine data. The simulation is grounded in sourced,
  real physical parameters (chilled water at ~5°C, 60–80°C virgin rock temperatures, the 28°C
  statutory wet-bulb safety limit), not arbitrary numbers.
- The "predicted" temperature is a scripted physics-based baseline, not a trained ML model.
- Telemetry ingestion is a direct function call in this build, not a running MQTT/Modbus pipeline —
  see `TEAM_AND_STACK.md` for what that would take to make literally true.
- Cross-sensor validation (`validate_cross_sensors` in `anomaly.py`) **is implemented** — it
  compares adjacent RTD probes and flags `LOCALIZED_PROBE_ANOMALY` when a single zone diverges
  by more than `MAX_PLAUSIBLE_NEIGHBOR_DELTA_C` (3.5 °C) from its neighbours while they agree.
  It is not yet wired into the live per-zone alert pipeline in the dashboard; that is the next
  engineering task. Only per-zone rolling Z-score currently drives the live alerts.

Supporting documents (not code): `ThermalTwin_Explained_Simply.pdf` (plain-language project overview),
`ThermalTwin_Rebuttal_Prep.pdf` (anticipated judge questions and honest answers, including this
project's open items), `Technical_Feasibility_Notes_OT_ICS_Anomaly_Detection.pdf` (background research
on OT/ICS anomaly detection approaches), and `SECURITY_AND_TRUST_NOTES.md` (PASTA threat-model
mapping, security lifecycle, and the post-quantum-cryptography / "trusted 10 years from now" answers
for the SSDLC and Data Privacy slide).

A GitHub Actions workflow (`.github/workflows/docker-build.yml`) builds the Docker image and runs a
smoke test (boots the container, polls Streamlit's health endpoint) on every push — see
`TEAM_AND_STACK.md`.

## Open items

- The claim that established OT-security vendors (Dragos/Claroty/Nozomi) don't serve mid-tier SA
  mines is still unverified — this is the single highest-risk unconfirmed assumption in the pitch.
- No confirmed real-world contact or quote from a Carletonville-area mine or resident yet.
- Final funding figure for the Lean Canvas/pitch ask is not yet locked in.


---

## Dashboard term glossary

### Underground Engine

The safety monitoring screen. Watches sensor readings from underground zones and flags heat danger or sensor tampering.

| Term | What it means |
|---|---|
| **Inject sensor tampering** | A demo toggle that simulates a bad actor (or a broken sensor) sending false temperature data underground |
| **Tamper signature: JUMP** | The fake temperature spikes suddenly — like someone injecting a false reading all at once (spoofing signature) |
| **Tamper signature: DRIFT** | The fake temperature creeps up slowly over several readings — like a sensor slowly losing calibration |
| **Reported temp °C** | What the sensor is actually sending back from underground |
| **Predicted temp °C** | What physics says the temperature *should* be, based on known rock temperature, depth, and airflow |
| **Wet-Bulb °C** | The heat-humidity combination that determines when human bodies overheat. SA law (MHSA) says work must stop above **28°C wet-bulb** |
| **Priority 1 / Priority 2** | Risk ranking — Priority 1 is the most urgent zone requiring immediate action |
| **Composite Risk Score** | A number combining: how far the wet-bulb is from the 28°C limit + how many workers are in the zone + how severe the anomaly is |
| **Signature (NORMAL / DRIFT / JUMP)** | The anomaly type the system has classified for that zone |
| **Recommended Action** | What the system says should happen — e.g. redirect ventilation or evacuate |
| **Anonymous Workers** | How many people are in the zone — shown as a count only, never names (POPIA-aligned) |
| **Data Privacy expander** | Shows how worker badge IDs are one-way hashed (scrambled) at the sensor so the platform never sees who is where, only *how many* |

### Commercial Door

For businesses that want to buy the waste heat the mine pumps to the surface via a **tPPA (thermal Power Purchase Agreement)**.

| Term | What it means |
|---|---|
| **Fence-line Capacity (MWth)** | The total megawatts of thermal energy available at the mine's boundary — e.g. Driefontein has 14.5 MWth |
| **Tariff Discount (25% below Eskom)** | The buyer pays 25% less than the standard Eskom industrial electricity rate for this heat |
| **Mandatory Local Hiring Quota (60%)** | Any business that buys the heat must hire at least 60% of its workforce from the local community — baked into the contract |
| **Eskom baseline tariff** | The standard SA industrial electricity price (R2.15/kWh) used as the comparison point |
| **tPPA (thermal Power Purchase Agreement)** | A 5-year contract where a business pays the mine for heat instead of paying Eskom for electricity to generate that same heat themselves |
| **Heat capacity slider (MWth)** | Select how many megawatts of heat to secure — the savings and revenue figures update live |
| **Your est. annual savings** | How much the off-taker (buyer) saves per year versus paying Eskom for equivalent energy |
| **Mine's est. annual revenue** | How much the mine earns annually from this deal |
| **Express Interest** | A one-tap form to register intent — no sign-in, no backend, session record only for demo purposes |

### Community Door

For local residents, youth cooperatives, and small enterprises. When no commercial buyer takes the heat, it powers community incubation projects instead.

| Term | What it means |
|---|---|
| **Heat Allocated (MWth)** | How many megawatts of thermal energy that specific project uses — drawn from the mine's surplus |
| **Water Temp** | The temperature range of the warm water delivered to the project — each use case needs a different range (e.g. aquaculture needs 26–28°C, drying needs 40–50°C) |
| **Jobs Created** | Direct and seasonal employment the project is expected to generate in the local community |
| **SLP metric** | Social and Labour Plan metric — the measurable community benefit the mine must prove to its regulator; each card shows what it contributes |
| **Focus group** | Who the opportunity is specifically designed for (e.g. local youth & women, youth cooperatives & persons with disabilities) |
| **RAS (Recirculating Aquaculture System)** | The fish farming method used in the tilapia card — water circulates in a closed loop at a controlled temperature |
| **Apply — 1 step** | A simple form to register interest in that opportunity — name only, no backend |

### How the three sections connect

The mine generates heat underground → the **Underground Engine** predicts and monitors it → surplus heat reaches the surface → the **Commercial Door** gives businesses first pick → the **Community Door** captures everything unallocated. The live gauge bar at the top of the dashboard shows exactly how much of the available thermal output is allocated at any moment.
