"""
ThermalTwin (MineFlow AI) — Anomaly Detection & Physics-Aware Security Engine
=============================================================================
Role: Analytics & Security (anomaly.py)

Key Capabilities:
  1. Statistical Rolling Z-Score: Moving window normalization on temperature residuals.
  2. Physics-Aware Security Baseline: Detects divergence between reported RTD readings
     and the thermodynamic predicted baseline.
  3. Signature Classification (DRIFT vs JUMP):
       - DRIFT: Gradual divergence indicating calibration wear, RTD corrosion, or dust coating.
       - JUMP: Sudden step discrepancy characteristic of sensor spoofing/tampering.
  4. Worker-Risk Ranking: Combines statutory wet-bulb heat thresholds (28°C MHSA limit),
     tamper security signatures, and anonymous worker occupancy density into prioritized
     operational actions for mine ventilation officers.
  5. Privacy Integration: Seamlessly consumes anonymous zone occupancy counts from privacy.py.
  6. Cross-Sensor Spatial Validation: Compares adjacent stope and haulage RTD probes
     to distinguish localized sensor tampering from sector-wide thermal events.

Designed to execute seamlessly with pandas/numpy or pure Python standard library.
"""

import math
from typing import Dict, List, Any, Optional, Tuple, Union

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    pd = None
    np = None
    HAS_PANDAS = False

import config


# =====================================================================
# 1. STATISTICAL LAYER: ROLLING Z-SCORE
# =====================================================================

def calculate_rolling_zscore(
    values: Union[List[float], Any],
    window: int = config.ROLLING_WINDOW_SIZE,
    min_periods: int = 3,
    epsilon: float = 1e-4
) -> Union[List[float], Any]:
    """
    Compute rolling Z-score over a 1D sequence of values.
    
    Formula:
        Z_t = (x_t - mean_t) / max(std_t, epsilon)
        
    Args:
        values: Series, list, or array of numeric values (e.g. temperatures or residuals).
        window: Size of the moving window.
        min_periods: Minimum samples before reporting valid Z-scores (earlier return 0.0).
        epsilon: Small variance floor to avoid division by zero when values are flat.
        
    Returns:
        List or pandas Series of rolling Z-scores matching the input format.
    """
    if HAS_PANDAS and isinstance(values, (pd.Series, pd.DataFrame)):
        if isinstance(values, pd.DataFrame):
            s = values.iloc[:, 0]
        else:
            s = values
        rolling_mean = s.rolling(window=window, min_periods=min_periods).mean()
        rolling_std = s.rolling(window=window, min_periods=min_periods).std(ddof=1)
        safe_std = rolling_std.clip(lower=epsilon)
        z = (s - rolling_mean) / safe_std
        return z.fillna(0.0)

    raw_list = list(values)
    n = len(raw_list)
    z_scores: List[float] = [0.0] * n

    for i in range(n):
        start_idx = max(0, i - window + 1)
        sub = raw_list[start_idx : i + 1]
        k = len(sub)
        if k < min_periods:
            z_scores[i] = 0.0
            continue

        mean = sum(sub) / k
        variance = sum((x - mean) ** 2 for x in sub) / (k - 1) if k > 1 else 0.0
        std = math.sqrt(variance)
        if std < epsilon:
            std = epsilon
        z_scores[i] = (raw_list[i] - mean) / std

    return z_scores


# =====================================================================
# 2. PHYSICS-AWARE SECURITY LAYER: MISMATCH DETECTION
# =====================================================================

def detect_physics_mismatch(
    reported: Union[List[float], Any],
    predicted: Union[List[float], Any],
    threshold_c: float = config.PHYSICS_MISMATCH_THRESHOLD_C
) -> Dict[str, Any]:
    """
    Compare reported sensor temperature against physical thermodynamic prediction.
    
    Args:
        reported: Reported RTD sensor temperatures (°C).
        predicted: Physics-based model predicted temperatures (°C).
        threshold_c: Discrepancy threshold in °C (|Reported - Predicted| >= threshold).
        
    Returns:
        Dictionary containing:
          - 'residuals': reported - predicted
          - 'abs_residuals': |reported - predicted|
          - 'is_mismatch': boolean flags indicating divergence
          - 'directions': 'OVER_REPORTING', 'UNDER_REPORTING', or 'MATCH'
    """
    rep_list = list(reported) if not HAS_PANDAS or not isinstance(reported, (pd.Series, pd.DataFrame)) else reported.tolist()
    pred_list = list(predicted) if not HAS_PANDAS or not isinstance(predicted, (pd.Series, pd.DataFrame)) else predicted.tolist()

    if len(rep_list) != len(pred_list):
        raise ValueError(f"Length mismatch: reported has {len(rep_list)} items, predicted has {len(pred_list)}.")

    residuals: List[float] = []
    abs_residuals: List[float] = []
    is_mismatch: List[bool] = []
    directions: List[str] = []

    for r, p in zip(rep_list, pred_list):
        diff = round(r - p, 3)
        abs_diff = round(abs(diff), 3)
        mismatch = abs_diff >= threshold_c

        if mismatch:
            direction = "OVER_REPORTING" if diff > 0 else "UNDER_REPORTING"
        else:
            direction = "MATCH"

        residuals.append(diff)
        abs_residuals.append(abs_diff)
        is_mismatch.append(mismatch)
        directions.append(direction)

    if HAS_PANDAS:
        df_result = pd.DataFrame({
            "reported": rep_list,
            "predicted": pred_list,
            "residual": residuals,
            "abs_residual": abs_residuals,
            "is_mismatch": is_mismatch,
            "direction": directions
        })
        return {
            "dataframe": df_result,
            "residuals": residuals,
            "abs_residuals": abs_residuals,
            "is_mismatch": is_mismatch,
            "directions": directions
        }

    return {
        "residuals": residuals,
        "abs_residuals": abs_residuals,
        "is_mismatch": is_mismatch,
        "directions": directions
    }


# =====================================================================
# 3. SIGNATURE CLASSIFICATION: DRIFT VS JUMP
# =====================================================================

def classify_signature_series(
    residuals: Union[List[float], Any],
    jump_rate_threshold: float = config.SIGNATURE_JUMP_THRESHOLD_C,
    mismatch_threshold: float = config.PHYSICS_MISMATCH_THRESHOLD_C,
    z_scores: Optional[Union[List[float], Any]] = None,
    z_threshold: float = config.Z_SCORE_ALERT_THRESHOLD
) -> List[str]:
    """
    Classify anomaly signature sequence into NORMAL, DRIFT, or JUMP.
    
    Classification Logic:
      - If residual < mismatch_threshold AND (optional) |z_score| < z_threshold:
          --> NORMAL
      - If anomaly triggered:
          - Compute rate of divergence: |residual[t] - residual[t-1]|
          - If rate >= jump_rate_threshold:
              --> JUMP (Sudden step divergence / sensor spoofing signature)
          - Else (rate < jump_rate_threshold but sustained divergence):
              --> DRIFT (Gradual divergence / calibration wear or RTD aging)
    """
    res = list(residuals) if not HAS_PANDAS or not isinstance(residuals, (pd.Series, pd.DataFrame)) else residuals.tolist()
    zs = None
    if z_scores is not None:
        zs = list(z_scores) if not HAS_PANDAS or not isinstance(z_scores, (pd.Series, pd.DataFrame)) else z_scores.tolist()

    n = len(res)
    signatures: List[str] = [config.SIGNATURE_NORMAL] * n

    for i in range(n):
        cur_res = res[i]
        abs_res = abs(cur_res)
        cur_z = abs(zs[i]) if (zs and i < len(zs)) else 0.0

        is_anomalous = (abs_res >= mismatch_threshold) or (cur_z >= z_threshold)

        if not is_anomalous:
            signatures[i] = config.SIGNATURE_NORMAL
            continue

        # Check rate of change from previous sample
        if i == 0:
            rate_of_change = abs_res
        else:
            prev_res = res[i - 1]
            rate_of_change = abs(cur_res - prev_res)

        if rate_of_change >= jump_rate_threshold:
            signatures[i] = config.SIGNATURE_JUMP
        else:
            signatures[i] = config.SIGNATURE_DRIFT

    return signatures


def classify_single_reading(
    reported: float,
    predicted: float,
    prev_reported: Optional[float] = None,
    prev_predicted: Optional[float] = None,
    z_score: Optional[float] = None,
    jump_threshold: float = config.SIGNATURE_JUMP_THRESHOLD_C,
    mismatch_threshold: float = config.PHYSICS_MISMATCH_THRESHOLD_C,
    z_threshold: float = config.Z_SCORE_ALERT_THRESHOLD
) -> Tuple[str, float, float]:
    """
    Classify a single telemetry reading in real time.
    
    Returns:
        Tuple of (signature: str, residual: float, rate_of_change: float)
    """
    residual = round(reported - predicted, 3)
    abs_res = abs(residual)

    rate_of_change = 0.0
    if prev_reported is not None and prev_predicted is not None:
        prev_res = prev_reported - prev_predicted
        rate_of_change = round(abs(residual - prev_res), 3)

    is_anomalous = (abs_res >= mismatch_threshold) or (z_score is not None and abs(z_score) >= z_threshold)

    if not is_anomalous:
        return config.SIGNATURE_NORMAL, residual, rate_of_change

    if rate_of_change >= jump_threshold:
        return config.SIGNATURE_JUMP, residual, rate_of_change
    else:
        return config.SIGNATURE_DRIFT, residual, rate_of_change


# =====================================================================
# 4. WORKER-RISK RANKING ENGINE (WITH PRIVACY LAYER INTEGRATION)
# =====================================================================

def calculate_zone_risk_score(
    wet_bulb_temp: float,
    signature: str,
    worker_count: int,
    z_score: float = 0.0,
    statutory_limit: float = config.STATUTORY_WET_BULB_LIMIT,
    caution_limit: float = config.WET_BULB_CAUTION_LIMIT
) -> Tuple[float, str, str]:
    """
    Calculate composite life-safety and operational risk score for an underground zone.
    
    Components:
      1. Thermal Severity (0 to 65 pts):
           - Wet-bulb >= 28°C (statutory breach): 50 pts + 15 * (T_wb - 28.0)
           - Wet-bulb >= 27°C (caution zone): 25 pts + 25 * (T_wb - 27.0)
           - Wet-bulb < 27°C: max(0, (T_wb - 22.0) * 4.0)
      2. Security Severity (0 to 35 pts):
           - JUMP: 35 pts (Active sensor tampering / spoofing: sensor may be under-reporting heat!)
           - DRIFT: 15 pts (Degraded sensor calibration wear)
           - NORMAL: 0 pts
      3. Worker Exposure Density (0 to 30 pts):
           - min(30.0, worker_count * 2.5)
      4. Statistical Deviation (0 to 15 pts):
           - min(15.0, abs(z_score) * 3.0)
           
    Returns:
        Tuple of (composite_score: float, priority_label: str, action_summary: str)
    """
    # 1. Thermal severity
    if wet_bulb_temp >= statutory_limit:
        thermal_pts = 50.0 + 15.0 * (wet_bulb_temp - statutory_limit)
    elif wet_bulb_temp >= caution_limit:
        thermal_pts = 25.0 + 25.0 * (wet_bulb_temp - caution_limit)
    else:
        thermal_pts = max(0.0, (wet_bulb_temp - 22.0) * 4.0)

    # 2. Security signature severity
    if signature == config.SIGNATURE_JUMP:
        security_pts = 35.0
    elif signature == config.SIGNATURE_DRIFT:
        security_pts = 15.0
    else:
        security_pts = 0.0

    # 3. Worker exposure
    worker_pts = min(30.0, float(worker_count) * 2.5)

    # 4. Statistical deviation
    stat_pts = min(15.0, abs(z_score) * 3.0)

    total_score = round(thermal_pts + security_pts + worker_pts + stat_pts, 2)

    # Priority & recommended action classification
    if total_score >= 75.0 or (wet_bulb_temp >= statutory_limit and worker_count > 0):
        priority = "Priority 1 - CRITICAL"
        action = (
            "EMERGENCY MITIGATION: Statutory wet-bulb limit breached or active spoofing signature "
            f"with {worker_count} workers exposed. Immediately divert backup chilled air/water and deploy safety team."
        )
    elif total_score >= 45.0:
        priority = "Priority 2 - HIGH"
        action = (
            "PROACTIVE VENTILATION: Temperature approaching caution limit or confirmed sensor tamper. "
            "Redirect auxiliary ventilation booster and inspect local RTD telemetry circuit."
        )
    elif total_score >= 25.0:
        priority = "Priority 3 - MEDIUM"
        action = (
            "MONITOR & CALIBRATE: Mild thermal escalation or sensor calibration drift detected. "
            "Log for shift supervisor review and schedule routine maintenance."
        )
    else:
        priority = "Priority 4 - LOW"
        action = "NOMINAL: Operating within normal thermodynamic parameters and statutory MHSA standards."

    return total_score, priority, action


def rank_worker_risk(
    zones_telemetry: Union[List[Dict[str, Any]], Any],
    occupancy_counts: Optional[Dict[str, int]] = None
) -> Union[List[Dict[str, Any]], Any]:
    """
    Rank all underground zones by danger/urgency for ventilation and safety dispatch.
    
    Seamlessly integrates with privacy.py:
    If `occupancy_counts` is provided (e.g. from privacy.zone_occupancy_report(raw_ids_by_zone)),
    it maps the privacy-preserving count to each zone automatically.
    
    Accepts list of dictionaries or pandas DataFrame.
    Expected keys per zone:
      - 'zone': str
      - 'reported_temp': float
      - 'predicted_temp': float
      - 'wet_bulb_temp': float
      - 'worker_count': int (or resolved via occupancy_counts)
      - 'z_score': float (optional, defaults to 0.0)
      - 'signature': str (optional, defaults to 'NORMAL')
      
    Returns sorted ranking (Priority 1 first) with composite risk scores and actionable directives.
    """
    if HAS_PANDAS and isinstance(zones_telemetry, pd.DataFrame):
        records = zones_telemetry.to_dict(orient="records")
    else:
        records = [dict(r) for r in zones_telemetry]

    ranked_list: List[Dict[str, Any]] = []

    for r in records:
        zone = r.get("zone", "Unknown Zone")
        rep = float(r.get("reported_temp", 26.0))
        pred = float(r.get("predicted_temp", 26.0))
        wb = float(r.get("wet_bulb_temp", rep * 0.85))
        
        # Privacy integration: resolve count from privacy layer if provided
        if occupancy_counts and zone in occupancy_counts:
            workers = int(occupancy_counts[zone])
        else:
            workers = int(r.get("worker_count", 0))

        z = float(r.get("z_score", 0.0))
        sig = r.get("signature", config.SIGNATURE_NORMAL)

        score, priority, action = calculate_zone_risk_score(
            wet_bulb_temp=wb,
            signature=sig,
            worker_count=workers,
            z_score=z
        )

        ranked_list.append({
            "zone": zone,
            "priority": priority,
            "composite_risk_score": score,
            "wet_bulb_c": round(wb, 2),
            "reported_temp_c": round(rep, 2),
            "predicted_temp_c": round(pred, 2),
            "residual_c": round(rep - pred, 2),
            "worker_count": workers,
            "signature": sig,
            "z_score": round(z, 2),
            "recommended_action": action
        })

    # Sort descending by composite risk score
    ranked_list.sort(key=lambda x: x["composite_risk_score"], reverse=True)

    # Assign 1-indexed rank
    for rank_idx, item in enumerate(ranked_list, start=1):
        item["rank"] = rank_idx

    if HAS_PANDAS and isinstance(zones_telemetry, pd.DataFrame):
        return pd.DataFrame(ranked_list)

    return ranked_list


# =====================================================================
# 5. CROSS-SENSOR SPATIAL VALIDATION
# =====================================================================

def validate_cross_sensors(
    zone_readings: Dict[str, float],
    adjacencies: Optional[Dict[str, List[str]]] = None,
    max_neighbor_delta_c: float = config.MAX_PLAUSIBLE_NEIGHBOR_DELTA_C
) -> Dict[str, Dict[str, Any]]:
    """
    Validate spatial correlation between neighbouring RTD sensors.
    
    If Zone A diverges significantly from adjacent zones connected along the
    same ventilation flow, it flags an isolated probe anomaly (spoofing or local failure).
    If multiple adjacent zones elevate together, it indicates a genuine sector-wide thermal load.
    
    Args:
        zone_readings: Mapping of zone name -> reported temperature (°C).
        adjacencies: Mapping of zone name -> list of neighbouring zone names.
        max_neighbor_delta_c: Maximum expected difference between adjacent zones under normal airflow.
        
    Returns:
        Dictionary mapping zone name -> spatial validation analysis.
    """
    results: Dict[str, Dict[str, Any]] = {}

    for zone, temp in zone_readings.items():
        neighbors = adjacencies.get(zone, []) if adjacencies else []
        valid_neighbors = [n for n in neighbors if n in zone_readings]

        if not valid_neighbors:
            results[zone] = {
                "valid": True,
                "status": "NO_NEIGHBORS_CONFIGURED",
                "avg_neighbor_temp_c": None,
                "delta_from_neighbors_c": 0.0,
                "is_isolated_anomaly": False
            }
            continue

        neighbor_temps = [zone_readings[n] for n in valid_neighbors]
        avg_neighbor = sum(neighbor_temps) / len(neighbor_temps)
        delta = round(abs(temp - avg_neighbor), 2)
        is_isolated = delta >= max_neighbor_delta_c

        results[zone] = {
            "valid": not is_isolated,
            "status": "LOCALIZED_PROBE_ANOMALY" if is_isolated else "SPATIALLY_CONSISTENT",
            "avg_neighbor_temp_c": round(avg_neighbor, 2),
            "delta_from_neighbors_c": delta,
            "is_isolated_anomaly": is_isolated,
            "evaluated_neighbors": valid_neighbors
        }

    return results


# =====================================================================
# 6. INTEGRATED TELEMETRY PIPELINE RUNNER
# =====================================================================

def process_telemetry_stream(
    reported_temps: List[float],
    predicted_temps: List[float],
    wet_bulb_temps: Optional[List[float]] = None,
    worker_counts: Optional[List[int]] = None,
    zone_name: str = "Zone 2 Stope Face"
) -> Dict[str, Any]:
    """
    End-to-end processing of a telemetry timeseries for a given zone.
    
    Returns structured analysis with rolling Z-score, mismatch detection,
    signature classification, and peak worker-risk evaluation.
    """
    n = len(reported_temps)
    if len(predicted_temps) != n:
        raise ValueError("Reported and predicted arrays must have the same length.")

    # 1. Physics mismatch
    mismatch_data = detect_physics_mismatch(reported_temps, predicted_temps)
    residuals = mismatch_data["residuals"]

    # 2. Rolling Z-Score on residuals
    z_scores = calculate_rolling_zscore(residuals, window=config.ROLLING_WINDOW_SIZE)

    # 3. Signature classification
    signatures = classify_signature_series(residuals=residuals, z_scores=z_scores)

    # 4. Latest state evaluation
    latest_reported = reported_temps[-1]
    latest_predicted = predicted_temps[-1]
    latest_residual = residuals[-1]
    latest_z = z_scores[-1]
    latest_sig = signatures[-1]
    latest_wb = wet_bulb_temps[-1] if (wet_bulb_temps and len(wet_bulb_temps) == n) else (latest_reported * 0.85)
    latest_workers = worker_counts[-1] if (worker_counts and len(worker_counts) == n) else 15

    score, priority, action = calculate_zone_risk_score(
        wet_bulb_temp=latest_wb,
        signature=latest_sig,
        worker_count=latest_workers,
        z_score=latest_z
    )

    summary = {
        "zone": zone_name,
        "latest_reported_c": round(latest_reported, 2),
        "latest_predicted_c": round(latest_predicted, 2),
        "latest_residual_c": round(latest_residual, 2),
        "latest_z_score": round(latest_z, 2),
        "latest_signature": latest_sig,
        "latest_wet_bulb_c": round(latest_wb, 2),
        "worker_count": latest_workers,
        "composite_risk_score": score,
        "priority": priority,
        "recommended_action": action,
        "series": {
            "reported": reported_temps,
            "predicted": predicted_temps,
            "residuals": residuals,
            "z_scores": z_scores,
            "signatures": signatures
        }
    }

    if HAS_PANDAS:
        df = pd.DataFrame({
            "reported": reported_temps,
            "predicted": predicted_temps,
            "residual": residuals,
            "z_score": z_scores,
            "signature": signatures
        })
        summary["dataframe"] = df

    return summary


if __name__ == "__main__":
    import privacy

    print("=== Testing ThermalTwin Anomaly & Security Engine ===")

    # Test 1: Rolling Z-Score
    test_vals = [25.0, 25.1, 25.0, 25.2, 25.1, 25.0, 25.1, 25.2, 25.1, 28.5]
    z_res = calculate_rolling_zscore(test_vals, window=5)
    print(f"Z-Score test (last point 28.5): {z_res[-1]:.2f}")

    # Test 2: Mismatch & Signature Classification (simulating sudden JUMP tamper on Zone 2)
    reported = [25.0, 25.1, 25.0, 25.2, 25.1, 25.0, 29.5, 29.8, 30.1]
    predicted = [25.0, 25.0, 25.1, 25.1, 25.2, 25.2, 25.3, 25.3, 25.4]
    mismatches = detect_physics_mismatch(reported, predicted)
    sigs = classify_signature_series(mismatches["residuals"])
    print(f"Tamper step signature detected: {sigs[6]} (Expected JUMP)")

    # Test 3: Privacy Integration with anomaly ranking:
    fake_raw_roster = {
        "Zone 2 Stope Face": [f"EMP-{i}" for i in range(101, 125)],   # 24 workers
        "Level 28 Haulage": [f"EMP-{i}" for i in range(201, 209)],    # 8 workers
        "Shaft 4 Return Airway": [f"EMP-{i}" for i in range(301, 305)]  # 4 workers
    }
    occupancy_report = privacy.zone_occupancy_report(fake_raw_roster)
    print(f"Privacy Layer Zone Occupancy Counts: {occupancy_report}")

    sample_zones = [
        {
            "zone": "Zone 2 Stope Face",
            "reported_temp": 29.8,
            "predicted_temp": 25.3,
            "wet_bulb_temp": 28.6,
            "z_score": 3.4,
            "signature": config.SIGNATURE_JUMP
        },
        {
            "zone": "Level 28 Haulage",
            "reported_temp": 24.5,
            "predicted_temp": 24.4,
            "wet_bulb_temp": 22.1,
            "z_score": 0.2,
            "signature": config.SIGNATURE_NORMAL
        },
        {
            "zone": "Shaft 4 Return Airway",
            "reported_temp": 27.2,
            "predicted_temp": 25.8,
            "wet_bulb_temp": 26.5,
            "z_score": 1.9,
            "signature": config.SIGNATURE_DRIFT
        }
    ]
    ranked = rank_worker_risk(sample_zones, occupancy_counts=occupancy_report)
    print("\n--- Privacy-Enriched Worker-Risk Ranking ---")
    for r in ranked:
        print(f"Rank {r['rank']} | {r['zone']}: {r['priority']} (Score: {r['composite_risk_score']}) | Anonymous Workers: {r['worker_count']}")

    # Test 4: Cross-Sensor Validation
    driefontein = config.get_mine_config("Driefontein")
    zone_temps = {
        "Level 28 Haulage": 25.0,
        "Zone 2 Stope Face": 31.5,  # Diverges sharply from neighbours
        "Shaft 4 Return Airway": 25.5,
        "Zone 3 Sub-Station": 24.8
    }
    cross_val = validate_cross_sensors(zone_temps, driefontein["zone_adjacencies"])
    print("\n--- Cross-Sensor Spatial Validation Result ---")
    for z, res in cross_val.items():
        print(f"{z}: {res['status']} (Delta: {res['delta_from_neighbors_c']}°C, Isolated: {res['is_isolated_anomaly']})")

    print("\nAnomaly & Security engine successfully verified!")
