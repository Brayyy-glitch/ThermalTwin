# Security & Trust Notes — for the SSDLC / Data Privacy slide + rebuttal prep

Source material: Devlab "Building Security Capabilities" workshop (PASTA, security lifecycle)
and the Devlab quantum-tech workshop (post-quantum cryptography). Owner: Narrative & Compliance.

## 1. PASTA — framing our existing detection as a named process, not ad-hoc code

PASTA (Process for Attack Simulation and Threat Analysis) gives judges a recognized methodology
name instead of "we wrote some anomaly detection." Mapped onto what `anomaly.py` / `config.py`
already do:

| PASTA stage | ThermalTwin answer |
|---|---|
| Identify risk evaluation criteria | Worker safety (heat exposure) and sensor data integrity — both feed into the 28°C statutory wet-bulb limit in `config.py` |
| Identify crucial assets | RTD temperature sensors, the telemetry pipeline, hashed worker-occupancy data, the fence-line heat-exchange interface |
| Understand operational risk tolerance | Near-zero tolerance for missed heat spikes (life-safety); moderate tolerance for false positives (operational cost, not safety) — this is *why* the system is tuned as alert-then-verify, not auto-shutdown |
| Identify threats & vulnerabilities | Sensor spoofing (`JUMP` signature), calibration drift (`DRIFT` signature), and — stated honestly — no live protection yet against a compromised MQTT/Modbus link, since that layer is still a stretch goal |
| Mitigate | The physics-aware baseline itself: predicted-vs-reported divergence is the mitigation, not a bolt-on afterthought |

## 2. Security lifecycle — mapped onto the actual repo

| Lifecycle stage | What this already is in ThermalTwin |
|---|---|
| Planning | `config.py` — the single source of truth for thresholds and ICP staging |
| Implementation | `simulator.py`, `anomaly.py`, `privacy.py`, `app.py` |
| Monitoring | The live dashboard's alert panel + Z-score expander |
| Maintenance | Threshold tuning in `config.py` (documented as the one safe file to hand-edit) |
| Review & update | `ThermalTwin_Rebuttal_Prep.pdf` + this document |

## 3. Post-quantum cryptography — the "trusted 10 years from now" answer

Judges were explicitly coached to ask: *"Does the transition to post-quantum cryptography mean
data stored today needs to be re-encrypted?"* and *"Is the data sensitive long-term?"* Have this
answer ready:

- **What we actually use today:** `privacy.py` hashes worker IDs with SHA-256 (one-way, salted).
  This is a hash function, not an asymmetric scheme (RSA/ECC/Diffie-Hellman) — it is **not**
  broken by Shor's algorithm. Grover's algorithm only gives a quadratic speedup against hash
  preimage resistance, which halves the *effective* bit-security (256-bit → ~128-bit quantum
  security) — still comfortably strong. So: **no re-encryption of stored data is needed**, and we
  can say so with a specific technical reason, not a hand-wave.
- **Is the data sensitive long-term?** Zone occupancy counts (the only thing that leaves the edge
  layer per `privacy.py`) are not identity records, health records, or government records — the
  high-risk categories called out in the workshop. So the "harvest now, decrypt later" threat model
  mainly matters here as a reason the hashing (not raw IDs) design choice is correct, not as an
  open risk.
- **Where PQC actually becomes relevant — honestly flagged as a roadmap item, not implemented:**
  If the MQTT/Modbus stretch goal (`TEAM_AND_STACK.md`) ships, that's a real network session that
  would need key exchange. The workshop's own recommendation applies directly: adapt a TLS-style
  session setup to use **ML-KEM (FIPS 203)** for key encapsulation instead of classical RSA/ECDH,
  optionally as a hybrid (classical + PQC together) rather than a hard swap. This is a one-line
  roadmap bullet on the Technical Architecture slide, not something to build for the demo.

## 4. Ready-made answers for the two judge questions most likely to land

- *"How many teams know which cryptographic algorithms are used in their solution?"*
  → SHA-256 (hashing, `privacy.py`), no asymmetric crypto in the current build; ML-KEM named as
  the PQC upgrade path if/when MQTT/Modbus ships.
- *"What evidence can you provide that your solution can still be trusted ten years from now?"*
  → The hashing choice was already quantum-resistant by construction, not retrofitted after this
  workshop — worth saying plainly rather than over-claiming foresight.