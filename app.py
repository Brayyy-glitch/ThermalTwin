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
  3. Community Door — incubation opportunity cards, stepped 1-decision-per-screen apply flow
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


# =====================================================================
# MULTILINGUAL STRING TABLE
# Four languages spoken in the Merafong / Carletonville area.
# All community-facing copy goes through this table so a translator only
# ever edits one dictionary — no code changes needed.
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
        "before_label": "Before (cost)",
        "after_label": "After (free heat)",
        "jobs_icon": "👩‍🌾",
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
        "before_label": "Ngaphambi (intengo)",
        "after_label": "Ngemuva (ukufudumala kwamahhala)",
        "jobs_icon": "👩‍🌾",
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
        "before_label": "Pele (tshenyegelo)",
        "after_label": "Morago (bothitho jo bo sa duelelweng)",
        "jobs_icon": "👩‍🌾",
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
        "before_label": "Voor (koste)",
        "after_label": "Na (gratis hitte)",
        "jobs_icon": "👩‍🌾",
        "listen_tooltip": "Luister",
    },
}

# Per-card icon and a one-line benefit string (language-neutral where possible)
CARD_META: dict = {
    "merafong_hydroponics": {
        "icon": "🥬",
        "icon_label": "Hydroponics / Vegetables",
        "benefit_en": "Grow vegetables all year — no winter heating bill.",
        "benefit_zu": "Ukukhula kwemifino unyaka wonke — ngaphandle kwezindleko zokufudumeza.",
        "benefit_tn": "Godisa merogo ka mokgabo wotlhe — ga go na tefelo ya bothitho.",
        "benefit_af": "Groente die hele jaar — geen verwarmingsrekening nie.",
        "color": "#59C97A",
    },
    "tilapia_aquaculture": {
        "icon": "🐟",
        "icon_label": "Fish Farming",
        "benefit_en": "Farm fish in warm water — no fuel needed.",
        "benefit_zu": "Ukufuya izinhlanzi emanzini afudumele — ngaphandle kwamafutha.",
        "benefit_tn": "Allela ditlhapi mo metsing a bothitho — ga go a tlhokagala metsi a mafutha.",
        "benefit_af": "Teelvis in warm water — geen brandstof nodig nie.",
        "color": "#3FC6D1",
    },
    "post_harvest_drying": {
        "icon": "🌾",
        "icon_label": "Crop Drying",
        "benefit_en": "Dry your harvest with free heat — stop food going to waste.",
        "benefit_zu": "Omisa isivuno sakho ngokufudumala kwamahhala — misa ukuchithwa kokudla.",
        "benefit_tn": "Omisa selelo sa gago ka bothitho jo bo sa duelelweng — emisa dijo go senyiwa.",
        "benefit_af": "Droog jou oes met gratis hitte — stop voedselvermorsing.",
        "color": "#FF8A3D",
    },
    "sanitation_laundry": {
        "icon": "🧺",
        "icon_label": "Laundry & Hot Water",
        "benefit_en": "Hot water for laundry and clinics — no coal, no paraffin.",
        "benefit_zu": "Amanzi ashisayo okuhlanza namakhliniki — ngaphandle komalahle, ngaphandle kwe-paraffin.",
        "benefit_tn": "Metsi a bothitho a go tlhapa le dikiliniki — ga go makhala, ga go paraffin.",
        "benefit_af": "Warm water vir wasserye en klinieke — geen steenkool, geen paraffien nie.",
        "color": "#B57FFF",
    },
}


# =====================================================================
# VISUAL IDENTITY — control-room theme, not default SaaS grey.
# Amber = heat/thermal, cyan = safety/commercial, green = nominal/community.
# Community Door gets larger touch targets and bigger base font.
# =====================================================================
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
          --tt-purple: #B57FFF;

          /* Community Door sizing — larger for low-literacy / small screens */
          --cd-font-size: 1.08rem;
          --cd-icon-size: 3.2rem;
          --cd-btn-padding: 18px 0;
          --cd-radius: 10px;
          --cd-touch-min: 56px;
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

        /* Default buttons */
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

        /* Capacity gauge bar */
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

        /* -------------------------------------------------------
           COMMUNITY DOOR — larger touch targets, bigger text
        ------------------------------------------------------- */

        /* Opportunity pick cards (Step 1) */
        .cd-pick-card {
          background-color: var(--tt-panel);
          border: 2px solid var(--tt-border);
          border-radius: var(--cd-radius);
          padding: 22px 14px 18px 14px;
          text-align: center;
          cursor: pointer;
          transition: border-color 0.15s, background-color 0.15s;
          min-height: 160px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }
        .cd-pick-card:hover {
          border-color: var(--tt-amber);
          background-color: #1e2a30;
        }
        .cd-pick-icon {
          font-size: var(--cd-icon-size);
          line-height: 1;
        }
        .cd-pick-label {
          font-family: 'Oswald', sans-serif;
          font-size: 1.05rem;
          font-weight: 600;
          color: var(--tt-text);
          margin-top: 4px;
        }
        .cd-pick-sublabel {
          font-size: 0.85rem;
          color: var(--tt-muted);
        }

        /* Apply button — big, finger-friendly */
        .cd-apply-btn > button, .stFormSubmitButton.cd-apply-btn > button {
          min-height: var(--cd-touch-min);
          font-size: 1.1rem !important;
          padding: var(--cd-btn-padding) !important;
          width: 100%;
          border-radius: var(--cd-radius) !important;
          background-color: var(--tt-green) !important;
          color: #0A1418 !important;
          font-weight: 700 !important;
          letter-spacing: 0.03em;
        }
        .cd-apply-btn > button:hover {
          background-color: var(--tt-amber) !important;
        }

        /* Back button — secondary */
        .cd-back-btn > button {
          min-height: 44px;
          background-color: transparent !important;
          color: var(--tt-muted) !important;
          border: 1px solid var(--tt-border) !important;
          border-radius: var(--cd-radius) !important;
          font-size: 0.95rem !important;
        }

        /* Bar chart rows for "numbers as pictures" */
        .cd-bar-row {
          display: flex; align-items: center; gap: 10px;
          margin: 4px 0; font-size: 0.9rem;
        }
        .cd-bar-label { color: var(--tt-muted); min-width: 80px; font-size: 0.82rem; }
        .cd-bar-track {
          flex: 1; height: 14px; background-color: #0A1013;
          border-radius: 3px; overflow: hidden;
          border: 1px solid var(--tt-border);
        }
        .cd-bar-fill { height: 100%; border-radius: 3px; }
        .cd-bar-value { min-width: 54px; text-align: right; font-size: 0.82rem; color: var(--tt-text); font-family: 'IBM Plex Mono', monospace; }

        /* WhatsApp human fallback strip */
        .cd-whatsapp-strip {
          background-color: #0d2318;
          border: 1px solid #1a4a2e;
          border-left: 4px solid #25D366;
          border-radius: 8px;
          padding: 12px 16px;
          display: flex;
          align-items: center;
          gap: 14px;
          font-size: var(--cd-font-size);
          margin: 10px 0;
        }
        .cd-whatsapp-icon { font-size: 1.8rem; flex-shrink: 0; }
        .cd-whatsapp-number { font-weight: 700; color: #25D366; font-size: 1.1rem; }
        .cd-whatsapp-name { color: var(--tt-muted); font-size: 0.88rem; }

        /* Offline / low-data note */
        .cd-offline-note {
          background-color: #0f1a20;
          border: 1px solid var(--tt-border);
          border-radius: 6px;
          padding: 8px 14px;
          font-size: 0.82rem;
          color: var(--tt-muted);
          margin-bottom: 10px;
        }

        /* Listen (voice) button */
        .cd-listen-btn {
          display: inline-flex; align-items: center; gap: 5px;
          background: none; border: 1px solid var(--tt-border);
          border-radius: 20px; padding: 3px 10px 3px 8px;
          font-size: 0.8rem; color: var(--tt-muted);
          cursor: pointer; transition: border-color 0.15s;
        }
        .cd-listen-btn:hover { border-color: var(--tt-amber); color: var(--tt-amber); }
        .cd-listen-icon { font-size: 1rem; }

        /* Confirmation / success screen */
        .cd-success-box {
          background-color: #0d2318;
          border: 2px solid var(--tt-green);
          border-radius: var(--cd-radius);
          padding: 32px 24px;
          text-align: center;
        }
        .cd-success-icon { font-size: 3.5rem; }
        .cd-success-heading {
          font-family: 'Oswald', sans-serif;
          font-size: 1.7rem;
          color: var(--tt-green);
          margin: 10px 0 6px 0;
        }
        .cd-success-sub { color: var(--tt-muted); font-size: 1rem; }

        /* Language selector pill row */
        .cd-lang-row {
          display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# SESSION STATE
# =====================================================================
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
# Community Door stepped flow state
if "cd_language" not in st.session_state:
    st.session_state.cd_language = "English"
if "cd_step" not in st.session_state:
    st.session_state.cd_step = "pick"          # "pick" | "detail" | "done"
if "cd_selected_card_id" not in st.session_state:
    st.session_state.cd_selected_card_id = None
if "cd_applicant_name" not in st.session_state:
    st.session_state.cd_applicant_name = ""


# =====================================================================
# HELPERS
# =====================================================================
def t(key: str) -> str:
    """Return the translated string for the current Community Door language."""
    lang = st.session_state.get("cd_language", "English")
    return LANG_STRINGS.get(lang, LANG_STRINGS["English"]).get(key, LANG_STRINGS["English"].get(key, key))


def card_benefit(card_id: str) -> str:
    """Return language-appropriate one-line benefit for a card."""
    lang = st.session_state.get("cd_language", "English")
    meta = CARD_META.get(card_id, {})
    mapping = {"English": "benefit_en", "isiZulu": "benefit_zu", "Setswana": "benefit_tn", "Afrikaans": "benefit_af"}
    return meta.get(mapping.get(lang, "benefit_en"), meta.get("benefit_en", ""))


def listen_button(text_to_speak: str, key: str) -> None:
    """
    Renders a small 🔊 Listen button. On click, uses the Web Speech API via
    st.components.v1.html to speak the text aloud in the current language.
    Gracefully does nothing on browsers without Speech API support.
    """
    lang_code_map = {"English": "en-ZA", "isiZulu": "zu-ZA", "Setswana": "tn-ZA", "Afrikaans": "af-ZA"}
    lang_code = lang_code_map.get(st.session_state.get("cd_language", "English"), "en-ZA")
    safe_text = text_to_speak.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")

    import streamlit.components.v1 as components
    components.html(
        f"""
        <button onclick="
          if('speechSynthesis' in window){{
            var u=new SpeechSynthesisUtterance('{safe_text}');
            u.lang='{lang_code}';
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
          }}
        " style="
          display:inline-flex;align-items:center;gap:5px;
          background:none;border:1px solid #2B363D;border-radius:20px;
          padding:4px 12px 4px 10px;font-size:0.82rem;color:#8FA0A8;
          cursor:pointer;font-family:Inter,sans-serif;
        ">
          🔊 {t('listen_tooltip')}
        </button>
        """,
        height=38,
    )


def whatsapp_strip() -> None:
    """Render the human fallback contact strip."""
    st.markdown(
        f"""
        <div class="cd-whatsapp-strip">
          <span class="cd-whatsapp-icon">💬</span>
          <div>
            <div style="font-size:0.85rem;color:#8FA0A8;">{t('whatsapp_label')}</div>
            <div class="cd-whatsapp-number">{t('whatsapp_number')}</div>
            <div class="cd-whatsapp-name">{t('whatsapp_contact')}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def offline_note() -> None:
    st.markdown(f'<div class="cd-offline-note">{t("offline_note")}</div>', unsafe_allow_html=True)


def jobs_bar(jobs_label: str, jobs_count_str: str, color: str) -> None:
    """
    Visual bar comparing 'before' (0 jobs) and 'after' (N jobs).
    Makes numeracy optional — the bar itself communicates magnitude.
    """
    # Parse first integer from jobs string, e.g. "45 direct full-time, 90 seasonal" -> 45
    import re
    match = re.search(r"\d+", jobs_count_str)
    jobs_num = int(match.group()) if match else 10
    # Scale: 60 jobs = 100% bar width
    pct = min(100, int(jobs_num / 60 * 100))
    before_label = t("before_label")
    after_label = t("after_label")

    st.markdown(
        f"""
        <div style="margin:10px 0 6px 0;">
          <div style="font-size:0.8rem;color:#8FA0A8;margin-bottom:4px;">{t('label_jobs')}</div>
          <div class="cd-bar-row">
            <span class="cd-bar-label">{before_label}</span>
            <div class="cd-bar-track">
              <div class="cd-bar-fill" style="width:3%;background-color:#2B363D;"></div>
            </div>
            <span class="cd-bar-value">0</span>
          </div>
          <div class="cd-bar-row">
            <span class="cd-bar-label">{after_label}</span>
            <div class="cd-bar-track">
              <div class="cd-bar-fill" style="width:{pct}%;background-color:{color};"></div>
            </div>
            <span class="cd-bar-value">{jobs_count_str.split(',')[0]}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def heat_bar(allocated_mw: float, total_mw: float, color: str) -> None:
    """Visual bar showing how much free heat this project gets vs the mine's total."""
    pct = min(100, int(allocated_mw / total_mw * 100))
    before_label = t("before_label")
    after_label = t("after_label")
    st.markdown(
        f"""
        <div style="margin:10px 0 6px 0;">
          <div style="font-size:0.8rem;color:#8FA0A8;margin-bottom:4px;">{t('label_heat')}</div>
          <div class="cd-bar-row">
            <span class="cd-bar-label">{before_label}</span>
            <div class="cd-bar-track">
              <div class="cd-bar-fill" style="width:3%;background-color:#2B363D;"></div>
            </div>
            <span class="cd-bar-value">R0</span>
          </div>
          <div class="cd-bar-row">
            <span class="cd-bar-label">{after_label}</span>
            <div class="cd-bar-track">
              <div class="cd-bar-fill" style="width:{pct}%;background-color:{color};"></div>
            </div>
            <span class="cd-bar-value">{allocated_mw} MW</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# STAGING BANNER
# =====================================================================
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


# =====================================================================
# SHARED LIVE STATUS HEADER
# =====================================================================
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


# =====================================================================
# DATA GENERATION (cached per mine + tamper settings for this session)
# =====================================================================
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
# SCREEN 1: UNDERGROUND ENGINE
# =====================================================================
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


# =====================================================================
# SCREEN 2: COMMERCIAL DOOR
# =====================================================================
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


# =====================================================================
# SCREEN 3: COMMUNITY DOOR — stepped flow for low-literacy users
# =====================================================================

def _render_language_selector() -> None:
    """Compact language pill switcher at the top of the Community Door."""
    cols = st.columns(4)
    for i, lang in enumerate(["English", "isiZulu", "Setswana", "Afrikaans"]):
        with cols[i]:
            active = st.session_state.cd_language == lang
            label = f"**{lang}**" if active else lang
            if st.button(label, key=f"lang_btn_{lang}", use_container_width=True):
                st.session_state.cd_language = lang
                st.rerun()


def _cd_step_pick() -> None:
    """
    Step 1 — One decision: which opportunity?
    Large icon cards. One tap → advance to detail view.
    No description text yet — icons carry the meaning first.
    """
    st.markdown(f"### {t('step1_heading')}")
    st.caption(t("step1_subtext"))
    listen_button(t("step1_heading") + ". " + t("step1_subtext"), key="listen_step1")

    cards = config.get_community_cards()
    col_pairs = [cards[i:i+2] for i in range(0, len(cards), 2)]

    for pair in col_pairs:
        cols = st.columns(len(pair))
        for col, card in zip(cols, pair):
            meta = CARD_META.get(card["id"], {"icon": "🌿", "color": "#59C97A"})
            with col:
                # Render the visual card
                st.markdown(
                    f"""
                    <div class="cd-pick-card" style="border-color:{meta['color']}22;">
                      <div class="cd-pick-icon">{meta['icon']}</div>
                      <div class="cd-pick-label">{card['title']}</div>
                      <div class="cd-pick-sublabel">{card_benefit(card['id'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Actual Streamlit button for interactivity underneath the visual
                if st.button(
                    f"{meta['icon']} {card['title']}",
                    key=f"pick_{card['id']}",
                    use_container_width=True,
                ):
                    st.session_state.cd_selected_card_id = card["id"]
                    st.session_state.cd_step = "detail"
                    st.rerun()

    st.markdown("---")
    whatsapp_strip()
    offline_note()


def _cd_step_detail() -> None:
    """
    Step 2 — One decision: apply or go back.
    Full card details + before/after visual bars. One big apply button.
    """
    card_id = st.session_state.cd_selected_card_id
    cards = {c["id"]: c for c in config.get_community_cards()}
    card = cards.get(card_id)
    if not card:
        st.session_state.cd_step = "pick"
        st.rerun()
        return

    meta = CARD_META.get(card_id, {"icon": "🌿", "color": "#59C97A"})
    mine_total_mw = config.get_mine_config(config.DEFAULT_MINE)["available_heat_capacity_mw"]

    # ---- Back button ----
    if st.button(t("step2_back"), key="cd_back_btn"):
        st.session_state.cd_step = "pick"
        st.rerun()

    # ---- Card header ----
    st.markdown(
        f"""
        <div style="text-align:center;padding:20px 0 10px 0;">
          <div style="font-size:4rem;">{meta['icon']}</div>
          <div style="font-family:'Oswald',sans-serif;font-size:1.6rem;color:{meta['color']};margin-top:8px;">
            {card['title']}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    listen_button(card["title"] + ". " + card["description"], key=f"listen_detail_{card_id}")

    # ---- Description ----
    st.write(card["description"])

    # ---- Numbers as pictures ----
    col_l, col_r = st.columns(2)
    with col_l:
        jobs_bar(t("label_jobs"), card["jobs_created"], meta["color"])
    with col_r:
        heat_bar(card["allocated_mw"], mine_total_mw, meta["color"])

    # ---- Focus & SLP ----
    st.markdown(
        f"""
        <div style="display:flex;gap:16px;flex-wrap:wrap;margin:10px 0 16px 0;font-size:0.9rem;">
          <div><span style="color:#8FA0A8;">{t('label_focus')} </span>{card['focus_group']}</div>
          <div><span style="color:#8FA0A8;">{t('label_slp')} </span>{card['slp_metric']}</div>
          <div><span style="color:#8FA0A8;">{t('label_temp')} </span>{card['water_temp_c']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Apply form — one input, one big button ----
    with st.form(f"cd_apply_form_{card_id}"):
        applicant = st.text_input(
            t("name_label"),
            placeholder=t("name_placeholder"),
            value=st.session_state.cd_applicant_name,
        )
        submitted = st.form_submit_button(t("step2_apply"), use_container_width=True)
        if submitted:
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
    """
    Step 3 — Confirmation. Nothing to decide. Just reassurance + next action.
    """
    card_id = st.session_state.cd_selected_card_id
    cards = {c["id"]: c for c in config.get_community_cards()}
    card = cards.get(card_id, {})
    meta = CARD_META.get(card_id, {"icon": "🌿"})

    st.markdown(
        f"""
        <div class="cd-success-box">
          <div class="cd-success-icon">{meta['icon']} ✅</div>
          <div class="cd-success-heading">{t('step3_heading')}</div>
          <div style="font-size:1.1rem;color:#E8ECEE;margin:8px 0 4px 0;">
            {card.get('title', '')}
          </div>
          <div class="cd-success-sub">
            {st.session_state.cd_applicant_name} · {t('step3_subtext')}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    whatsapp_strip()

    if st.button(t("step3_another"), use_container_width=True):
        st.session_state.cd_step = "pick"
        st.session_state.cd_selected_card_id = None
        st.session_state.cd_applicant_name = ""
        st.rerun()

    if st.session_state.community_applications:
        with st.expander(f"📋 Applications received ({len(st.session_state.community_applications)})"):
            st.dataframe(
                pd.DataFrame(st.session_state.community_applications),
                use_container_width=True,
                hide_index=True,
            )


def render_community_door() -> None:
    """
    Community Door — redesigned for low-literacy, multilingual, low-resource users.

    UX principles applied:
    - Language first: isiZulu / Setswana / Afrikaans / English switcher at top
    - Icons before words: large emoji icons lead every option
    - One decision per screen: stepped flow (pick → detail → done)
    - Numbers as pictures: before/after bar charts instead of raw numbers
    - Human fallback: WhatsApp contact visible on every screen
    - Voice-first: 🔊 Listen button reads key text aloud using Web Speech API
    - Weak signal: no heavy images, no autoplay, minimal DOM weight
    """
    st.subheader(t("community_tab_title"))
    st.caption(t("community_intro"))

    # Language selector — always at top, always visible
    _render_language_selector()

    step = st.session_state.get("cd_step", "pick")
    if step == "pick":
        _cd_step_pick()
    elif step == "detail":
        _cd_step_detail()
    elif step == "done":
        _cd_step_done()
    else:
        st.session_state.cd_step = "pick"
        st.rerun()


# =====================================================================
# SCREEN 4: ICP / ABOUT
# =====================================================================
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


# =====================================================================
# MAIN
# =====================================================================
def main() -> None:
    inject_theme()
    render_staging_banner()
    st.title("ThermalTwin — MineFlow AI")

    phase1_mines = config.get_mines_by_phase(1)
    selected_mine = st.sidebar.selectbox(
        "Active mine (Phase 1 demo)", phase1_mines, index=phase1_mines.index(config.DEFAULT_MINE)
    )
    st.sidebar.caption(config.get_mine_config(selected_mine)["location"])
    st.sidebar.markdown("---")
    st.sidebar.caption("No login. No backend. All data for this demo lives in your browser session only.")

    render_status_header(selected_mine)
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔻 Underground Engine", "🏭 Commercial Door", t("community_tab_title"), "ℹ️ About"]
    )
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
