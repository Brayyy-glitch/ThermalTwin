"""
ThermalTwin (MineFlow AI) — Dashboard & Integration
====================================================
Role: Dashboard & Integration (app.py)

Screens:
  Landing    — Role selection (Community / Mine Operator)
  Community  — Incubation opportunity cards linking to external forms
  Login      — Credential gate for mine operators
  Operator   — Underground Engine + Commercial Door + About (operator-only)

Run with: streamlit run app.py
"""

import hashlib

import pandas as pd
import streamlit as st

import anomaly
import config
import privacy
import simulator

# =====================================================================
# PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title="ThermalTwin — MineFlow AI",
    page_icon=":thermometer:",
    layout="wide",
)

# =====================================================================
# CREDENTIALS  (demo only — hardcoded, no real auth backend)
# Username: operator   Password: thermaltwin2026
# =====================================================================
_OPERATOR_USERNAME = "operator"
_OPERATOR_PASSWORD_HASH = hashlib.sha256("thermaltwin2026".encode()).hexdigest()

# =====================================================================
# COMMUNITY FORM LINKS  (replace placeholder URLs before going live)
# =====================================================================
COMMUNITY_FORM_URLS = {
    "merafong_hydroponics":  "https://forms.google.com/PLACEHOLDER_HYDROPONICS",
    "tilapia_aquaculture":   "https://forms.google.com/PLACEHOLDER_AQUACULTURE",
    "post_harvest_drying":   "https://forms.google.com/PLACEHOLDER_DRYING",
    "sanitation_laundry":    "https://forms.google.com/PLACEHOLDER_LAUNDRY",
}

# =====================================================================
# THEME
# Blue/white base  |  Green = stable  |  Amber = caution  |  Red = critical
# =====================================================================
def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

        :root {
          --tt-bg:        #F0F4F8;
          --tt-surface:   #FFFFFF;
          --tt-navy:      #1A3C5E;
          --tt-blue:      #2563EB;
          --tt-blue-lt:   #EFF6FF;
          --tt-border:    #CBD5E1;
          --tt-text:      #0F172A;
          --tt-muted:     #64748B;
          --tt-green:     #16A34A;
          --tt-green-bg:  #DCFCE7;
          --tt-amber:     #D97706;
          --tt-amber-bg:  #FEF3C7;
          --tt-red:       #DC2626;
          --tt-red-bg:    #FEE2E2;
        }

        html, body, [class*="css"] {
          font-family: 'Inter', sans-serif;
          color: var(--tt-text);
          background-color: var(--tt-bg);
        }
        .stApp { background-color: var(--tt-bg); }
        /* Ensure markdown text inside HTML blocks is never forced white */
        .stMarkdown p, .stMarkdown span, .stMarkdown li { color: var(--tt-text) !important; }

        /* Headings */
        h1, h2, h3, h4,
        .stMarkdown h1, .stMarkdown h2,
        .stMarkdown h3, .stMarkdown h4 {
          font-family: 'Inter', sans-serif !important;
          font-weight: 700;
          color: var(--tt-navy);
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
          background-color: var(--tt-navy);
          border-right: 1px solid var(--tt-border);
        }
        [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
        [data-testid="stSidebar"] .stSelectbox label { color: #CBD5E1 !important; }

        /* Metric cards */
        [data-testid="stMetric"] {
          background-color: var(--tt-surface);
          border: 1px solid var(--tt-border);
          border-top: 3px solid var(--tt-blue);
          border-radius: 6px;
          padding: 14px 16px;
        }
        [data-testid="stMetricValue"] {
          font-family: 'IBM Plex Mono', monospace !important;
          color: var(--tt-navy) !important;
        }
        [data-testid="stMetricLabel"] { color: var(--tt-muted) !important; }

        /* Bordered containers */
        [data-testid="stVerticalBlockBorderWrapper"] {
          background-color: var(--tt-surface);
          border: 1px solid var(--tt-border) !important;
          border-radius: 6px !important;
        }

        /* Forms */
        [data-testid="stForm"] {
          background-color: transparent;
          border: none;
          padding: 0;
        }

        /* Buttons */
        .stButton > button,
        .stFormSubmitButton > button {
          font-family: 'Inter', sans-serif;
          font-weight: 600;
          background-color: var(--tt-blue);
          color: #FFFFFF;
          border: none;
          border-radius: 4px;
          padding: 8px 20px;
        }
        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
          background-color: var(--tt-navy);
          color: #FFFFFF;
        }

        /* Tabs */
        [data-testid="stTabs"] button {
          font-family: 'Inter', sans-serif;
          font-weight: 500;
          color: var(--tt-muted);
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
          color: var(--tt-blue) !important;
          border-bottom-color: var(--tt-blue) !important;
          font-weight: 700;
        }

        /* Data tables */
        .stDataFrame {
          font-family: 'IBM Plex Mono', monospace !important;
          font-size: 0.82rem !important;
        }

        /* Signal badges */
        .tt-badge {
          display: inline-block;
          font-family: 'Inter', sans-serif;
          font-weight: 600;
          font-size: 0.78rem;
          padding: 3px 10px;
          border-radius: 12px;
          letter-spacing: 0.03em;
        }
        .tt-green  { background: var(--tt-green-bg);  color: var(--tt-green); }
        .tt-amber  { background: var(--tt-amber-bg);  color: var(--tt-amber); }
        .tt-red    { background: var(--tt-red-bg);    color: var(--tt-red);   }

        /* Alert banners */
        .tt-alert-green {
          background: var(--tt-green-bg);
          border-left: 4px solid var(--tt-green);
          color: var(--tt-green);
          padding: 12px 16px; border-radius: 4px; margin: 8px 0;
          font-weight: 600;
        }
        .tt-alert-amber {
          background: var(--tt-amber-bg);
          border-left: 4px solid var(--tt-amber);
          color: var(--tt-amber);
          padding: 12px 16px; border-radius: 4px; margin: 8px 0;
          font-weight: 600;
        }
        .tt-alert-red {
          background: var(--tt-red-bg);
          border-left: 4px solid var(--tt-red);
          color: var(--tt-red);
          padding: 12px 16px; border-radius: 4px; margin: 8px 0;
          font-weight: 600;
        }

        /* Role cards on landing */
        .tt-role-card {
          background: var(--tt-surface);
          border: 2px solid var(--tt-border);
          border-radius: 10px;
          padding: 32px 24px;
          text-align: center;
          cursor: pointer;
          transition: border-color 0.2s;
        }
        .tt-role-card:hover { border-color: var(--tt-blue); }
        .tt-role-card .tt-card-icon {
          font-size: 2.4rem;
          margin-bottom: 12px;
          color: var(--tt-blue);
        }
        .tt-role-card h3 { color: var(--tt-navy) !important; margin: 0 0 6px 0; }
        .tt-role-card p  { color: var(--tt-muted) !important; font-size: 0.9rem; margin: 0; }

        /* Gauge bar */
        .tt-gauge-track {
          width: 100%; height: 20px;
          background: #E2E8F0;
          border: 1px solid var(--tt-border);
          border-radius: 4px;
          overflow: hidden;
          display: flex;
          margin: 6px 0 4px 0;
        }
        .tt-gauge-community  { background: var(--tt-green); height: 100%; }
        .tt-gauge-commercial { background: var(--tt-blue);  height: 100%; }
        .tt-gauge-caption {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 0.76rem;
          color: var(--tt-muted);
          display: flex;
          justify-content: space-between;
        }

        /* Divider */
        hr { border-color: var(--tt-border); }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# SESSION STATE INIT
# =====================================================================
def _init_state() -> None:
    defaults = {
        "role":                  None,          # "community" | "operator"
        "authenticated":         False,
        "tamper_active":         False,
        "tamper_mode":           config.SIGNATURE_JUMP,
        "commercial_interests":  [],
        "telemetry_cache":       {},
        "confirm_action":        None,          # pending human-fallback confirmation
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =====================================================================
# HELPERS — signal colour mapping
# =====================================================================
def _priority_to_signal(priority: str) -> str:
    """Map anomaly.py priority label to green | amber | red."""
    p = priority.lower()
    if "critical" in p or "priority 1" in p:
        return "red"
    if "high" in p or "priority 2" in p:
        return "amber"
    return "green"


def _signal_badge(label: str, signal: str) -> str:
    return f'<span class="tt-badge tt-{signal}">{label}</span>'


def _signal_banner(message: str, signal: str) -> None:
    st.markdown(
        f'<div class="tt-alert-{signal}">{message}</div>',
        unsafe_allow_html=True,
    )


# =====================================================================
# SCREEN 0 — LANDING (role selection)
# =====================================================================
def render_landing() -> None:
    st.markdown(
        """
        <div style="text-align:center; padding: 40px 0 24px 0;">
          <h1 style="color:#1A3C5E; font-size:2rem; margin-bottom:6px;">ThermalTwin — MineFlow AI</h1>
          <p style="color:#64748B; font-size:1rem;">
            Deep-level mine safety &amp; community heat reuse platform
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown(
            """
            <div class="tt-role-card">
              <div class="tt-card-icon">
                <!-- Mine / industrial building icon -->
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"
                     viewBox="0 0 24 24" fill="none"
                     stroke="#2563EB" stroke-width="1.6"
                     stroke-linecap="round" stroke-linejoin="round">
                  <rect x="2" y="7" width="20" height="14" rx="1"/>
                  <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
                  <line x1="12" y1="12" x2="12" y2="16"/>
                  <line x1="9"  y1="14" x2="15" y2="14"/>
                  <rect x="9" y="16" width="6" height="5"/>
                </svg>
              </div>
              <h3>I am with the mine</h3>
              <p>Access the underground safety dashboard, thermal output data,
                 and commercial partner tools. Operator credentials required.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Enter — Operator Login", key="btn_operator", use_container_width=True):
            st.session_state.role = "operator"
            st.rerun()

    with right:
        st.markdown(
            """
            <div class="tt-role-card">
              <div class="tt-card-icon">
                <!-- Community / people icon -->
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"
                     viewBox="0 0 24 24" fill="none"
                     stroke="#2563EB" stroke-width="1.6"
                     stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="9"  cy="7"  r="3"/>
                  <circle cx="17" cy="9"  r="2.2"/>
                  <path d="M2 21v-1a7 7 0 0 1 14 0v1"/>
                  <path d="M17 21v-1a4.5 4.5 0 0 0-2.5-4"/>
                </svg>
              </div>
              <h3>I am from the community</h3>
              <p>Explore incubation opportunities powered by mine waste heat —
                 hydroponics, aquaculture, agro-processing, and more.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Enter — Community Portal", key="btn_community", use_container_width=True):
            st.session_state.role = "community"
            st.rerun()

    st.markdown(
        """
        <p style="text-align:center; color:#94A3B8; font-size:0.78rem; margin-top:48px;">
          No personal data is collected on this portal. Worker occupancy is anonymised at source.
        </p>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# SCREEN 1 — COMMUNITY DOOR
# =====================================================================
def render_community_portal() -> None:
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Back"):
            st.session_state.role = None
            st.rerun()
    with col_title:
        st.markdown(
            "<h2 style='margin:0;'>Community Opportunities</h2>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<p style='color:#64748B;'>Mine waste heat — energy that would otherwise be lost — "
        "powers these community incubation projects. Click <strong>Apply</strong> on any card "
        "to open the application form.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    cards = config.get_community_cards()
    col_a, col_b = st.columns(2, gap="large")

    for idx, card in enumerate(cards):
        col = col_a if idx % 2 == 0 else col_b
        with col:
            with st.container(border=True):
                st.markdown(f"### {card['title']}")
                st.caption(f"For: {card['focus_group']}")
                st.write(card["description"])

                m1, m2, m3 = st.columns(3)
                m1.metric("Heat allocated", f"{card['allocated_mw']} MWth")
                m2.metric("Water temp",     card["water_temp_c"])
                m3.metric("Jobs created",   card["jobs_created"])

                st.caption(f"SLP benefit: {card['slp_metric']}")

                form_url = COMMUNITY_FORM_URLS.get(card["id"], "#")
                st.markdown(
                    f"""
                    <a href="{form_url}" target="_blank"
                       style="display:inline-block; margin-top:10px;
                              background:#2563EB; color:#fff; font-weight:600;
                              padding:8px 20px; border-radius:4px;
                              text-decoration:none; font-size:0.9rem;">
                      &#9654; Apply
                    </a>
                    """,
                    unsafe_allow_html=True,
                )


# =====================================================================
# SCREEN 2 — OPERATOR LOGIN
# =====================================================================
def render_login() -> None:
    col_back, _ = st.columns([1, 8])
    with col_back:
        if st.button("← Back"):
            st.session_state.role = None
            st.rerun()

    st.markdown(
        "<div style='max-width:400px; margin: 60px auto 0 auto;'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h2 style='text-align:center; color:#1A3C5E;'>Operator Sign-In</h2>"
        "<p style='text-align:center; color:#64748B; margin-bottom:24px;'>"
        "Access restricted to authorised mine personnel.</p>",
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            if username == _OPERATOR_USERNAME and pw_hash == _OPERATOR_PASSWORD_HASH:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
# OPERATOR DASHBOARD — shared data helpers
# =====================================================================
def _get_telemetry(mine_name: str) -> pd.DataFrame:
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


def _build_zone_summaries(df: pd.DataFrame) -> list:
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


# =====================================================================
# OPERATOR DASHBOARD — sidebar
# =====================================================================
def _render_sidebar() -> str:
    st.sidebar.markdown(
        "<h2 style='color:#E2E8F0; font-size:1rem; margin-bottom:4px;'>"
        "ThermalTwin</h2>"
        "<p style='color:#94A3B8; font-size:0.78rem; margin-top:0;'>Operator Dashboard</p>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    phase1_mines = config.get_mines_by_phase(1)
    selected_mine = st.sidebar.selectbox(
        "Active mine",
        phase1_mines,
        index=phase1_mines.index(config.DEFAULT_MINE),
    )
    mine_cfg = config.get_mine_config(selected_mine)
    st.sidebar.caption(mine_cfg["location"])
    st.sidebar.caption(f"Depth: {mine_cfg['depth_meters']} m")
    st.sidebar.markdown("---")

    if st.sidebar.button("Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.rerun()

    return selected_mine


# =====================================================================
# OPERATOR DASHBOARD — status header
# =====================================================================
def _render_status_header(selected_mine: str) -> None:
    mine_cfg = config.get_mine_config(selected_mine)
    available_mw = float(mine_cfg["available_heat_capacity_mw"])
    community_mw = config.get_total_allocated_community_heat_mw()
    commercial_mw = sum(i["heat_mw"] for i in st.session_state.commercial_interests)
    allocated_mw  = round(community_mw + commercial_mw, 2)
    remaining_mw  = max(0.0, round(available_mw - allocated_mw, 2))

    st.markdown(f"#### {config.SURFACE_PORTAL_HEADER}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Available thermal output", f"{available_mw:.1f} MWth",
              help=f"{selected_mine} fence-line capacity")
    c2.metric("Allocated (community + commercial)", f"{allocated_mw:.1f} MWth")
    c3.metric("Unallocated headroom",    f"{remaining_mw:.1f} MWth")

    community_pct  = min(100.0, (community_mw / available_mw) * 100) if available_mw > 0 else 0.0
    commercial_pct = min(100.0 - community_pct, (commercial_mw / available_mw) * 100) if available_mw > 0 else 0.0
    st.markdown(
        f"""
        <div class="tt-gauge-track">
          <div class="tt-gauge-community"  style="width:{community_pct:.1f}%;"></div>
          <div class="tt-gauge-commercial" style="width:{commercial_pct:.1f}%;"></div>
        </div>
        <div class="tt-gauge-caption">
          <span>&#9632; community {community_mw:.1f} MWth &nbsp; &#9632; commercial {commercial_mw:.1f} MWth</span>
          <span>{remaining_mw:.1f} MWth headroom</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# TAB A — UNDERGROUND ENGINE (one decision per screen + human fallback)
# =====================================================================
def render_underground_engine(selected_mine: str) -> None:

    # --- Step 0: demo controls (collapsed, not the main focus) -------
    with st.expander("Demo controls — inject simulated sensor event"):
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.tamper_active = st.toggle(
                "Inject sensor tampering",
                value=st.session_state.tamper_active,
            )
        with c2:
            st.session_state.tamper_mode = st.radio(
                "Signature type",
                [config.SIGNATURE_JUMP, config.SIGNATURE_DRIFT],
                horizontal=True,
                help="JUMP = sudden spoof. DRIFT = gradual calibration wear.",
            )
        if st.button("Refresh telemetry"):
            st.session_state.telemetry_cache = {}
            st.session_state.confirm_action = None
            st.rerun()

    df        = _get_telemetry(selected_mine)
    summaries = _build_zone_summaries(df)
    top       = summaries[0]
    signal    = _priority_to_signal(top["priority"])

    # --- Step 1: ONE top-level decision banner -----------------------
    st.markdown("### Zone Status")

    if signal == "red":
        _signal_banner(
            f"[!] CRITICAL — {top['zone']} — Wet-bulb {top['latest_wet_bulb_c']:.1f} deg C "
            f"| {top['worker_count']} workers at risk",
            "red",
        )
    elif signal == "amber":
        _signal_banner(
            f"[~] CAUTION — {top['zone']} — Heat spike predicted within "
            f"{config.PREDICTION_LEAD_TIME_MINUTES} minutes",
            "amber",
        )
    else:
        _signal_banner(
            "[+] All zones operating within normal parameters",
            "green",
        )

    # --- Step 2: Zone summary table ----------------------------------
    st.markdown("##### Zone overview")
    rows = []
    for s in summaries:
        sig   = _priority_to_signal(s["priority"])
        badge = _signal_badge(s["latest_signature"], sig)
        rows.append({
            "Zone":             s["zone"],
            "Wet-bulb (deg C)": s["latest_wet_bulb_c"],
            "Signature":        s["latest_signature"],
            "Workers":          s["worker_count"],
            "Risk score":       s["composite_risk_score"],
            "Status":           s["priority"].split(" - ")[-1],
        })
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

    # --- Step 3: Zone detail (one zone at a time) --------------------
    st.markdown("##### Zone detail")
    zone_names = [s["zone"] for s in summaries]
    focus_zone = st.selectbox("Select zone", zone_names, index=0, label_visibility="collapsed")
    zone_df    = df[df["zone"] == focus_zone].sort_values("timestamp").set_index("timestamp")

    z_summary  = next(s for s in summaries if s["zone"] == focus_zone)
    z_signal   = _priority_to_signal(z_summary["priority"])

    col_chart, col_stats = st.columns([3, 1])
    with col_chart:
        st.caption(f"Reported vs predicted temperature — {focus_zone}")
        st.line_chart(zone_df[["reported_temp_c", "predicted_temp_c"]])
    with col_stats:
        st.metric("Wet-bulb",   f"{z_summary['latest_wet_bulb_c']:.1f} deg C")
        st.metric("Workers",    z_summary["worker_count"])
        st.metric("Signature",  z_summary["latest_signature"])
        st.markdown(
            _signal_badge(z_summary["priority"].split(" - ")[-1], z_signal),
            unsafe_allow_html=True,
        )

    # --- Step 4: HUMAN FALLBACK — operator must confirm action -------
    if z_signal in ("red", "amber"):
        st.markdown("---")
        st.markdown("##### Recommended action")
        st.info(z_summary["recommended_action"])

        st.warning(
            "This system recommends but does not act autonomously. "
            "A qualified ventilation officer must confirm before any intervention is carried out."
        )

        confirm_key = f"confirm_{focus_zone}"
        if st.session_state.confirm_action != confirm_key:
            if st.button(
                f"[>] I confirm I have reviewed this alert and authorise the recommended action for {focus_zone}",
                key=f"btn_confirm_{focus_zone}",
            ):
                st.session_state.confirm_action = confirm_key
                st.rerun()
        else:
            _signal_banner(
                f"[+] Action authorised by operator for {focus_zone}. "
                "Ventilation team has been notified. Log this intervention in the shift report.",
                "green",
            )
            if st.button("Clear confirmation", key=f"btn_clear_{focus_zone}"):
                st.session_state.confirm_action = None
                st.rerun()


# =====================================================================
# TAB B — COMMERCIAL DOOR
# =====================================================================
def render_commercial_door(selected_mine: str) -> None:
    mine_cfg = config.get_mine_config(selected_mine)
    cfg      = config.COMMERCIAL_DOOR_CONFIG

    st.markdown("### Thermal Power Purchase Agreement (tPPA)")
    st.caption(cfg["tppa_summary"])

    c1, c2, c3 = st.columns(3)
    c1.metric("[>] Fence-line capacity",       f"{mine_cfg['available_heat_capacity_mw']:.1f} MWth")
    c2.metric("[%] Tariff discount",           f"{cfg['default_discount_percent']:.0f}% below Eskom")
    c3.metric("[+] Local hiring quota",        f"{cfg['mandatory_local_hiring_quota']:.0f}% minimum")

    st.markdown("---")
    st.markdown("##### Estimate your savings")

    max_mw       = float(mine_cfg["available_heat_capacity_mw"])
    requested_mw = st.slider(
        "Heat capacity to secure (MWth)",
        min_value=0.5, max_value=max_mw,
        value=min(2.0, max_mw), step=0.5,
    )
    savings = config.calculate_commercial_savings(requested_mw)

    s1, s2 = st.columns(2)
    s1.metric("[R] Your estimated annual saving",        f"R {savings['annual_offtaker_savings_zar']:,.0f}")
    s2.metric("[R] Mine estimated annual revenue",       f"R {savings['annual_mine_revenue_zar']:,.0f}")

    st.markdown("---")
    st.markdown("##### Register interest")

    with st.form("express_interest_form"):
        name      = st.text_input("Company name")
        contact   = st.text_input("Contact email")
        submitted = st.form_submit_button("Submit expression of interest", use_container_width=True)
        if submitted:
            if name and contact:
                st.session_state.commercial_interests.append(
                    {"company": name, "contact": contact,
                     "heat_mw": requested_mw, "mine": selected_mine}
                )
                st.success(
                    f"Interest recorded for {requested_mw:.1f} MWth at {selected_mine}. "
                    "The team will be in touch."
                )
            else:
                st.error("Please provide both a company name and a contact email.")

    if st.session_state.commercial_interests:
        with st.expander(
            f"Submissions received ({len(st.session_state.commercial_interests)})"
        ):
            st.dataframe(
                pd.DataFrame(st.session_state.commercial_interests),
                use_container_width=True,
                hide_index=True,
            )


# =====================================================================
# TAB C — ABOUT (operator-facing, no judge internals)
# =====================================================================
def render_about() -> None:
    st.markdown("### About ThermalTwin")
    st.markdown(
        """
ThermalTwin sits between the mine and the surrounding community:

- **Underground Engine** — predicts dangerous heat 25-30 minutes ahead and uses the same physics
  baseline as a tamper-detection layer. Sensors under-reporting heat trigger the same alert as
  sensors approaching the statutory limit.
- **Surface Engine** — routes heat already being extracted to the surface toward commercial off-takers
  (Commercial Door) or community incubation projects (Community Door). Only heat — never mine water —
  crosses the fence line.
- **Privacy by design** — worker badge IDs are hashed one-way at the sensor before reaching this
  platform. The dashboard only ever sees an anonymous occupancy count per zone, not identities.

**Phase 1 (this build):** Driefontein, South Deep, Kusasalethu, Kloof — 2.5 km to 3.3 km depth,
closed-loop chilled service water cooling.

**Phase 2 (roadmap):** Mponeng, TauTona — greater than 3.3 km depth, melted ice-brine interface.
        """
    )

    with st.expander("Statutory and safety thresholds in use"):
        t1, t2, t3 = st.columns(3)
        t1.metric("MHSA wet-bulb limit",  f"{config.STATUTORY_WET_BULB_LIMIT} deg C")
        t2.metric("Caution threshold",    f"{config.WET_BULB_CAUTION_LIMIT} deg C")
        t3.metric("Prediction lead time", f"{config.PREDICTION_LEAD_TIME_MINUTES} min")

    with st.expander("Honest caveats"):
        st.markdown(
            """
- All telemetry in this build is **simulated**. The predicted baseline is a physics-grounded
  stand-in, not a trained ML model.
- The competitive claim that OT-security vendors underserve mid-tier SA mines is our assessment,
  not yet confirmed by an industry source.
- Cross-sensor spatial validation (comparing adjacent RTD probes) is implemented in the engine
  but not yet surfaced in this dashboard view.
            """
        )


# =====================================================================
# OPERATOR DASHBOARD SHELL
# =====================================================================
def render_operator_dashboard() -> None:
    selected_mine = _render_sidebar()

    st.title("ThermalTwin — Operator Dashboard")

    p1 = config.STAGING_CONFIG["Phase 1"]
    p2 = config.STAGING_CONFIG["Phase 2"]
    st.markdown(
        f"""
        <div style="background:#EFF6FF; border:1px solid #BFDBFE;
        border-left:3px solid #2563EB; padding:8px 16px; border-radius:4px;
        font-size:0.83rem; margin-bottom:12px; display:flex;
        flex-wrap:wrap; justify-content:space-between; gap:6px;">
          <span style="color:#1D4ED8; font-weight:600;">
            [+] {p1['name']} &nbsp;|&nbsp; {p1['depth_band']} &nbsp;|&nbsp;
            {', '.join(p1['mines'])}
          </span>
          <span style="color:#64748B;">
            [-] {p2['name']} &nbsp;|&nbsp; {p2['depth_band']} &nbsp;|&nbsp;
            {', '.join(p2['mines'])} (roadmap)
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_status_header(selected_mine)
    st.markdown("---")

    tab_ug, tab_comm, tab_about = st.tabs([
        "[>] Underground Engine",
        "[+] Commercial Door",
        "[i] About",
    ])

    with tab_ug:
        render_underground_engine(selected_mine)
    with tab_comm:
        render_commercial_door(selected_mine)
    with tab_about:
        render_about()


# =====================================================================
# MAIN ROUTER
# =====================================================================
def main() -> None:
    inject_theme()
    _init_state()

    role          = st.session_state.role
    authenticated = st.session_state.authenticated

    if role is None:
        render_landing()

    elif role == "community":
        render_community_portal()

    elif role == "operator" and not authenticated:
        render_login()

    elif role == "operator" and authenticated:
        render_operator_dashboard()


if __name__ == "__main__":
    main()
