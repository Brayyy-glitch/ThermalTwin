# -*- coding: utf-8 -*-
"""
ThermalTwin (MineFlow AI) — Dashboard & Integration
====================================================
Role-based access:
  - Mining Business / Manager  → all 4 tabs (Underground + Commercial + Community + About)
  - Mining Business / Operator → Underground Engine + About only
  - Community Member           → Community Door only (simplified, accessible view)

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
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# 1. USER STORE  (demo-only, in-memory — replace with a DB in production)
# =====================================================================
# Structure: { email: { password, name, account_type, role } }
# account_type: "mining" | "community"
# role (mining only): "manager" | "operator"
DEMO_USERS: dict = {
    "manager@thermaltwin.co.za": {
        "password": "manager123",
        "name": "Thabo Nkosi",
        "account_type": "mining",
        "role": "manager",
        "mine": "Driefontein",
    },
    "operator@thermaltwin.co.za": {
        "password": "operator123",
        "name": "Lerato Dlamini",
        "account_type": "mining",
        "role": "operator",
        "mine": "Driefontein",
    },
    "community@merafong.co.za": {
        "password": "community123",
        "name": "Nompumelelo Sithole",
        "account_type": "community",
        "role": "community",
        "mine": None,
    },
}

# =====================================================================
# 2. MULTILINGUAL STRING TABLE (Community Door)
# =====================================================================
LANG_STRINGS: dict = {
    "English": {
        "community_tab_title": "🌱 Community Door",
        "community_intro": "Opportunities for local youth, women, and persons with disabilities. No experience needed — just your name.",
        "step1_heading": "What would you like to do?",
        "step1_subtext": "Tap a picture to learn more.",
        "step2_heading": "About this opportunity",
        "step2_back": "← Back",
        "step2_apply": "Apply — 1 step",
        "step3_heading": "You're in! ✅",
        "step3_subtext": "We will call or WhatsApp you within 3 days.",
        "step3_another": "Apply for another opportunity",
        "label_jobs": "Jobs created",
        "label_heat": "Free heat",
        "label_temp": "Water temp",
        "label_focus": "Who is this for?",
        "label_slp": "Community benefit",
        "name_placeholder": "Your name",
        "name_label": "Enter your name to apply",
        "whatsapp_label": "Need help? WhatsApp or call:",
        "whatsapp_number": "+27 18 788 1234",
        "whatsapp_contact": "Sifiso (Community Desk, Merafong)",
        "offline_note": "📶 This page works on slow data. No videos or heavy images.",
        "before_label": "Before",
        "after_label": "After (free heat)",
        "listen_tooltip": "Listen",
    },
    "isiZulu": {
        "community_tab_title": "🌱 Umnyango Womphakathi",
        "community_intro": "Amathuba abantu abasha bendawo, abesifazane, nabantu abakhubazekile. Asidingeki ulwazi — igama lakho kuphela.",
        "step1_heading": "Ufuna ukwenzani?",
        "step1_subtext": "Thepha isithombe ukuze ufunde okwengeziwe.",
        "step2_heading": "Mayelana naleli thuba",
        "step2_back": "← Emuva",
        "step2_apply": "Faka isicelo — isinyathelo esisodwa",
        "step3_heading": "Ukuqalisile! ✅",
        "step3_subtext": "Sizokunxibelelana nge-WhatsApp noma sikuncinzele ngezinsuku ezi-3.",
        "step3_another": "Faka isicelo sokunye ithuba",
        "label_jobs": "Imisebenzi",
        "label_heat": "Ukufudumala kwamahhala",
        "label_temp": "Ukushisa kwamanzi",
        "label_focus": "Ngubani lo?",
        "label_slp": "Inzuzo yomphakathi",
        "name_placeholder": "Igama lakho",
        "name_label": "Faka igama lakho ukuze wenze isicelo",
        "whatsapp_label": "Udinga usizo? WhatsApp noma shayela:",
        "whatsapp_number": "+27 18 788 1234",
        "whatsapp_contact": "USifiso (Idesiki Lomphakathi, Merafong)",
        "offline_note": "📶 Lekhasi lisebenza ngisho nangedatha engolangolanyo.",
        "before_label": "Ngaphambi",
        "after_label": "Ngemuva (ukufudumala kwamahhala)",
        "listen_tooltip": "Lalela",
    },
    "Setswana": {
        "community_tab_title": "🌱 Kgoro ya Setšhaba",
        "community_intro": "Ditšhono tsa basha ba lefelo, basadi, le batho ba nang le bogole. Ga go a tlhokagala maitemogelo — leina la gago fela.",
        "step1_heading": "O batla go dira eng?",
        "step1_subtext": "Kgofa setshwantsho go ithuta go feta.",
        "step2_heading": "Ka ga tšhono eno",
        "step2_back": "← Boela morago",
        "step2_apply": "Kopa — ga le lengwe",
        "step3_heading": "O simologile! ✅",
        "step3_subtext": "Re tla go letsetsa kgotsa go romela WhatsApp mo malatsing a 3.",
        "step3_another": "Kopa tšhono e nngwe",
        "label_jobs": "Ditiro tse dirilweng",
        "label_heat": "Bothitho jo bo sa duelelweng",
        "label_temp": "Botshelo jwa metsi",
        "label_focus": "Ke mang ono?",
        "label_slp": "Molemo wa setšhaba",
        "name_placeholder": "Leina la gago",
        "name_label": "Tsenya leina la gago go kopa",
        "whatsapp_label": "Tlhoka thuso? WhatsApp kgotsa letsetsa:",
        "whatsapp_number": "+27 18 788 1234",
        "whatsapp_contact": "Sifiso (Tafole ya Setšhaba, Merafong)",
        "offline_note": "📶 Tsebe eno e a dira le mo go simologileng data.",
        "before_label": "Pele",
        "after_label": "Morago (bothitho jo bo sa duelelweng)",
        "listen_tooltip": "Reetsa",
    },
    "Afrikaans": {
        "community_tab_title": "🌱 Gemeenskapsdeur",
        "community_intro": "Geleenthede vir plaaslike jeug, vroue, en mense met gestremdhede. Geen ondervinding nodig — net jou naam.",
        "step1_heading": "Wat wil jy doen?",
        "step1_subtext": "Tik op 'n prent om meer te leer.",
        "step2_heading": "Oor hierdie geleentheid",
        "step2_back": "← Terug",
        "step2_apply": "Doen aansoek — 1 stap",
        "step3_heading": "Jy's ingeskryf! ✅",
        "step3_subtext": "Ons sal jou binne 3 dae bel of WhatsApp.",
        "step3_another": "Doen aansoek vir 'n ander geleentheid",
        "label_jobs": "Werk geskep",
        "label_heat": "Gratis hitte",
        "label_temp": "Water temp",
        "label_focus": "Vir wie is dit?",
        "label_slp": "Gemeenskapsvoordeel",
        "name_placeholder": "Jou naam",
        "name_label": "Voer jou naam in om aansoek te doen",
        "whatsapp_label": "Hulp nodig? WhatsApp of bel:",
        "whatsapp_number": "+27 18 788 1234",
        "whatsapp_contact": "Sifiso (Gemeenskapstafel, Merafong)",
        "offline_note": "📶 Hierdie bladsy werk op stadige data. Geen videos of swaar beelde nie.",
        "before_label": "Voor",
        "after_label": "Na (gratis hitte)",
        "listen_tooltip": "Luister",
    },
}

CARD_META: dict = {
    "merafong_hydroponics": {
        "icon": "🥬",
        "benefit_en": "Grow vegetables all year — no winter heating bill.",
        "benefit_zu": "Ukukhula kwemifino unyaka wonke — ngaphandle kwezindleko zokufudumeza.",
        "benefit_tn": "Godisa merogo ka mokgabo wotlhe — ga go na tefelo ya bothitho.",
        "benefit_af": "Groente die hele jaar — geen verwarmingsrekening nie.",
        "color": "#16A34A",
        "bg": "#F0FDF4",
        "border": "#BBF7D0",
    },
    "tilapia_aquaculture": {
        "icon": "🐟",
        "benefit_en": "Farm fish in warm water — no fuel needed.",
        "benefit_zu": "Ukufuya izinhlanzi emanzini afudumele — ngaphandle kwamafutha.",
        "benefit_tn": "Allela ditlhapi mo metsing a bothitho — ga go a tlhokagala metsi a mafutha.",
        "benefit_af": "Teelvis in warm water — geen brandstof nodig nie.",
        "color": "#0369A1",
        "bg": "#F0F9FF",
        "border": "#BAE6FD",
    },
    "post_harvest_drying": {
        "icon": "🌾",
        "benefit_en": "Dry your harvest with free heat — stop food going to waste.",
        "benefit_zu": "Omisa isivuno sakho ngokufudumala kwamahhala — misa ukuchithwa kokudla.",
        "benefit_tn": "Omisa selelo sa gago ka bothitho jo bo sa duelelweng — emisa dijo go senyiwa.",
        "benefit_af": "Droog jou oes met gratis hitte — stop voedselvermorsing.",
        "color": "#B45309",
        "bg": "#FFFBEB",
        "border": "#FDE68A",
    },
    "sanitation_laundry": {
        "icon": "🧺",
        "benefit_en": "Hot water for laundry and clinics — no coal, no paraffin.",
        "benefit_zu": "Amanzi ashisayo okuhlanza namakhliniki — ngaphandle komalahle, ngaphandle kwe-paraffin.",
        "benefit_tn": "Metsi a bothitho a go tlhapa le dikiliniki — ga go makhala, ga go paraffin.",
        "benefit_af": "Warm water vir wasserye en klinieke — geen steenkool, geen paraffien nie.",
        "color": "#7C3AED",
        "bg": "#FAF5FF",
        "border": "#DDD6FE",
    },
}

# =====================================================================
# 3. THEME  —  bright light mode, vivid accent colours
# =====================================================================
def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        /* ── Colour tokens ── */
        :root {
          --bg:          #F8FAFC;
          --surface:     #FFFFFF;
          --card:        #FFFFFF;
          --border:      #E2E8F0;
          --border-hi:   #CBD5E1;

          --text:        #0F172A;
          --text-sec:    #475569;
          --muted:       #94A3B8;

          /* Vivid brand palette */
          --orange:      #EA580C;
          --orange-lo:   #FFF7ED;
          --orange-mid:  #FED7AA;
          --teal:        #0D9488;
          --teal-lo:     #F0FDFA;
          --teal-mid:    #99F6E4;
          --green:       #16A34A;
          --green-lo:    #F0FDF4;
          --green-mid:   #BBF7D0;
          --red:         #DC2626;
          --red-lo:      #FEF2F2;
          --blue:        #2563EB;
          --blue-lo:     #EFF6FF;
          --purple:      #7C3AED;
          --purple-lo:   #FAF5FF;
          --amber:       #D97706;
          --amber-lo:    #FFFBEB;

          --r-sm:  6px;
          --r-md:  10px;
          --r-lg:  16px;
          --r-xl:  24px;
          --shadow-sm: 0 1px 3px rgba(15,23,42,0.08), 0 1px 2px rgba(15,23,42,0.06);
          --shadow-md: 0 4px 12px rgba(15,23,42,0.10), 0 2px 4px rgba(15,23,42,0.06);
          --shadow-lg: 0 10px 30px rgba(15,23,42,0.12), 0 4px 8px rgba(15,23,42,0.06);

          --cd-icon-size: 3.2rem;
          --cd-radius:    14px;
          --cd-touch-min: 52px;
        }

        /* ── Reset & base ── */
        html, body, [class*="css"] {
          font-family: 'Plus Jakarta Sans', sans-serif !important;
          color: var(--text) !important;
          font-size: 15px;
          line-height: 1.65;
        }
        .stApp { background-color: var(--bg) !important; }

        /* ── Headings ── */
        h1,h2,h3,h4,
        .stMarkdown h1,.stMarkdown h2,.stMarkdown h3,.stMarkdown h4 {
          font-family: 'Space Grotesk', sans-serif !important;
          font-weight: 700 !important;
          color: var(--text) !important;
          letter-spacing: -0.015em;
          line-height: 1.2 !important;
        }
        h1,.stMarkdown h1 { font-size: 2rem !important; }
        h2,.stMarkdown h2 { font-size: 1.5rem !important; }
        h3,.stMarkdown h3 { font-size: 1.15rem !important; }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
          background-color: var(--surface) !important;
          border-right: 1px solid var(--border) !important;
        }
        [data-testid="stSidebar"] * { color: var(--text) !important; }

        /* ── Metric cards ── */
        [data-testid="stMetric"] {
          background: var(--surface);
          border: 1px solid var(--border);
          border-top: 3px solid var(--orange);
          border-radius: var(--r-md);
          padding: 18px 20px 14px;
          box-shadow: var(--shadow-sm);
          transition: box-shadow 0.2s, border-top-color 0.2s;
        }
        [data-testid="stMetric"]:hover {
          box-shadow: var(--shadow-md);
          border-top-color: var(--teal);
        }
        [data-testid="stMetricValue"] {
          font-family: 'JetBrains Mono', monospace !important;
          font-size: 1.6rem !important;
          font-weight: 600 !important;
          color: var(--text) !important;
        }
        [data-testid="stMetricLabel"] {
          font-size: 0.72rem !important;
          font-weight: 700 !important;
          text-transform: uppercase !important;
          letter-spacing: 0.07em !important;
          color: var(--muted) !important;
        }

        /* ── Containers / cards ── */
        [data-testid="stVerticalBlockBorderWrapper"] {
          background: var(--surface) !important;
          border: 1px solid var(--border) !important;
          border-radius: var(--r-md) !important;
          box-shadow: var(--shadow-sm) !important;
        }

        /* ── Forms & inputs ── */
        [data-testid="stForm"] { background: transparent; border: none; padding: 0; }
        .stTextInput input, .stTextInput textarea {
          background: var(--surface) !important;
          border: 1.5px solid var(--border-hi) !important;
          border-radius: var(--r-sm) !important;
          color: var(--text) !important;
          font-family: 'Plus Jakarta Sans', sans-serif !important;
          font-size: 0.95rem !important;
          padding: 10px 14px !important;
          transition: border-color 0.18s, box-shadow 0.18s !important;
        }
        .stTextInput input:focus, .stTextInput textarea:focus {
          border-color: var(--teal) !important;
          box-shadow: 0 0 0 3px rgba(13,148,136,0.12) !important;
          outline: none !important;
        }
        .stSelectbox [data-baseweb="select"] > div {
          background: var(--surface) !important;
          border: 1.5px solid var(--border-hi) !important;
          border-radius: var(--r-sm) !important;
          color: var(--text) !important;
        }
        .stRadio label, .stCheckbox label { color: var(--text) !important; font-size: 0.95rem !important; }

        /* ── Primary button (teal) ── */
        .stButton > button {
          font-family: 'Plus Jakarta Sans', sans-serif !important;
          font-weight: 700 !important;
          font-size: 0.9rem !important;
          background-color: var(--teal) !important;
          color: #ffffff !important;
          border: none !important;
          border-radius: var(--r-sm) !important;
          padding: 10px 22px !important;
          letter-spacing: 0.02em !important;
          box-shadow: 0 2px 8px rgba(13,148,136,0.22) !important;
          transition: background-color 0.18s, box-shadow 0.18s, transform 0.1s !important;
        }
        .stButton > button:hover {
          background-color: #0F766E !important;
          box-shadow: 0 4px 16px rgba(13,148,136,0.32) !important;
          transform: translateY(-1px) !important;
        }
        .stButton > button:active { transform: translateY(0) !important; }

        .stFormSubmitButton > button {
          font-family: 'Plus Jakarta Sans', sans-serif !important;
          font-weight: 700 !important;
          font-size: 0.95rem !important;
          background-color: var(--teal) !important;
          color: #ffffff !important;
          border: none !important;
          border-radius: var(--r-sm) !important;
          padding: 11px 24px !important;
          width: 100% !important;
          letter-spacing: 0.03em !important;
          box-shadow: 0 2px 8px rgba(13,148,136,0.22) !important;
          transition: background-color 0.18s, box-shadow 0.18s, transform 0.1s !important;
        }
        .stFormSubmitButton > button:hover {
          background-color: #0F766E !important;
          box-shadow: 0 4px 16px rgba(13,148,136,0.32) !important;
          transform: translateY(-1px) !important;
        }

        /* ── Tabs ── */
        [data-testid="stTabs"] { border-bottom: 2px solid var(--border); margin-bottom: 4px; }
        [data-testid="stTabs"] button {
          font-family: 'Plus Jakarta Sans', sans-serif !important;
          font-weight: 600 !important;
          font-size: 0.88rem !important;
          color: var(--muted) !important;
          padding: 10px 18px !important;
          border-radius: var(--r-sm) var(--r-sm) 0 0 !important;
          transition: color 0.15s !important;
        }
        [data-testid="stTabs"] button:hover { color: var(--text-sec) !important; }
        [data-testid="stTabs"] button[aria-selected="true"] {
          color: var(--orange) !important;
          border-bottom: 2px solid var(--orange) !important;
          background-color: var(--orange-lo) !important;
        }

        /* ── Dataframe ── */
        .stDataFrame {
          border: 1px solid var(--border) !important;
          border-radius: var(--r-md) !important;
          overflow: hidden !important;
          box-shadow: var(--shadow-sm) !important;
        }

        /* ── Alerts ── */
        .stAlert { border-radius: var(--r-md) !important; font-size: 0.92rem !important; }

        /* ── Expander ── */
        [data-testid="stExpander"] {
          border: 1px solid var(--border) !important;
          border-radius: var(--r-md) !important;
          background: var(--surface) !important;
          box-shadow: var(--shadow-sm) !important;
        }
        [data-testid="stExpander"] summary {
          font-weight: 600 !important;
          color: var(--text-sec) !important;
          font-size: 0.9rem !important;
        }

        /* ── Code ── */
        code, pre { font-family: 'JetBrains Mono', monospace !important; font-size: 0.82rem !important; }

        /* ── HR ── */
        hr { border-color: var(--border) !important; margin: 20px 0 !important; }

        /* ─────────────────────────────────────────
           CAPACITY GAUGE BAR
        ───────────────────────────────────────── */
        .tt-gauge-wrap {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: var(--r-md);
          padding: 14px 18px;
          box-shadow: var(--shadow-sm);
          margin-top: 6px;
        }
        .tt-gauge-track {
          width: 100%; height: 18px;
          background: #F1F5F9;
          border-radius: 99px;
          overflow: hidden;
          display: flex;
          margin: 8px 0 6px;
          border: 1px solid var(--border);
        }
        .tt-gauge-community {
          background: linear-gradient(90deg, #16A34A, #22C55E);
          height: 100%; border-radius: 99px 0 0 99px;
        }
        .tt-gauge-commercial {
          background: linear-gradient(90deg, #0D9488, #14B8A6);
          height: 100%;
        }
        .tt-gauge-caption {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.76rem;
          color: var(--muted);
          display: flex;
          justify-content: space-between;
        }

        /* ─────────────────────────────────────────
           STAGING BANNER
        ───────────────────────────────────────── */
        .tt-staging-banner {
          background: #F0FDF4;
          border: 1px solid #BBF7D0;
          border-left: 4px solid #16A34A;
          padding: 10px 18px;
          border-radius: var(--r-sm);
          display: flex;
          flex-wrap: wrap;
          justify-content: space-between;
          gap: 8px;
          margin-bottom: 18px;
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.78rem;
        }

        /* ─────────────────────────────────────────
           SCREEN SECTION HEADINGS
        ───────────────────────────────────────── */
        .tt-screen-heading {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 14px;
          padding-bottom: 10px;
          border-bottom: 1px solid var(--border);
        }
        .tt-screen-title {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 1.45rem;
          font-weight: 800;
          color: var(--text);
          letter-spacing: -0.02em;
        }
        .tt-badge {
          font-size: 0.72rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.07em;
          padding: 3px 10px;
          border-radius: 99px;
        }
        .tt-badge-orange { background: var(--orange-lo); color: var(--orange); }
        .tt-badge-teal   { background: var(--teal-lo);   color: var(--teal);   }
        .tt-badge-green  { background: var(--green-lo);  color: var(--green);  }

        /* ─────────────────────────────────────────
           LOGIN / REGISTER SCREEN
        ───────────────────────────────────────── */
        .auth-hero {
          text-align: center;
          padding: 32px 24px 20px;
        }
        .auth-logo { font-size: 3.5rem; }
        .auth-title {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 2rem;
          font-weight: 800;
          color: var(--text);
          letter-spacing: -0.025em;
          margin: 8px 0 4px;
        }
        .auth-sub { color: var(--text-sec); font-size: 0.95rem; }

        .auth-card {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: var(--r-xl);
          padding: 32px 36px;
          box-shadow: var(--shadow-lg);
          max-width: 480px;
          margin: 0 auto;
        }

        .account-type-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 22px 14px;
          border-radius: var(--r-lg);
          cursor: pointer;
          transition: all 0.18s;
          text-align: center;
          min-height: 120px;
        }
        .account-type-btn.mining {
          background: var(--orange-lo);
          border: 2px solid var(--orange-mid);
        }
        .account-type-btn.mining:hover, .account-type-btn.mining.selected {
          border-color: var(--orange);
          box-shadow: 0 0 0 3px rgba(234,88,12,0.12);
        }
        .account-type-btn.community {
          background: var(--green-lo);
          border: 2px solid var(--green-mid);
        }
        .account-type-btn.community:hover, .account-type-btn.community.selected {
          border-color: var(--green);
          box-shadow: 0 0 0 3px rgba(22,163,74,0.12);
        }
        .account-type-icon { font-size: 2.2rem; }
        .account-type-label {
          font-family: 'Space Grotesk', sans-serif;
          font-weight: 700;
          font-size: 1rem;
          color: var(--text);
        }
        .account-type-sub { font-size: 0.8rem; color: var(--text-sec); }

        /* ─────────────────────────────────────────
           ROLE BADGE (sidebar)
        ───────────────────────────────────────── */
        .sidebar-user-card {
          background: var(--bg);
          border: 1px solid var(--border);
          border-radius: var(--r-md);
          padding: 12px 14px;
          margin-bottom: 16px;
        }
        .sidebar-user-name {
          font-weight: 700;
          font-size: 0.95rem;
          color: var(--text);
        }
        .sidebar-user-role {
          font-size: 0.76rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          margin-top: 4px;
        }
        .role-manager  { color: var(--orange); }
        .role-operator { color: var(--teal); }
        .role-community{ color: var(--green); }

        /* ─────────────────────────────────────────
           COMMUNITY DOOR
        ───────────────────────────────────────── */
        .cd-pick-card {
          background: var(--surface);
          border: 2px solid var(--border);
          border-radius: var(--cd-radius);
          padding: 26px 14px 20px;
          text-align: center;
          min-height: 185px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-bottom: 4px;
          transition: border-color 0.18s, box-shadow 0.18s, transform 0.15s;
          box-shadow: var(--shadow-sm);
        }
        .cd-pick-card:hover {
          border-color: var(--orange);
          box-shadow: var(--shadow-md);
          transform: translateY(-3px);
        }
        .cd-pick-icon { font-size: var(--cd-icon-size); line-height: 1; }
        .cd-pick-label {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 1rem;
          font-weight: 700;
          color: var(--text);
        }
        .cd-pick-sublabel { font-size: 0.83rem; color: var(--text-sec); line-height: 1.4; }

        .cd-pick-btn > button {
          min-height: var(--cd-touch-min) !important;
          font-size: 0.95rem !important;
          font-weight: 700 !important;
          width: 100% !important;
          border-radius: var(--r-sm) !important;
          background: var(--surface) !important;
          color: var(--text) !important;
          border: 1.5px solid var(--border-hi) !important;
          box-shadow: var(--shadow-sm) !important;
          transition: border-color 0.15s, color 0.15s !important;
        }
        .cd-pick-btn > button:hover {
          border-color: var(--orange) !important;
          color: var(--orange) !important;
          transform: none !important;
          box-shadow: 0 0 0 3px rgba(234,88,12,0.1) !important;
        }

        .cd-apply-btn > button {
          min-height: var(--cd-touch-min) !important;
          font-size: 1.05rem !important;
          font-weight: 800 !important;
          width: 100% !important;
          border-radius: var(--r-md) !important;
          background-color: var(--green) !important;
          color: #ffffff !important;
          border: none !important;
          box-shadow: 0 4px 14px rgba(22,163,74,0.28) !important;
          letter-spacing: 0.03em !important;
        }
        .cd-apply-btn > button:hover {
          background-color: #15803D !important;
          box-shadow: 0 6px 20px rgba(22,163,74,0.36) !important;
          transform: translateY(-2px) !important;
        }

        .cd-back-btn > button {
          min-height: 44px !important;
          background: transparent !important;
          color: var(--text-sec) !important;
          border: 1px solid var(--border) !important;
          border-radius: var(--r-sm) !important;
          font-size: 0.9rem !important;
          box-shadow: none !important;
        }
        .cd-back-btn > button:hover {
          border-color: var(--border-hi) !important;
          color: var(--text) !important;
          background: var(--bg) !important;
          transform: none !important;
          box-shadow: none !important;
        }

        .cd-bar-row { display: flex; align-items: center; gap: 10px; margin: 5px 0; }
        .cd-bar-label { color: var(--muted); min-width: 72px; font-size: 0.78rem; }
        .cd-bar-track {
          flex: 1; height: 11px;
          background: #F1F5F9;
          border-radius: 99px;
          overflow: hidden;
          border: 1px solid var(--border);
        }
        .cd-bar-fill { height: 100%; border-radius: 99px; }
        .cd-bar-value {
          min-width: 52px; text-align: right;
          font-size: 0.78rem;
          color: var(--text-sec);
          font-family: 'JetBrains Mono', monospace;
        }

        .cd-whatsapp-strip {
          background: #F0FDF4;
          border: 1px solid #BBF7D0;
          border-left: 4px solid #25D366;
          border-radius: var(--r-md);
          padding: 14px 18px;
          display: flex;
          align-items: center;
          gap: 14px;
          margin: 16px 0 8px;
          box-shadow: var(--shadow-sm);
        }
        .cd-whatsapp-icon { font-size: 1.8rem; flex-shrink: 0; }
        .cd-whatsapp-number { font-weight: 800; color: #16A34A; font-size: 1.1rem; }
        .cd-whatsapp-name { color: var(--text-sec); font-size: 0.84rem; margin-top: 2px; }

        .cd-offline-note {
          background: #FAFAFA;
          border: 1px solid var(--border);
          border-radius: var(--r-sm);
          padding: 8px 14px;
          font-size: 0.8rem;
          color: var(--muted);
          margin-bottom: 10px;
        }

        .cd-success-box {
          background: var(--green-lo);
          border: 2px solid var(--green-mid);
          border-radius: var(--r-xl);
          padding: 40px 32px;
          text-align: center;
          box-shadow: var(--shadow-md);
        }
        .cd-success-icon { font-size: 4rem; }
        .cd-success-heading {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 2rem;
          font-weight: 800;
          color: var(--green);
          margin: 12px 0 6px;
          letter-spacing: -0.02em;
        }
        .cd-success-sub { color: var(--text-sec); font-size: 1rem; line-height: 1.6; }

        .cd-step-indicator { display: flex; align-items: center; margin-bottom: 22px; }
        .cd-step-dot {
          width: 28px; height: 28px; border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          font-size: 0.75rem; font-weight: 700; flex-shrink: 0;
        }
        .cd-step-dot.active { background: var(--orange); color: #fff; }
        .cd-step-dot.done   { background: var(--green);  color: #fff; }
        .cd-step-dot.idle   { background: var(--border); color: var(--muted); }
        .cd-step-line { flex: 1; height: 2px; background: var(--border); margin: 0 4px; }
        .cd-step-line.done { background: var(--green); }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# 4. SESSION STATE
# =====================================================================
def _init_session() -> None:
    defaults = {
        "authenticated": False,
        "user": None,                  # dict from DEMO_USERS
        "auth_mode": "login",          # "login" | "register"
        "reg_account_type": None,      # "mining" | "community"
        "tamper_active": False,
        "tamper_mode": config.SIGNATURE_JUMP,
        "commercial_interests": [],
        "community_applications": [],
        "telemetry_cache": {},
        "cd_language": "English",
        "cd_step": "pick",
        "cd_selected_card_id": None,
        "cd_applicant_name": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_session()


# =====================================================================
# 5. HELPERS
# =====================================================================
def t(key: str) -> str:
    lang = st.session_state.get("cd_language", "English")
    return LANG_STRINGS.get(lang, LANG_STRINGS["English"]).get(
        key, LANG_STRINGS["English"].get(key, key)
    )

def card_benefit(card_id: str) -> str:
    lang = st.session_state.get("cd_language", "English")
    meta = CARD_META.get(card_id, {})
    mapping = {"English": "benefit_en", "isiZulu": "benefit_zu",
               "Setswana": "benefit_tn", "Afrikaans": "benefit_af"}
    return meta.get(mapping.get(lang, "benefit_en"), meta.get("benefit_en", ""))

def current_role() -> str:
    u = st.session_state.user
    return u["role"] if u else ""

def is_manager()  -> bool: return current_role() == "manager"
def is_operator() -> bool: return current_role() == "operator"
def is_community()-> bool: return current_role() == "community"

def listen_button(text_to_speak: str, key: str) -> None:
    import streamlit.components.v1 as components
    lang_code_map = {"English": "en-ZA", "isiZulu": "zu-ZA",
                     "Setswana": "tn-ZA", "Afrikaans": "af-ZA"}
    lang_code = lang_code_map.get(st.session_state.get("cd_language", "English"), "en-ZA")
    safe = text_to_speak.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
    components.html(
        f"""<button onclick="if('speechSynthesis' in window){{
          var u=new SpeechSynthesisUtterance('{safe}');
          u.lang='{lang_code}';
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(u);
        }}" style="display:inline-flex;align-items:center;gap:5px;
          background:#F8FAFC;border:1px solid #E2E8F0;border-radius:99px;
          padding:4px 12px 4px 10px;font-size:0.8rem;color:#475569;
          cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif;">
          🔊 {t('listen_tooltip')}
        </button>""",
        height=38,
    )

def whatsapp_strip() -> None:
    st.markdown(
        f"""<div class="cd-whatsapp-strip">
          <span class="cd-whatsapp-icon">💬</span>
          <div>
            <div style="font-size:0.82rem;color:#475569;">{t('whatsapp_label')}</div>
            <div class="cd-whatsapp-number">{t('whatsapp_number')}</div>
            <div class="cd-whatsapp-name">{t('whatsapp_contact')}</div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

def offline_note() -> None:
    st.markdown(
        f'<div class="cd-offline-note">{t("offline_note")}</div>',
        unsafe_allow_html=True,
    )

def jobs_bar(jobs_count_str: str, color: str) -> None:
    import re
    match = re.search(r"\d+", jobs_count_str)
    jobs_num = int(match.group()) if match else 10
    pct = min(100, int(jobs_num / 60 * 100))
    st.markdown(
        f"""<div style="margin:10px 0 6px;">
          <div style="font-size:0.78rem;color:#94A3B8;margin-bottom:4px;">{t('label_jobs')}</div>
          <div class="cd-bar-row">
            <span class="cd-bar-label">{t('before_label')}</span>
            <div class="cd-bar-track"><div class="cd-bar-fill" style="width:2%;background:#E2E8F0;"></div></div>
            <span class="cd-bar-value">0</span>
          </div>
          <div class="cd-bar-row">
            <span class="cd-bar-label">{t('after_label')}</span>
            <div class="cd-bar-track"><div class="cd-bar-fill" style="width:{pct}%;background:{color};"></div></div>
            <span class="cd-bar-value">{jobs_count_str.split(',')[0]}</span>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

def heat_bar(allocated_mw: float, total_mw: float, color: str) -> None:
    pct = min(100, int(allocated_mw / total_mw * 100))
    st.markdown(
        f"""<div style="margin:10px 0 6px;">
          <div style="font-size:0.78rem;color:#94A3B8;margin-bottom:4px;">{t('label_heat')}</div>
          <div class="cd-bar-row">
            <span class="cd-bar-label">{t('before_label')}</span>
            <div class="cd-bar-track"><div class="cd-bar-fill" style="width:2%;background:#E2E8F0;"></div></div>
            <span class="cd-bar-value">R0</span>
          </div>
          <div class="cd-bar-row">
            <span class="cd-bar-label">{t('after_label')}</span>
            <div class="cd-bar-track"><div class="cd-bar-fill" style="width:{pct}%;background:{color};"></div></div>
            <span class="cd-bar-value">{allocated_mw} MW</span>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

def screen_heading(icon: str, title: str, badge: str, badge_cls: str) -> None:
    st.markdown(
        f"""<div class="tt-screen-heading">
          <span class="tt-screen-title">{icon} {title}</span>
          <span class="tt-badge {badge_cls}">{badge}</span>
        </div>""",
        unsafe_allow_html=True,
    )


# =====================================================================
# 6. LOGIN & REGISTER SCREENS
# =====================================================================
def render_auth() -> None:
    """Full-page auth gate shown when user is not logged in."""
    # centre the form with empty columns
    _, mid, _ = st.columns([1, 2, 1])

    with mid:
        st.markdown(
            """<div class="auth-hero">
              <div class="auth-logo">🌡️</div>
              <div class="auth-title">ThermalTwin</div>
              <div class="auth-sub">MineFlow AI &nbsp;·&nbsp; Mine heat, redirected to the community</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Toggle login / register
        col_l, col_r = st.columns(2)
        if col_l.button("Sign In", use_container_width=True,
                        type="primary" if st.session_state.auth_mode == "login" else "secondary"):
            st.session_state.auth_mode = "login"
            st.rerun()
        if col_r.button("Create Account", use_container_width=True,
                        type="primary" if st.session_state.auth_mode == "register" else "secondary"):
            st.session_state.auth_mode = "register"
            st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        if st.session_state.auth_mode == "login":
            _render_login_form()
        else:
            _render_register_form()

        # ── Guest access — community door only, no credentials needed ──
        st.markdown(
            """<div style="text-align:center;margin:18px 0 4px;">
              <span style="font-size:0.85rem;color:#94A3B8;">
                Looking for community opportunities?
              </span>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button(
            "🌱 Continue as Guest — Community Door only",
            use_container_width=True,
            key="guest_btn",
        ):
            guest = {
                "email": "guest",
                "name": "Community Guest",
                "account_type": "community",
                "role": "community",
                "mine": None,
                "password": "",
            }
            st.session_state.authenticated = True
            st.session_state.user = guest
            st.rerun()

        st.markdown(
            """<div style="text-align:center;margin:4px 0 10px;">
              <span style="font-size:0.78rem;color:#CBD5E1;">
                No account needed · Community opportunities only · No mine data shown
              </span>
            </div>""",
            unsafe_allow_html=True,
        )

        # Demo credentials hint
        with st.expander("🔑 Demo credentials (hackathon)"):
            st.markdown(
                """
| Role | Email | Password |
|---|---|---|
| Mine Manager | manager@thermaltwin.co.za | manager123 |
| Mine Operator | operator@thermaltwin.co.za | operator123 |
| Community Member | community@merafong.co.za | community123 |
                """
            )


def _render_login_form() -> None:
    with st.form("login_form"):
        st.markdown("#### Sign in to your account")
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Sign In →", use_container_width=True)

    if submitted:
        user = DEMO_USERS.get(email.strip().lower())
        if user and user["password"] == password:
            st.session_state.authenticated = True
            st.session_state.user = {**user, "email": email.strip().lower()}
            st.rerun()
        else:
            st.error("Incorrect email or password. Check the demo credentials below.")


def _render_register_form() -> None:
    """
    Registration flow:
      Step A — choose account type (Mining Business or Community Member)
      Step B — fill in details
    """
    st.markdown("#### Create your account")

    # ---- Step A: account type picker ----
    if st.session_state.reg_account_type is None:
        st.markdown(
            "<p style='color:#475569;font-size:0.9rem;margin-bottom:12px;'>"
            "Who are you joining as?</p>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                """<div class="account-type-btn mining">
                  <span class="account-type-icon">⛏️</span>
                  <span class="account-type-label">Mining Business</span>
                  <span class="account-type-sub">Managers & operators at a mine site</span>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button("Select — Mining Business", use_container_width=True, key="pick_mining"):
                st.session_state.reg_account_type = "mining"
                st.rerun()
        with c2:
            st.markdown(
                """<div class="account-type-btn community">
                  <span class="account-type-icon">🌱</span>
                  <span class="account-type-label">Community Member</span>
                  <span class="account-type-sub">Local residents & entrepreneurs</span>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button("Select — Community Member", use_container_width=True, key="pick_community"):
                st.session_state.reg_account_type = "community"
                st.rerun()
        return

    # ---- Step B: fill in details ----
    acct = st.session_state.reg_account_type
    icon = "⛏️" if acct == "mining" else "🌱"
    label = "Mining Business" if acct == "mining" else "Community Member"
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:14px;'>"
        f"<span style='font-size:1.3rem;'>{icon}</span>"
        f"<span style='font-weight:700;'>{label}</span>"
        f"<button onclick='location.reload()' style='margin-left:auto;background:none;"
        f"border:1px solid #E2E8F0;border-radius:6px;padding:3px 10px;font-size:0.8rem;"
        f"color:#475569;cursor:pointer;'>Change</button></div>",
        unsafe_allow_html=True,
    )
    # "Change" is cosmetic above; provide a real Streamlit button too
    if st.button("← Change account type", key="change_acct"):
        st.session_state.reg_account_type = None
        st.rerun()

    with st.form("register_form"):
        full_name = st.text_input("Full name", placeholder="Your full name")
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="Min 6 characters")
        confirm = st.text_input("Confirm password", type="password", placeholder="Repeat password")

        role = "community"
        if acct == "mining":
            role = st.selectbox(
                "Your role at the mine",
                ["manager", "operator"],
                format_func=lambda x: "Mine Manager" if x == "manager" else "Mine Operator",
            )
            mine = st.selectbox("Mine site", config.get_mines_by_phase(1))
        else:
            mine = None

        submitted = st.form_submit_button("Create Account →", use_container_width=True)

    if submitted:
        errors = []
        if not full_name.strip():
            errors.append("Full name is required.")
        if not email.strip() or "@" not in email:
            errors.append("A valid email address is required.")
        if email.strip().lower() in DEMO_USERS:
            errors.append("An account with that email already exists.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            # Add to in-memory store and log straight in
            new_user = {
                "password": password,
                "name": full_name.strip(),
                "account_type": acct,
                "role": role,
                "mine": mine,
            }
            DEMO_USERS[email.strip().lower()] = new_user
            st.session_state.authenticated = True
            st.session_state.user = {**new_user, "email": email.strip().lower()}
            st.session_state.reg_account_type = None
            st.rerun()


# =====================================================================
# 7. SIDEBAR — user card + mine selector + logout
# =====================================================================
def render_sidebar() -> str:
    """Render sidebar, return selected mine name (or None for community)."""
    u = st.session_state.user
    role = u["role"]
    role_label = {"manager": "Mine Manager", "operator": "Mine Operator",
                  "community": "Community Member"}.get(role, role.title())
    role_cls = {"manager": "role-manager", "operator": "role-operator",
                "community": "role-community"}.get(role, "")

    st.sidebar.markdown(
        f"""<div class="sidebar-user-card">
          <div class="sidebar-user-name">👤 {u['name']}</div>
          <div class="sidebar-user-role {role_cls}">{role_label}</div>
          <div style="font-size:0.76rem;color:#94A3B8;margin-top:2px;">{u['email']}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    selected_mine = None
    if role in ("manager", "operator"):
        phase1 = config.get_mines_by_phase(1)
        default_idx = phase1.index(u.get("mine", config.DEFAULT_MINE)) \
            if u.get("mine") in phase1 else 0
        selected_mine = st.sidebar.selectbox(
            "Active mine", phase1, index=default_idx
        )
        st.sidebar.caption(config.get_mine_config(selected_mine)["location"])
        st.sidebar.markdown("---")

    st.sidebar.caption("No backend · Session data only · POPIA-compliant")
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        _init_session()
        st.rerun()

    return selected_mine


# =====================================================================
# 8. SHARED STATUS HEADER  (mining roles only)
# =====================================================================
def render_staging_banner() -> None:
    p1 = config.STAGING_CONFIG["Phase 1"]
    p2 = config.STAGING_CONFIG["Phase 2"]
    st.markdown(
        f"""<div class="tt-staging-banner">
          <div style="color:#16A34A;display:flex;align-items:center;gap:7px;">
            <span style="width:8px;height:8px;border-radius:50%;background:#16A34A;
              display:inline-block;box-shadow:0 0 5px #16A34A;"></span>
            <strong>{p1['name']}</strong> &nbsp;·&nbsp; {p1['depth_band']}
            &nbsp;·&nbsp; {', '.join(p1['mines'])}
          </div>
          <div style="color:#94A3B8;display:flex;align-items:center;gap:7px;">
            <span style="width:8px;height:8px;border-radius:50%;background:#CBD5E1;
              display:inline-block;"></span>
            {p2['name']} &nbsp;·&nbsp; {p2['depth_band']}
            &nbsp;·&nbsp; {', '.join(p2['mines'])} (Roadmap)
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_status_header(selected_mine: str) -> None:
    mine_cfg = config.get_mine_config(selected_mine)
    available_mw = float(mine_cfg["available_heat_capacity_mw"])
    community_mw = config.get_total_allocated_community_heat_mw()
    commercial_mw = sum(i["heat_mw"] for i in st.session_state.commercial_interests)
    allocated_mw = round(community_mw + commercial_mw, 2)
    remaining_mw = max(0.0, round(available_mw - allocated_mw, 2))

    st.markdown(
        "<div style='font-size:0.72rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.1em;color:#94A3B8;margin-bottom:8px;'>"
        f"{config.SURFACE_PORTAL_HEADER}</div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Available Thermal Output", f"{available_mw:.1f} MWth",
              help=f"{selected_mine} fence-line capacity")
    c2.metric("Allocated (Community + Commercial)", f"{allocated_mw:.1f} MWth")
    c3.metric("Unallocated Headroom", f"{remaining_mw:.1f} MWth")

    cpct = min(100.0, community_mw / available_mw * 100) if available_mw else 0.0
    xpct = min(100.0 - cpct, commercial_mw / available_mw * 100) if available_mw else 0.0
    st.markdown(
        f"""<div class="tt-gauge-wrap">
          <div class="tt-gauge-track">
            <div class="tt-gauge-community" style="width:{cpct:.1f}%;"></div>
            <div class="tt-gauge-commercial" style="width:{xpct:.1f}%;"></div>
          </div>
          <div class="tt-gauge-caption">
            <span>
              <span style="color:#16A34A;">●</span> community {community_mw:.1f} MWth
              &nbsp;&nbsp;
              <span style="color:#0D9488;">●</span> commercial {commercial_mw:.1f} MWth
            </span>
            <span style="color:#EA580C;font-weight:600;">{remaining_mw:.1f} MWth available</span>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


# =====================================================================
# 9. DATA HELPERS
# =====================================================================
def get_telemetry(mine_name: str) -> pd.DataFrame:
    key = (mine_name, st.session_state.tamper_active, st.session_state.tamper_mode)
    if key not in st.session_state.telemetry_cache:
        st.session_state.telemetry_cache[key] = simulator.simulate_mine_telemetry(
            mine_name=mine_name,
            num_samples=180,
            inject_physics_mismatch=st.session_state.tamper_active,
            tamper_mode=st.session_state.tamper_mode,
        )
    return st.session_state.telemetry_cache[key]


def build_zone_summaries(df: pd.DataFrame) -> list:
    summaries = []
    for zone in df["zone"].unique():
        zdf = df[df["zone"] == zone].sort_values("timestamp")
        summaries.append(anomaly.process_telemetry_stream(
            reported_temps=zdf["reported_temp_c"].tolist(),
            predicted_temps=zdf["predicted_temp_c"].tolist(),
            wet_bulb_temps=zdf["wet_bulb_c"].tolist(),
            worker_counts=zdf["zone_occupancy_count"].tolist(),
            zone_name=zone,
        ))
    summaries.sort(key=lambda r: r["composite_risk_score"], reverse=True)
    return summaries


# =====================================================================
# 10. SCREEN — UNDERGROUND ENGINE  (Manager + Operator)
# =====================================================================
def render_underground_engine(selected_mine: str) -> None:
    screen_heading("🔻", "Underground Engine", "Predictive Safety", "tt-badge-orange")
    st.caption(
        f"Predicts a dangerous heat spike ~{config.PREDICTION_LEAD_TIME_MINUTES} min "
        "ahead and doubles as a tamper-detection layer using the same physics baseline."
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
            help="JUMP = sudden step. DRIFT = gradual calibration decay.",
        )
        if st.button("🔄 Regenerate telemetry"):
            st.session_state.telemetry_cache = {}
            st.rerun()

    df = get_telemetry(selected_mine)
    summaries = build_zone_summaries(df)

    with info_col:
        top = summaries[0]
        if top["priority"].startswith("Priority 1"):
            st.error(f"🚨 **CRITICAL** — {top['zone']}: {top['recommended_action']}")
        elif top["priority"].startswith("Priority 2"):
            st.warning(f"⚠️ **HIGH** — {top['zone']}: {top['recommended_action']}")
        else:
            st.success(f"✅ **All zones nominal** — Highest: {top['zone']} ({top['priority']})")

    zone_names = [s["zone"] for s in summaries]
    focus_zone = st.selectbox("Zone detail", zone_names)
    zone_df = df[df["zone"] == focus_zone].sort_values("timestamp").set_index("timestamp")

    # ── 25-minute forecast (OLS linear extrapolation) ──
    reported_series = zone_df["reported_temp_c"].tolist()
    fc = simulator.forecast_zone_temperature(reported_series)

    fc1, fc2, fc3 = st.columns(3)
    fc_color = "#DC2626" if fc["is_breach_predicted"] else "#0D9488"
    breach_label = (
        f"⚠️ +{fc['breach_margin_c']:.1f}°C above limit"
        if fc["is_breach_predicted"]
        else f"✅ {abs(fc['breach_margin_c']):.1f}°C below limit"
    )
    fc1.metric(
        f"Forecast wet-bulb in {fc['lead_minutes']} min",
        f"{fc['forecast_wb_c']:.1f}°C",
        delta=breach_label,
        delta_color="inverse" if fc["is_breach_predicted"] else "normal",
        help=f"Point forecast: {fc['forecast_temp_c']:.1f}°C ± {fc['sigma_c']:.2f}°C  "
             f"(slope {fc['slope_c_per_min']:+.3f}°C/min, R²={fc['r_squared']:.2f})",
    )
    fc2.metric(
        "Trend (°C / min)",
        f"{fc['slope_c_per_min']:+.4f}",
        help="Positive = heating up. Derived from OLS fit over last 10 samples.",
    )
    fc3.metric(
        "Forecast ±1σ band",
        f"{fc['lower_c']:.1f} – {fc['upper_c']:.1f}°C",
        help="Uncertainty from the residual standard error of the linear fit.",
    )

    # Build chart: history + single forecast point with uncertainty
    chart_df = zone_df[["reported_temp_c", "predicted_temp_c"]].copy()

    # Append one row at t+25 min to show the forecast point on the chart
    last_ts = chart_df.index[-1]
    forecast_ts = last_ts + pd.Timedelta(minutes=fc["lead_minutes"])
    forecast_row = pd.DataFrame(
        {
            "reported_temp_c": [None],
            "predicted_temp_c": [None],
            "forecast_temp_c": [fc["forecast_temp_c"]],
            "forecast_upper_c": [fc["upper_c"]],
            "forecast_lower_c": [fc["lower_c"]],
        },
        index=[forecast_ts],
    )
    # Extend history columns to match
    chart_df["forecast_temp_c"] = None
    chart_df["forecast_upper_c"] = None
    chart_df["forecast_lower_c"] = None
    chart_df = pd.concat([chart_df, forecast_row])

    st.line_chart(
        chart_df[["reported_temp_c", "predicted_temp_c",
                  "forecast_temp_c", "forecast_upper_c", "forecast_lower_c"]],
        color=["#EA580C", "#0D9488", "#DC2626", "#FCA5A5", "#FCA5A5"],
    )
    st.caption(
        f"🔴 reported &nbsp; 🟢 predicted (physics baseline) &nbsp; "
        f"🔴 dashed = {fc['lead_minutes']}-min forecast point &nbsp; "
        f"(OLS over last {fc['samples_used']} samples, R²={fc['r_squared']:.2f})"
    )

    st.markdown("**Worker-Risk Ranking** *(anonymous occupancy only)*")
    st.dataframe(
        pd.DataFrame([{
            "Rank": i + 1, "Zone": s["zone"], "Priority": s["priority"],
            "Risk Score": s["composite_risk_score"], "Wet-Bulb °C": s["latest_wet_bulb_c"],
            "Signature": s["latest_signature"], "Workers": s["worker_count"],
        } for i, s in enumerate(summaries)]),
        use_container_width=True, hide_index=True,
    )

    with st.expander("🔒 Data Privacy — how worker counts are produced"):
        ids = [f"{focus_zone.replace(' ','').upper()}-{i}" for i in range(6)]
        hashed = privacy.hash_worker_ids(ids)
        st.code(f"Raw: {ids}\nHashed: {hashed}\nCount: {privacy.zone_occupancy_density(hashed)}")
        st.caption("No PII stored or transmitted — POPIA-compliant hashed occupancy count only.")


# =====================================================================
# 11. SCREEN — COMMERCIAL DOOR  (Manager only)
# =====================================================================
def render_commercial_door(selected_mine: str) -> None:
    screen_heading("🏭", "Commercial Door", "Thermal tPPA", "tt-badge-teal")
    mine_cfg = config.get_mine_config(selected_mine)
    cfg = config.COMMERCIAL_DOOR_CONFIG

    c1, c2, c3 = st.columns(3)
    c1.metric("Fence-line Capacity", f"{mine_cfg['available_heat_capacity_mw']:.1f} MWth")
    c2.metric("Tariff Discount", f"{cfg['default_discount_percent']:.0f}% below Eskom")
    c3.metric("Local Hiring Quota", f"{cfg['mandatory_local_hiring_quota']:.0f}%")
    st.caption(cfg["tppa_summary"])

    max_mw = float(mine_cfg["available_heat_capacity_mw"])
    requested_mw = st.slider("Heat capacity to secure (MWth)", 0.5, max_mw, min(2.0, max_mw), 0.5)
    savings = config.calculate_commercial_savings(requested_mw)
    s1, s2 = st.columns(2)
    s1.metric("Est. annual offtaker savings", f"R {savings['annual_offtaker_savings_zar']:,.0f}")
    s2.metric("Est. annual mine revenue", f"R {savings['annual_mine_revenue_zar']:,.0f}")

    with st.form("express_interest_form"):
        st.markdown("**Express Interest — 1 form**")
        name = st.text_input("Company name")
        contact = st.text_input("Contact email")
        if st.form_submit_button("Submit Expression of Interest →", use_container_width=True):
            if name and contact:
                st.session_state.commercial_interests.append(
                    {"company": name, "contact": contact,
                     "heat_mw": requested_mw, "mine": selected_mine}
                )
                st.success(f"Recorded {requested_mw:.1f} MWth interest at {selected_mine}. We'll be in touch.")
            else:
                st.error("Company name and contact email are required.")

    if st.session_state.commercial_interests:
        with st.expander(f"📋 Submissions ({len(st.session_state.commercial_interests)})"):
            st.dataframe(pd.DataFrame(st.session_state.commercial_interests),
                         use_container_width=True, hide_index=True)


# =====================================================================
# 12. SCREEN — COMMUNITY DOOR  (stepped, accessible, all community users)
# =====================================================================
def _render_lang_selector() -> None:
    cols = st.columns(4)
    for i, lang in enumerate(["English", "isiZulu", "Setswana", "Afrikaans"]):
        with cols[i]:
            active = st.session_state.cd_language == lang
            if st.button(f"**{lang}**" if active else lang,
                         key=f"lang_{lang}", use_container_width=True):
                st.session_state.cd_language = lang
                st.rerun()


def _cd_step_pick() -> None:
    st.markdown(f"### {t('step1_heading')}")
    st.caption(t("step1_subtext"))
    listen_button(t("step1_heading") + ". " + t("step1_subtext"), key="ls1")

    cards = config.get_community_cards()
    for pair in [cards[i:i+2] for i in range(0, len(cards), 2)]:
        cols = st.columns(len(pair))
        for col, card in zip(cols, pair):
            meta = CARD_META.get(card["id"], {"icon": "🌿", "color": "#16A34A",
                                              "bg": "#F0FDF4", "border": "#BBF7D0"})
            with col:
                st.markdown(
                    f"""<div class="cd-pick-card"
                      style="border-color:{meta['border']};background:{meta['bg']};">
                      <div class="cd-pick-icon">{meta['icon']}</div>
                      <div class="cd-pick-label">{card['title']}</div>
                      <div class="cd-pick-sublabel">{card_benefit(card['id'])}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if st.button(f"{meta['icon']} {card['title']}",
                             key=f"pick_{card['id']}", use_container_width=True):
                    st.session_state.cd_selected_card_id = card["id"]
                    st.session_state.cd_step = "detail"
                    st.rerun()

    st.markdown("---")
    whatsapp_strip()
    offline_note()


def _cd_step_detail() -> None:
    card_id = st.session_state.cd_selected_card_id
    cards = {c["id"]: c for c in config.get_community_cards()}
    card = cards.get(card_id)
    if not card:
        st.session_state.cd_step = "pick"; st.rerun(); return

    meta = CARD_META.get(card_id, {"icon": "🌿", "color": "#16A34A",
                                   "bg": "#F0FDF4", "border": "#BBF7D0"})
    mine_total_mw = config.get_mine_config(config.DEFAULT_MINE)["available_heat_capacity_mw"]

    if st.button(t("step2_back"), key="cd_back"):
        st.session_state.cd_step = "pick"; st.rerun()

    st.markdown(
        f"""<div style="text-align:center;padding:20px 0 12px;
          background:{meta['bg']};border-radius:14px;margin-bottom:16px;
          border:1px solid {meta['border']};">
          <div style="font-size:3.8rem;">{meta['icon']}</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:1.5rem;
            font-weight:800;color:{meta['color']};margin-top:8px;">{card['title']}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    listen_button(card["title"] + ". " + card["description"], key=f"ld_{card_id}")
    st.write(card["description"])

    col_l, col_r = st.columns(2)
    with col_l:
        jobs_bar(card["jobs_created"], meta["color"])
    with col_r:
        heat_bar(card["allocated_mw"], mine_total_mw, meta["color"])

    st.markdown(
        f"""<div style="display:flex;gap:14px;flex-wrap:wrap;margin:12px 0 18px;
          font-size:0.88rem;padding:12px 16px;background:{meta['bg']};
          border-radius:10px;border:1px solid {meta['border']};">
          <div><span style="color:#94A3B8;">{t('label_focus')} </span>
               <strong>{card['focus_group']}</strong></div>
          <div><span style="color:#94A3B8;">{t('label_slp')} </span>
               <strong>{card['slp_metric']}</strong></div>
          <div><span style="color:#94A3B8;">{t('label_temp')} </span>
               <strong>{card['water_temp_c']}</strong></div>
        </div>""",
        unsafe_allow_html=True,
    )

    with st.form(f"apply_{card_id}"):
        applicant = st.text_input(t("name_label"), placeholder=t("name_placeholder"),
                                  value=st.session_state.cd_applicant_name)
        if st.form_submit_button(t("step2_apply"), use_container_width=True):
            if applicant.strip():
                st.session_state.cd_applicant_name = applicant.strip()
                st.session_state.community_applications.append(
                    {"applicant": applicant.strip(), "opportunity": card["title"]}
                )
                st.session_state.cd_step = "done"
                st.rerun()
            else:
                st.error("✏️ " + t("name_label"))

    st.markdown("---")
    whatsapp_strip()
    offline_note()


def _cd_step_done() -> None:
    card_id = st.session_state.cd_selected_card_id
    card = {c["id"]: c for c in config.get_community_cards()}.get(card_id, {})
    meta = CARD_META.get(card_id, {"icon": "🌿"})

    st.markdown(
        f"""<div class="cd-success-box">
          <div class="cd-success-icon">{meta['icon']} ✅</div>
          <div class="cd-success-heading">{t('step3_heading')}</div>
          <div style="font-size:1.05rem;color:#0F172A;margin:8px 0 4px;">
            {card.get('title','')}</div>
          <div class="cd-success-sub">
            {st.session_state.cd_applicant_name} · {t('step3_subtext')}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    whatsapp_strip()

    if st.button(t("step3_another"), use_container_width=True):
        st.session_state.cd_step = "pick"
        st.session_state.cd_selected_card_id = None
        st.session_state.cd_applicant_name = ""
        st.rerun()

    if st.session_state.community_applications:
        with st.expander(f"📋 Applications ({len(st.session_state.community_applications)})"):
            st.dataframe(pd.DataFrame(st.session_state.community_applications),
                         use_container_width=True, hide_index=True)


def render_community_door() -> None:
    screen_heading("🌱", "Community Door", "Opportunities", "tt-badge-green")
    st.caption(t("community_intro"))
    _render_lang_selector()

    step = st.session_state.get("cd_step", "pick")
    s1 = "active" if step == "pick" else "done"
    s2 = "active" if step == "detail" else ("done" if step == "done" else "idle")
    s3 = "active" if step == "done" else "idle"
    l1 = "done" if step in ("detail", "done") else ""
    l2 = "done" if step == "done" else ""
    st.markdown(
        f"""<div class="cd-step-indicator">
          <div class="cd-step-dot {s1}">1</div>
          <div class="cd-step-line {l1}"></div>
          <div class="cd-step-dot {s2}">2</div>
          <div class="cd-step-line {l2}"></div>
          <div class="cd-step-dot {s3}">✓</div>
        </div>""",
        unsafe_allow_html=True,
    )

    if step == "pick":
        _cd_step_pick()
    elif step == "detail":
        _cd_step_detail()
    elif step == "done":
        _cd_step_done()
    else:
        st.session_state.cd_step = "pick"; st.rerun()


# =====================================================================
# 13. SCREEN — ABOUT
# =====================================================================
def render_about() -> None:
    screen_heading("ℹ️", "About ThermalTwin", "MineFlow AI", "tt-badge-teal")
    st.markdown(
        """
Deep gold mines spend heavily fighting naturally hot rock; a few hundred metres away,
Merafong households often can't afford to use the power they're connected to.
ThermalTwin sits between the two:

- **Underground Engine** — predicts dangerous heat 25–30 min ahead using a live OLS
  linear extrapolation over the last 10 sensor readings; the same physics baseline
  doubles as a tamper-detection layer.
- **Surface Engine** — routes heat already pumped to surface toward businesses
  (Commercial Door / tPPA) or community incubation projects (Community Door / SLP).
- **Roadmap** — quantum sensing for order-of-magnitude precision improvements, and
  quantum-enhanced ML for detecting adversarial drift invisible to classical models.
        """
    )

    with st.expander("🛡️ Adversarial robustness — known attack vectors & mitigations"):
        st.markdown(
            """
**The threat:** a sophisticated attacker who understands our detection thresholds can craft a
slow drift that stays just below the `PHYSICS_MISMATCH_THRESHOLD_C` (1.5 °C) and the
`Z_SCORE_ALERT_THRESHOLD` (2.5σ) indefinitely — making the heat risk invisible while the
sensor reading slowly diverges from reality.

**Current mitigations:**
- **Cross-sensor spatial validation** (`validate_cross_sensors` in `anomaly.py`) — compares
  each RTD probe against its physically adjacent neighbours. A zone whose temperature diverges
  by more than `MAX_PLAUSIBLE_NEIGHBOR_DELTA_C` (3.5 °C) from all its neighbours is flagged
  `LOCALIZED_PROBE_ANOMALY`, regardless of Z-score. A real thermal event would heat adjacent
  zones too; a spoofed sensor is isolated by definition.
- **DRIFT signature** — sustained sub-threshold divergence across `SIGNATURE_DRIFT_MIN_TIMESTEPS`
  (3) consecutive samples is still classified and surfaced in the risk ranking, adding 15 points
  to the composite score and triggering a Priority 2–3 alert.
- **25-minute forecast** — the OLS slope detects an accelerating trend before it crosses the
  statutory 28 °C wet-bulb limit, giving a window to act even if the absolute reading is
  still nominally safe.

**Remaining gap (honest):**
A patient attacker could craft a ramp whose rate of change exactly matches the natural
baseline drift. This requires knowing the mine's `vrt_celsius`, `depth_meters`, and
our detection parameters — a high bar but not impossible. The roadmap mitigation is
ensemble detection (multiple independent models with different thresholds) and
eventually quantum-enhanced anomaly detection for sub-classical sensitivity.
            """
        )

    with st.expander("🔒 Privacy — edge security assumption"):
        st.markdown(
            """
**The claim:** "No PII is stored or transmitted" — this is true for the platform layer.
Worker badge IDs are SHA-256 hashed with a salt at the edge before any data reaches
the dashboard. The platform only ever sees an anonymous occupancy count.

**The dependency:** this claim rests on the edge device being secure. In production,
raw worker IDs do exist — briefly — at the sensor layer before hashing. If the edge
device is physically compromised or its firmware is tampered with, raw IDs could be
extracted before hashing occurs.

**Mitigations in the roadmap:**
- Edge devices should run in a Trusted Execution Environment (TEE / secure enclave)
  so the hash operation itself cannot be observed or bypassed.
- The salt (`EDGE_HASH_SALT` in `config.py`) must be rotated periodically and stored
  in a hardware security module (HSM) at the edge, not in plaintext config.
- Tamper-evident hardware seals and remote attestation for edge firmware integrity.
            """
        )

    with st.expander("💬 Honest caveats"):
        st.markdown(
            """
- Telemetry is **simulated** — the "predicted" baseline is scripted physics, not a trained ML model.
- The 25-minute forecast uses **OLS linear extrapolation** over the last 10 samples — a real
  deployment would train a time-series model on historical shift data.
- Phase 1 (chilled water mines); Phase 2 (Mponeng, TauTona) needs an ice-brine heat-exchanger
  design before the Surface Engine is applicable.
- Cross-sensor spatial validation (`validate_cross_sensors`) **is implemented** in `anomaly.py`
  but is not yet wired into the live dashboard alert pipeline — it runs as a standalone
  function. Wiring it to the per-zone alert is the next engineering task.
- The claim about OT-security vendors under-serving mid-tier SA mines is our belief,
  not yet confirmed with an industry source.
            """
        )


# =====================================================================
# 14. MAIN — role-gated routing
# =====================================================================
def main() -> None:
    inject_theme()

    # ---- Gate: show auth screen if not logged in ----
    if not st.session_state.authenticated:
        render_auth()
        return

    # ---- Logged-in: render sidebar & get selected mine ----
    selected_mine = render_sidebar()

    u = st.session_state.user
    role = u["role"]

    # ---- App header ----
    st.markdown(
        f"""<div style="margin-bottom:20px;">
          <div style="font-family:'Space Grotesk',sans-serif;font-size:2rem;
            font-weight:800;color:#0F172A;letter-spacing:-0.025em;">
            🌡️ ThermalTwin
          </div>
          <div style="font-size:0.9rem;color:#475569;margin-top:2px;">
            MineFlow AI &nbsp;·&nbsp; Mine heat, redirected to the community
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ---- COMMUNITY MEMBER: single screen, no mine metrics ----
    if role == "community":
        render_community_door()
        return

    # ---- MINING roles: staging banner + status header ----
    render_staging_banner()
    render_status_header(selected_mine)
    st.markdown("---")

    # ---- OPERATOR: Underground + About only ----
    if role == "operator":
        tab1, tab2 = st.tabs(["🔻 Underground Engine", "ℹ️ About"])
        with tab1:
            render_underground_engine(selected_mine)
        with tab2:
            render_about()
        return

    # ---- MANAGER: all four tabs ----
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔻 Underground Engine",
        "🏭 Commercial Door",
        "🌱 Community Door",
        "ℹ️ About",
    ])
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
