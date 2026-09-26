"""
ThermalTwin (MineFlow AI) — Dashboard & Integration
====================================================
Role: Dashboard & Integration (app.py)

Wires together:
  - simulator.py -> synthetic underground telemetry (per mine/zone)
  - anomaly.py -> rolling Z-score, physics-mismatch, DRIFT/JUMP signatures, worker-risk ranking
  - privacy.py -> POPIA-safe worker-tag hashing / anonymous occupancy counts
  - config.py -> single source of truth for mines, thresholds, Surface Engine Portal data

Screens (the 5-screen two-sided portal, no backend, no login):
  1. Underground Engine — live safety telemetry, tamper injection, worker-risk ranking
  2. Commercial Door — fence-line heat capacity, tPPA "Express Interest"
  3. Community Door — incubation opportunity cards, 1-step "Apply"
  4. Live Status Header — Available Thermal Output vs Allocated Community Hubs (always visible)
  5. ICP / About — problem, solution, honest caveats for judges

Run with: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import anomaly
import config
import privacy
import simulator

st.set_page_config(
    page_title="ThermalTwin — MineFlow AI",
    page_icon=":thermometer:",
    layout="wide",
)


# ---------------------------------------------------------------------
# VISUAL IDENTITY — control-room theme, not default SaaS grey.
# Amber = heat/thermal, cyan = safety/commercial, green = nominal/community.
# ---------------------------------------------------------------------
def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

        :root {
          --tt-bg: #12181C;
          --tt-panel: #182027;
          --tt-border: #2B363D;
          --tt-text: #E8ECEE;
          --tt-muted: #8FA0A8;
          --tt-amber: #FF8A3D;
          --tt-cyan: #3FC6D1;
          --tt-green: #59C97A;
          --tt-red: #E5484D;
        }

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--tt-text); }
        .stApp { background-color: var(--tt-bg); }

        h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
          font-family: 'Oswald', sans-serif !important;
          letter-spacing: 0.02em;
          color: var(--tt-text);
        }

        [data-testid="stSidebar"] { background-color: var(--tt-panel); border-right: 1px solid var(--tt-border); }

        [data-testid="stMetric"] {
          background-color: var(--tt-panel);
          border: 1px solid var(--tt-border);
          border-top: 2px solid var(--tt-amber);
          border-radius: 4px;
          padding: 12px 14px;
        }
        [data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace !important; color: var(--tt-text); }
        [data-testid="stMetricLabel"] { color: var(--tt-muted) !important; }

        [data-testid="stVerticalBlockBorderWrapper"] {
          background-color: var(--tt-panel);
          border: 1px solid var(--tt-border) !important;
          border-radius: 4px !important;
        }

        [data-testid="stForm"] {
          background-color: transparent;
          border: none;
          padding: 0;
        }

        .stButton > button, .stFormSubmitButton > button {
          font-family: 'Inter', sans-serif;
          font-weight: 600;
          background-color: var(--tt-cyan);
          color: #0A1418;
          border: none;
          border-radius: 3px;
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover {
          background-color: var(--tt-amber);
          color: #0A1418;
        }

        [data-testid="stTabs"] button { font-family: 'Inter', sans-serif; font-weight: 500; }
        [data-testid="stTabs"] button[aria-selected="true"] {
          color: var(--tt-amber) !important;
          border-bottom-color: var(--tt-amber) !important;
        }

        .stDataFrame, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
          font-family: 'IBM Plex Mono', monospace !important;
          font-size: 0.85rem !important;
        }

        .tt-gauge-track {
          width: 100%; height: 22px; background-color: #0A1013;
          border: 1px solid var(--tt-border); border-radius: 3px; overflow: hidden;
          display: flex; margin: 6px 0 4px 0;
        }
        .tt-gauge-community { background-color: var(--tt-green); height: 100%; }
        .tt-gauge-commercial { background-color: var(--tt-cyan); height: 100%; }
        .tt-gauge-caption {
          font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: var(--tt-muted);
          display: flex; justify-content: space-between;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# SESSION STATE (no backend — everything lives in-memory for the demo)
# ---------------------------------------------------------------------
if "tamper_active" not in st.session_state:
    st.session_state.tamper_active = False
if "tamper_mode" not in st.session_state:
    st.session_state.tamper_mode = config.SIGNATURE_JUMP
if "commercial_interests" not in st.session_state:
    st.session_state.commercial_interests = []
if "community_applications" not in st.session_state:
    st.session_state.community_applications = []
if "telemetry_cache" not in st.session_state:
    st.session_state.telemetry_cache = {}


# ---------------------------------------------------------------------
# STAGING BANNER (Phase 1 Active Demo vs Phase 2 Roadmap)
# ---------------------------------------------------------------------
def render_staging_banner() -> None:
    p1 = config.STAGING_CONFIG["Phase 1"]
    p2 = config.STAGING_CONFIG["Phase 2"]
    st.markdown(
        f"""
        <div style="background-color:#182027;border:1px solid #2B363D;border-left:3px solid #59C97A;
        padding:10px 18px;border-radius:4px;display:flex;flex-wrap:wrap;
        justify-content:space-between;gap:8px;margin-bottom:14px;
        font-family:'IBM Plex Mono',monospace;font-size:0.85rem;">
          <div style="color:#59C97A;">
            ● {p1['name']} · {p1['depth_band']} · {', '.join(p1['mines'])}
          </div>
          <div style="color:#8FA0A8;">
            ○ {p2['name']} · {p2['depth_band']} · {', '.join(p2['mines'])}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# SHARED LIVE STATUS HEADER
# ---------------------------------------------------------------------
def render_status_header(selected_mine: str) -> None:
    mine_cfg = config.get_mine_config(selected_mine)
    available_mw = float(mine_cfg["available_heat_capacity_mw"])

    community_mw = config.get_total_allocated_community_heat_mw()
    commercial_mw = sum(i["heat_mw"] for i in st.session_state.commercial_interests)
    allocated_mw = round(community_mw + commercial_mw, 2)
    remaining_mw = max(0.0, round(available_mw - allocated_mw, 2))

    st.markdown(f"#### {config.SURFACE_PORTAL_HEADER}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Available Thermal Output", f"{available_mw:.1f} MWth", help=f"{selected_mine} fence-line capacity")
    c2.metric("Allocated (Community + Commercial)", f"{allocated_mw:.1f} MWth")
    c3.metric("Unallocated Headroom", f"{remaining_mw:.1f} MWth")

    community_pct = min(100.0, (community_mw / available_mw) * 100) if available_mw > 0 else 0.0
    commercial_pct = min(100.0 - community_pct, (commercial_mw / available_mw) * 100) if available_mw > 0 else 0.0
    st.markdown(
        f"""
        <div class="tt-gauge-track">
          <div class="tt-gauge-community" style="width:{community_pct:.1f}%;"></div>
          <div class="tt-gauge-commercial" style="width:{commercial_pct:.1f}%;"></div>
        </div>
        <div class="tt-gauge-caption">
          <span>● community {community_mw:.1f} MWth &nbsp; ● commercial {commercial_mw:.1f} MWth</span>
          <span>{remaining_mw:.1f} MWth headroom</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# DATA GENERATION (cached per mine + tamper settings for this session)
# ---------------------------------------------------------------------
def get_telemetry(mine_name: str) -> pd.DataFrame:
    cache_key = (mine_name, st.session_state.tamper_active, st.session_state.tamper_mode)
    if cache_key not in st.session_state.telemetry_cache:
        df = simulator.simulate_mine_telemetry(
            mine_name=mine_name,
            num_samples=180,
            inject_physics_mismatch=st.session_state.tamper_active,
            tamper_mode=st.session_state.tamper_mode,
        )
        st.session_state.telemetry_cache[cache_key] = df
    return st.session_state.telemetry_cache[cache_key]


def build_zone_summaries(df: pd.DataFrame) -> list:
    """Run each zone's timeseries through the anomaly engine end-to-end."""
    summaries = []
    for zone in df["zone"].unique():
        zone_df = df[df["zone"] == zone].sort_values("timestamp")
        result = anomaly.process_telemetry_stream(
            reported_temps=zone_df["reported_temp_c"].tolist(),
            predicted_temps=zone_df["predicted_temp_c"].tolist(),
            wet_bulb_temps=zone_df["wet_bulb_c"].tolist(),
            worker_counts=zone_df["zone_occupancy_count"].tolist(),
            zone_name=zone,
        )
        summaries.append(result)
    summaries.sort(key=lambda r: r["composite_risk_score"], reverse=True)
    return summaries


# ---------------------------------------------------------------------
# SCREEN 1: UNDERGROUND ENGINE (safety)
# ---------------------------------------------------------------------
def render_underground_engine(selected_mine: str) -> None:
    st.subheader("Underground Engine — Predictive Safety & Security")
    st.caption(
        f"Predicts a dangerous heat spike ~{config.PREDICTION_LEAD_TIME_MINUTES} minutes ahead of time, "
        "and doubles as a tamper-detection layer using the same physics baseline."
    )

    ctrl_col, info_col = st.columns([1, 2])
    with ctrl_col:
        st.markdown("**Demo controls**")
        st.session_state.tamper_active = st.toggle(
            "Inject sensor tampering", value=st.session_state.tamper_active
        )
        st.session_state.tamper_mode = st.radio(
            "Tamper signature",
            [config.SIGNATURE_JUMP, config.SIGNATURE_DRIFT],
            index=0 if st.session_state.tamper_mode == config.SIGNATURE_JUMP else 1,
            horizontal=True,
            help="JUMP = sudden spoofing step. DRIFT = gradual sensor wear/calibration decay.",
        )
        if st.button("Regenerate telemetry"):
            st.session_state.telemetry_cache = {}
            st.rerun()

    df = get_telemetry(selected_mine)
    summaries = build_zone_summaries(df)

    with info_col:
        top = summaries[0]
        if top["priority"].startswith("Priority 1"):
            st.error(f"ALERT: {top['zone']}: {top['priority']} — {top['recommended_action']}")
        elif top["priority"].startswith("Priority 2"):
            st.warning(f"WARNING: {top['zone']}: {top['priority']} — {top['recommended_action']}")
        else:
            st.success(f"All zones nominal. Highest priority: {top['zone']} ({top['priority']}).")

    zone_names = [s["zone"] for s in summaries]
    focus_zone = st.selectbox("Zone detail", zone_names, index=0)
    zone_df = df[df["zone"] == focus_zone].sort_values("timestamp").set_index("timestamp")
    st.line_chart(zone_df[["reported_temp_c", "predicted_temp_c"]])

    st.markdown("**Worker-Risk Ranking** (anonymous occupancy only — see Data Privacy note below)")
    ranking_table = pd.DataFrame(
        [
            {
                "Rank": i + 1,
                "Zone": s["zone"],
                "Priority": s["priority"],
                "Risk Score": s["composite_risk_score"],
                "Wet-Bulb °C": s["latest_wet_bulb_c"],
                "Signature": s["latest_signature"],
                "Anonymous Workers": s["worker_count"],
            }
            for i, s in enumerate(summaries)
        ]
    )
    st.dataframe(ranking_table, use_container_width=True, hide_index=True)

    with st.expander("Data Privacy — how worker counts are produced"):
        sample_ids = [f"{focus_zone.replace(' ', '').upper()}-{i}" for i in range(6)]
        hashed = privacy.hash_worker_ids(sample_ids)
        st.write("Raw badge IDs never leave the sensor layer. Example (illustrative only):")
        st.code(f"Raw: {sample_ids}\nHashed: {hashed}\nCount: {privacy.zone_occupancy_density(hashed)}")
        st.caption("No PII is stored or transmitted — only a de-duplicated hashed occupancy count, per the POPIA note in the pitch pack.")


# ---------------------------------------------------------------------
# SCREEN 2: COMMERCIAL DOOR
# ---------------------------------------------------------------------
def render_commercial_door(selected_mine: str) -> None:
    st.subheader("Commercial Door — Thermal Power Purchase Agreement (tPPA)")
    mine_cfg = config.get_mine_config(selected_mine)
    cfg = config.COMMERCIAL_DOOR_CONFIG

    c1, c2, c3 = st.columns(3)
    c1.metric("Fence-line Capacity", f"{mine_cfg['available_heat_capacity_mw']:.1f} MWth")
    c2.metric("Tariff Discount", f"{cfg['default_discount_percent']:.0f}% below Eskom")
    c3.metric("Mandatory Local Hiring Quota", f"{cfg['mandatory_local_hiring_quota']:.0f}%")
    st.caption(cfg["tppa_summary"])

    max_mw = float(mine_cfg["available_heat_capacity_mw"])
    requested_mw = st.slider("Heat capacity you'd like to secure (MWth)", 0.5, max_mw, min(2.0, max_mw), 0.5)
    savings = config.calculate_commercial_savings(requested_mw)

    s1, s2 = st.columns(2)
    s1.metric("Your est. annual savings", f"R {savings['annual_offtaker_savings_zar']:,.0f}")
    s2.metric("Mine's est. annual revenue from this deal", f"R {savings['annual_mine_revenue_zar']:,.0f}")

    with st.form("express_interest_form"):
        st.markdown("**1-Tap Express Interest**")
        name = st.text_input("Company name")
        contact = st.text_input("Contact email")
        submitted = st.form_submit_button("Express Interest in tPPA")
        if submitted:
            if name and contact:
                st.session_state.commercial_interests.append(
                    {"company": name, "contact": contact, "heat_mw": requested_mw, "mine": selected_mine}
                )
                st.success(f"Interest recorded for {requested_mw:.1f} MWth at {selected_mine}. The team will follow up.")
            else:
                st.error("Please provide a company name and contact email.")

    if st.session_state.commercial_interests:
        with st.expander(f"Express Interest submissions ({len(st.session_state.commercial_interests)})"):
            st.dataframe(pd.DataFrame(st.session_state.commercial_interests), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# SCREEN 3: COMMUNITY DOOR
# ---------------------------------------------------------------------
def render_community_door() -> None:
    st.subheader("Community Door — Incubation Opportunities")
    st.caption("Plain-language opportunities for local youth, women, and persons living with disabilities — no private off-taker required.")

    cards = config.get_community_cards()
    cols = st.columns(2)
    for idx, card in enumerate(cards):
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"**{card['title']}**")
                st.caption(card["focus_group"])
                st.write(card["description"])
                m1, m2, m3 = st.columns(3)
                m1.metric("Heat Allocated", f"{card['allocated_mw']} MWth")
                m2.metric("Water Temp", card["water_temp_c"])
                m3.metric("Jobs Created", card["jobs_created"])
                st.caption(f"SLP metric: {card['slp_metric']}")

                with st.form(f"apply_form_{card['id']}"):
                    applicant = st.text_input("Your name", key=f"name_{card['id']}")
                    apply_clicked = st.form_submit_button("Apply — 1 step")
                    if apply_clicked:
                        if applicant:
                            st.session_state.community_applications.append(
                                {"applicant": applicant, "opportunity": card["title"]}
                            )
                            st.success(f"Application received for {card['title']}.")
                        else:
                            st.error("Please enter your name.")

    if st.session_state.community_applications:
        with st.expander(f"Applications received ({len(st.session_state.community_applications)})"):
            st.dataframe(pd.DataFrame(st.session_state.community_applications), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# SCREEN 4: ICP / ABOUT
# ---------------------------------------------------------------------
def render_about() -> None:
    st.subheader("About ThermalTwin (MineFlow AI)")
    st.markdown(
        """
Deep gold mines spend heavily to fight naturally hot rock underground; a few hundred metres away,
Merafong households often can't afford to use the power they're connected to. ThermalTwin sits
between the two:

- **Underground Engine** — predicts dangerous heat 25–30 minutes ahead, and its physics baseline
  doubles as a tamper-detection layer (a sensor claiming "cold" when physics says "hot" is itself the alarm).
- **Surface Engine** — captures heat already being pumped to surface for cooling and routes it to
  businesses (Commercial Door) or community incubation projects (Community Door) when no
  business takes the deal, with only heat — never mine water — ever leaving the fence line.
        """
    )
    with st.expander("Honest caveats (say these out loud if asked)"):
        st.markdown(
            """
- This demo runs on **simulated telemetry**, not a trained ML model — the "predicted" baseline is a scripted
  physics stand-in deliberately offset from the "reported" value to demonstrate the concept.
- Phase 1 targets "cold water" mines (Driefontein, South Deep, Kusasalethu, Kloof); Phase 2 (Mponeng,
  TauTona) needs a different heat-exchanger design suited to melted ice-brine, not chilled water.
- The competitive claim that established OT-security vendors underserve mid-tier SA mines is our belief,
  not yet confirmed with an industry source.
            """
        )


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
def main() -> None:
    inject_theme()
    render_staging_banner()
    st.title("ThermalTwin — MineFlow AI")

    phase1_mines = config.get_mines_by_phase(1)
    selected_mine = st.sidebar.selectbox("Active mine (Phase 1 demo)", phase1_mines, index=phase1_mines.index(config.DEFAULT_MINE))
    st.sidebar.caption(config.get_mine_config(selected_mine)["location"])
    st.sidebar.markdown("---")
    st.sidebar.caption("No login. No backend. All data for this demo lives in your browser session only.")

    render_status_header(selected_mine)
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["Underground Engine", "Commercial Door", "Community Door", "About"])
    with tab1:
        render_underground_engine(selected_mine)
    with tab2:
        render_commercial_door(selected_mine)
    with tab3:
        render_community_door()
    with tab4:
        render_about()


if __name__ == "__main__":
    main()