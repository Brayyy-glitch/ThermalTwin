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
- **Surface Engine** — a fence-line heat exchanger model and revenue calculator for selling a mine's
  rejected heat to adjacent commercial partners (greenhouses, aquaculture), without altering the
  mine's existing water treatment or cooling circuit.
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

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Demo script (~3 minutes)

1. **Baseline** — open the dashboard, show the Phase 1/Phase 2 staging banner, pick a mine from the
   sidebar (note the numbers actually change per mine — this isn't cosmetic).
2. **Inject the tamper event** — toggle "Inject Physics Mismatch," watch Zone 2's predicted-vs-reported
   chart diverge and the alert fire, tagged `JUMP` and ranked by worker occupancy.
3. **Show the Z-score expander** — the statistical layer behind the alert.
4. **Show the Data Privacy expander** — raw fake worker IDs going in, hashed tags coming out.
5. **Surface Matchmaker** — adjust the sidebar heat/tariff inputs, show the fence-line revenue estimate.

## What's simulated vs. real, stated plainly

- All telemetry is synthetic — there is no live mine data. The simulation is grounded in sourced,
  real physical parameters (chilled water at ~5°C, 60–80°C virgin rock temperatures, the 28°C
  statutory wet-bulb safety limit), not arbitrary numbers.
- The "predicted" temperature is a scripted physics-based baseline, not a trained ML model.
- Telemetry ingestion is a direct function call in this build, not a running MQTT/Modbus pipeline —
  see `TEAM_AND_STACK.md` for what that would take to make literally true.
- Cross-sensor validation (comparing neighbouring RTD sensors) is part of the target user journey but
  not yet implemented — only per-zone rolling Z-score is live.

Supporting documents (not code): `ThermalTwin_Explained_Simply.pdf` (plain-language project overview),
`ThermalTwin_Rebuttal_Prep.pdf` (anticipated judge questions and honest answers, including this
project's open items), `Technical_Feasibility_Notes_OT_ICS_Anomaly_Detection.pdf` (background research
on OT/ICS anomaly detection approaches).

## Open items

- The claim that established OT-security vendors (Dragos/Claroty/Nozomi) don't serve mid-tier SA
  mines is still unverified — this is the single highest-risk unconfirmed assumption in the pitch.
- No confirmed real-world contact or quote from a Carletonville-area mine or resident yet.
- Final funding figure for the Lean Canvas/pitch ask is not yet locked in.