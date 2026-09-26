"""
ThermalTwin (MineFlow AI) — System Configuration & Single Source of Truth
========================================================================
Owns:
  - ICP Staging data (Phase 1 Active Demo vs Phase 2 Roadmap)
  - Mine specifications (depths, virgin rock temperatures, cooling mechanisms)
  - Thermodynamic & statutory safety limits (SA MHSA wet-bulb 28°C)
  - Physics-aware anomaly detection thresholds (rolling Z-score, mismatch, drift/jump)
  - Surface Engine Portal configuration (Commercial Door & Community Door)

Designed to be safely human-editable by Narrative & Compliance without breaking code.
"""

from typing import Dict, List, Any, Optional

# =====================================================================
# 1. STATUTORY & THERMODYNAMIC CONSTANTS
# =====================================================================

# South African Mine Health and Safety Act (MHSA) statutory wet-bulb temperature limit (°C).
# Above 28.0°C wet-bulb, work shifts must be regulated/curtailed, and heat stroke risk escalates exponentially.
STATUTORY_WET_BULB_LIMIT: float = 28.0

# Proactive caution threshold (°C). Early warning horizon where ventilation should be proactively redirected.
WET_BULB_CAUTION_LIMIT: float = 27.0

# Critical emergency evacuation dry-bulb equivalent / extreme threshold (°C)
STATUTORY_HEAT_STROKE_CRITICAL: float = 32.5

# Standard chilled service water supply temperature delivered underground (°C)
CHILLED_WATER_SUPPLY_TEMP_C: float = 5.0

# Ice-brine return flow interface temperature for ultra-deep mines past 3,300m (°C)
ICE_BRINE_SUPPLY_TEMP_C: float = 0.5

# Early warning predictive horizon in minutes (Underground Engine)
PREDICTION_LEAD_TIME_MINUTES: int = 25

# Telemetry sample interval in seconds (1 reading per minute)
TELEMETRY_INTERVAL_SECONDS: int = 60


# =====================================================================
# 2. ANOMALY & SECURITY DETECTION THRESHOLDS
# =====================================================================

# Number of rolling readings used to compute moving mean and standard deviation
ROLLING_WINDOW_SIZE: int = 20

# Statistical Z-score alert threshold (|Z| >= 2.5 flags anomalous statistical divergence)
Z_SCORE_ALERT_THRESHOLD: float = 2.5

# Statistical Z-score critical threshold (|Z| >= 3.5 indicates extreme statistical aberration)
Z_SCORE_CRITICAL_THRESHOLD: float = 3.5

# Minimum difference (|T_reported - T_predicted| in °C) that triggers a physics-mismatch security alert
PHYSICS_MISMATCH_THRESHOLD_C: float = 1.5

# Single-step rate of change (|delta_t - delta_{t-1}| in °C) distinguishing sudden JUMP from gradual DRIFT
# A rate >= 0.8°C per sample indicates an abrupt step change characteristic of sensor spoofing/injection.
SIGNATURE_JUMP_THRESHOLD_C: float = 0.8

# Minimum number of consecutive timesteps with sustained divergence required to classify as DRIFT
SIGNATURE_DRIFT_MIN_TIMESTEPS: int = 3

# Spatial correlation limit for cross-sensor validation: max plausible delta between adjacent RTDs (°C)
MAX_PLAUSIBLE_NEIGHBOR_DELTA_C: float = 3.5

# Anomaly signature constants
SIGNATURE_NORMAL: str = "NORMAL"
SIGNATURE_DRIFT: str = "DRIFT"
SIGNATURE_JUMP: str = "JUMP"


# =====================================================================
# 3. ICP STAGING & TARGET MINES (SINGLE SOURCE OF TRUTH)
# =====================================================================

# Phase 1 vs Phase 2 Staging Model
# Conventional chilled-water cooling stops being practical past ~3,300m (the water heats up
# excessively on the descent), so the deepest mines require melted ice-brine circuits.
STAGING_CONFIG: Dict[str, Dict[str, Any]] = {
    "Phase 1": {
        "name": "Phase 1 (Active Demo)",
        "depth_band": "2.5 km – 3.3 km",
        "depth_range_m": (2500, 3300),
        "cooling_mechanism": "Closed-loop chilled service water heat exchanger",
        "cooling_water_temp_c": CHILLED_WATER_SUPPLY_TEMP_C,
        "active": True,
        "mines": ["Driefontein", "South Deep", "Kusasalethu", "Kloof"],
        "description": "Standard deep-level gold mines cooled by high-volume surface refrigeration and chilled service water downcasts."
    },
    "Phase 2": {
        "name": "Phase 2 (Roadmap)",
        "depth_band": "> 3.3 km – 4.0 km",
        "depth_range_m": (3301, 4000),
        "cooling_mechanism": "Melted ice-brine return flow interface",
        "cooling_water_temp_c": ICE_BRINE_SUPPLY_TEMP_C,
        "active": False,
        "mines": ["Mponeng", "TauTona"],
        "description": "Ultra-deep gold mines where chilled water absorbs too much heat on descent, requiring surface ice slurry plants and underground ice-brine return flow."
    }
}

# Detailed specifications per mine
MINES_DATA: Dict[str, Dict[str, Any]] = {
    "Driefontein": {
        "phase": 1,
        "depth_meters": 3000,
        "vrt_celsius": 62.0,  # Virgin Rock Temperature
        "operator": "Sibanye-Stillwater",
        "location": "Carletonville, Far West Rand, Gauteng",
        "cooling_mechanism": "Closed-loop chilled service water heat exchanger",
        "cooling_supply_temp_c": CHILLED_WATER_SUPPLY_TEMP_C,
        "baseline_airflow_m3s": 420.0,
        "available_heat_capacity_mw": 14.5,
        "default_zones": [
            "Level 28 Haulage",
            "Zone 2 Stope Face",
            "Shaft 4 Return Airway",
            "Zone 3 Sub-Station"
        ],
        "zone_adjacencies": {
            "Level 28 Haulage": ["Zone 2 Stope Face", "Zone 3 Sub-Station"],
            "Zone 2 Stope Face": ["Level 28 Haulage", "Shaft 4 Return Airway"],
            "Shaft 4 Return Airway": ["Zone 2 Stope Face"],
            "Zone 3 Sub-Station": ["Level 28 Haulage"]
        }
    },
    "South Deep": {
        "phase": 1,
        "depth_meters": 2990,
        "vrt_celsius": 60.5,
        "operator": "Gold Fields",
        "location": "Westonaria, Gauteng",
        "cooling_mechanism": "Closed-loop chilled service water heat exchanger",
        "cooling_supply_temp_c": CHILLED_WATER_SUPPLY_TEMP_C,
        "baseline_airflow_m3s": 480.0,
        "available_heat_capacity_mw": 16.0,
        "default_zones": [
            "Trackless Ramp West",
            "Zone 2 Ventilation Bypass",
            "Main Orebody 95-3",
            "South Stope 1"
        ],
        "zone_adjacencies": {
            "Trackless Ramp West": ["Zone 2 Ventilation Bypass", "Main Orebody 95-3"],
            "Zone 2 Ventilation Bypass": ["Trackless Ramp West", "South Stope 1"],
            "Main Orebody 95-3": ["Trackless Ramp West"],
            "South Stope 1": ["Zone 2 Ventilation Bypass"]
        }
    },
    "Kusasalethu": {
        "phase": 1,
        "depth_meters": 3200,
        "vrt_celsius": 64.0,
        "operator": "Harmony Gold",
        "location": "Carletonville, Gauteng",
        "cooling_mechanism": "Closed-loop chilled service water heat exchanger",
        "cooling_supply_temp_c": CHILLED_WATER_SUPPLY_TEMP_C,
        "baseline_airflow_m3s": 390.0,
        "available_heat_capacity_mw": 13.8,
        "default_zones": [
            "Working Stope 88",
            "Zone 2 Active Stope",
            "Raise Bore Intake",
            "De-cline 3 Haulage"
        ],
        "zone_adjacencies": {
            "Working Stope 88": ["Zone 2 Active Stope", "Raise Bore Intake"],
            "Zone 2 Active Stope": ["Working Stope 88", "De-cline 3 Haulage"],
            "Raise Bore Intake": ["Working Stope 88"],
            "De-cline 3 Haulage": ["Zone 2 Active Stope"]
        }
    },
    "Kloof": {
        "phase": 1,
        "depth_meters": 3100,
        "vrt_celsius": 63.0,
        "operator": "Sibanye-Stillwater",
        "location": "Westonaria, Gauteng",
        "cooling_mechanism": "Closed-loop chilled service water heat exchanger",
        "cooling_supply_temp_c": CHILLED_WATER_SUPPLY_TEMP_C,
        "baseline_airflow_m3s": 410.0,
        "available_heat_capacity_mw": 14.2,
        "default_zones": [
            "Sub-vertical Hoist Chamber",
            "Zone 2 Stope Face",
            "Reeves Shaft Level 40",
            "East Return Airway"
        ],
        "zone_adjacencies": {
            "Sub-vertical Hoist Chamber": ["Zone 2 Stope Face", "Reeves Shaft Level 40"],
            "Zone 2 Stope Face": ["Sub-vertical Hoist Chamber", "East Return Airway"],
            "Reeves Shaft Level 40": ["Sub-vertical Hoist Chamber"],
            "East Return Airway": ["Zone 2 Stope Face"]
        }
    },
    "Mponeng": {
        "phase": 2,
        "depth_meters": 3840,
        "vrt_celsius": 68.0,
        "operator": "Harmony Gold",
        "location": "Carletonville / Merafong, Gauteng",
        "cooling_mechanism": "Melted ice-brine return flow interface",
        "cooling_supply_temp_c": ICE_BRINE_SUPPLY_TEMP_C,
        "baseline_airflow_m3s": 520.0,
        "available_heat_capacity_mw": 22.0,
        "default_zones": [
            "Level 115 Stope",
            "Zone 2 Deep Haulage",
            "Sub-Shaft 3",
            "Ventilation Incline 4"
        ],
        "zone_adjacencies": {
            "Level 115 Stope": ["Zone 2 Deep Haulage", "Sub-Shaft 3"],
            "Zone 2 Deep Haulage": ["Level 115 Stope", "Ventilation Incline 4"],
            "Sub-Shaft 3": ["Level 115 Stope"],
            "Ventilation Incline 4": ["Zone 2 Deep Haulage"]
        }
    },
    "TauTona": {
        "phase": 2,
        "depth_meters": 3900,
        "vrt_celsius": 66.5,
        "operator": "Care & Maintenance / Redevelopment",
        "location": "Carletonville, Gauteng",
        "cooling_mechanism": "Melted ice-brine return flow interface",
        "cooling_supply_temp_c": ICE_BRINE_SUPPLY_TEMP_C,
        "baseline_airflow_m3s": 350.0,
        "available_heat_capacity_mw": 18.5,
        "default_zones": [
            "Level 112 Workings",
            "Zone 2 Return Way",
            "Shaft 1 North",
            "Old Stope West"
        ],
        "zone_adjacencies": {
            "Level 112 Workings": ["Zone 2 Return Way", "Shaft 1 North"],
            "Zone 2 Return Way": ["Level 112 Workings", "Old Stope West"],
            "Shaft 1 North": ["Level 112 Workings"],
            "Old Stope West": ["Zone 2 Return Way"]
        }
    }
}

DEFAULT_MINE: str = "Driefontein"


# =====================================================================
# 4. SURFACE ENGINE PORTAL (COMMERCIAL & COMMUNITY DOORS)
# =====================================================================

SURFACE_PORTAL_HEADER: str = "Available Thermal Output vs. Allocated Community Hubs"

# Commercial Door Configuration
COMMERCIAL_DOOR_CONFIG: Dict[str, Any] = {
    "default_heat_capacity_mw": 14.5,
    "default_discount_percent": 25.0,  # 25% discount off municipal/Eskom commercial tariff
    "mandatory_local_hiring_quota": 60.0,  # 60% minimum local workforce requirement
    "eskom_baseline_tariff_zar_kwh": 2.15,  # Standard baseline industrial/commercial electricity tariff (ZAR/kWh)
    "tppa_default_term_years": 5,
    "tppa_summary": (
        "Standard 5-year thermal Power Purchase Agreement (tPPA) with guaranteed 25% tariff "
        "discount against Eskom grid rates, fence-line thermal SLA, and verified 60% local hiring quota."
    )
}

# Community Door Configuration: Plain-language opportunity cards demonstrating Social and Labour Plan (SLP) value
COMMUNITY_OPPORTUNITY_CARDS: List[Dict[str, Any]] = [
    {
        "id": "merafong_hydroponics",
        "title": "Merafong Youth Hydroponics Agripark",
        "focus_group": "Local Youth & Women (Carletonville & Khutsong)",
        "allocated_mw": 3.5,
        "water_temp_c": "24°C – 30°C",
        "jobs_created": "45 direct full-time, 90 seasonal",
        "description": "Climate-controlled greenhouse agriculture cultivating high-value tomatoes, peppers, and leafy greens utilizing the fence-line heat exchanger loop to eliminate winter heating bills.",
        "slp_metric": "Food Security & Youth Employment"
    },
    {
        "id": "tilapia_aquaculture",
        "title": "Community Tilapia Aquaculture Facility",
        "focus_group": "Youth Cooperatives & Persons with Disabilities",
        "allocated_mw": 2.8,
        "water_temp_c": "26°C – 28°C",
        "jobs_created": "30 permanent jobs",
        "description": "Recirculating aquaculture system (RAS) maintaining optimal 27°C fingerling growth temperatures year-round using secondary warm-water return circuits without fuel combustion.",
        "slp_metric": "High-Protein Production & Inclusive Enterprise"
    },
    {
        "id": "post_harvest_drying",
        "title": "Post-Harvest Agro-Processing & Drying Hub",
        "focus_group": "Female Smallholder Farmers & Informal Traders",
        "allocated_mw": 2.2,
        "water_temp_c": "40°C – 50°C",
        "jobs_created": "25 direct jobs",
        "description": "Clean thermal warm-air drying beds for grains, dried fruit, moringa, and herbs, eliminating post-harvest spoilage and unlocking direct retail supply agreements.",
        "slp_metric": "Crop Spoilage Elimination & Women in Agriculture"
    },
    {
        "id": "sanitation_laundry",
        "title": "Eco-District Sanitation & Community Laundry Centre",
        "focus_group": "Community Micro-Enterprises & Local Clinics",
        "allocated_mw": 1.8,
        "water_temp_c": "55°C – 60°C",
        "jobs_created": "18 direct jobs",
        "description": "Low-cost industrial hot water utility serving community laundries, clinic sanitation, and micro-processing, directly displacing coal and paraffin burning in surrounding townships.",
        "slp_metric": "Public Health & Energy Poverty Relief"
    }
]


# =====================================================================
# 5. HELPER FUNCTIONS
# =====================================================================

def get_mine_config(mine_name: str) -> Dict[str, Any]:
    """Retrieve full configuration dictionary for a given mine."""
    if mine_name not in MINES_DATA:
        raise KeyError(f"Mine '{mine_name}' not found. Available mines: {list(MINES_DATA.keys())}")
    return MINES_DATA[mine_name]


def get_all_mines() -> List[str]:
    """Return ordered list of all configured mines."""
    return list(MINES_DATA.keys())


def get_mines_by_phase(phase: int) -> List[str]:
    """Return list of mine names corresponding to Phase 1 or Phase 2."""
    return [name for name, data in MINES_DATA.items() if data.get("phase") == phase]


def get_community_cards() -> List[Dict[str, Any]]:
    """Return all community opportunity cards."""
    return COMMUNITY_OPPORTUNITY_CARDS


def get_total_allocated_community_heat_mw() -> float:
    """Return the total thermal power in MW allocated across all community hubs."""
    return round(sum(card["allocated_mw"] for card in COMMUNITY_OPPORTUNITY_CARDS), 2)


def calculate_commercial_savings(
    heat_mw: float,
    discount_percent: float = COMMERCIAL_DOOR_CONFIG["default_discount_percent"],
    tariff_zar_kwh: float = COMMERCIAL_DOOR_CONFIG["eskom_baseline_tariff_zar_kwh"],
    annual_operating_hours: int = 8760
) -> Dict[str, float]:
    """
    Calculate annual energy value, off-taker savings, and mine revenue for a thermal PPA (tPPA).
    """
    annual_kwh = heat_mw * 1000.0 * annual_operating_hours
    baseline_cost_zar = annual_kwh * tariff_zar_kwh
    discount_factor = discount_percent / 100.0
    tppa_tariff_zar = tariff_zar_kwh * (1.0 - discount_factor)
    annual_savings_zar = baseline_cost_zar * discount_factor
    mine_revenue_zar = annual_kwh * tppa_tariff_zar

    return {
        "annual_thermal_kwh": annual_kwh,
        "baseline_cost_zar": baseline_cost_zar,
        "tppa_tariff_zar": round(tppa_tariff_zar, 3),
        "annual_offtaker_savings_zar": round(annual_savings_zar, 2),
        "annual_mine_revenue_zar": round(mine_revenue_zar, 2)
    }


if __name__ == "__main__":
    print(f"=== ThermalTwin Config Verified ===")
    print(f"Default Mine: {DEFAULT_MINE} ({get_mine_config(DEFAULT_MINE)['location']})")
    print(f"Statutory Wet-Bulb Limit: {STATUTORY_WET_BULB_LIMIT}°C")
    print(f"Phase 1 Mines: {get_mines_by_phase(1)}")
    print(f"Phase 2 Mines: {get_mines_by_phase(2)}")
    total_comm_mw = get_total_allocated_community_heat_mw()
    print(f"Total Community Allocation: {total_comm_mw} MWth across {len(COMMUNITY_OPPORTUNITY_CARDS)} hubs")
    savings = calculate_commercial_savings(14.5)
    print(f"Commercial Savings on 14.5 MWth: R {savings['annual_offtaker_savings_zar']:,.2f} saved annually")
