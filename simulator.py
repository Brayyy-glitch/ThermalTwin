"""
ThermalTwin (MineFlow AI) — Simulation Layer
===========================================

This module generates synthetic telemetry for the underground heating and safety demo.
It is intentionally physics-aware but not a trained ML model: the "predicted" baseline is
scripted from mine configuration and the "reported" values can be intentionally perturbed to
simulate sensor drift or spoofing.

The data contract is designed to be consumed by:
- anomaly.py: statistical and physics-based classification
- privacy.py: worker-tag hashing and zone occupancy density
- app.py: charting and dashboard display
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from config import (
    DEFAULT_MINE,
    PHYSICS_MISMATCH_THRESHOLD_C,
    PREDICTION_LEAD_TIME_MINUTES,
    SIGNATURE_DRIFT,
    SIGNATURE_DRIFT_MIN_TIMESTEPS,
    SIGNATURE_JUMP,
    SIGNATURE_JUMP_THRESHOLD_C,
    SIGNATURE_NORMAL,
    STATUTORY_WET_BULB_LIMIT,
    TELEMETRY_INTERVAL_SECONDS,
    WET_BULB_CAUTION_LIMIT,
    get_mine_config,
)
from privacy import hash_worker_ids


def _default_zone_names(mine_name: str) -> List[str]:
    """Return the configured default zones for a mine."""
    mine_cfg = get_mine_config(mine_name)
    return list(mine_cfg.get("default_zones", ["Zone 1", "Zone 2", "Zone 3"]))


def _baseline_temperature_c(mine_name: str, zone_index: int, sample_index: int) -> float:
    """Generate a physically plausible baseline for a mine/zone at a given timestep."""
    mine_cfg = get_mine_config(mine_name)
    depth_m = float(mine_cfg["depth_meters"])
    vrt_c = float(mine_cfg["vrt_celsius"])
    noise_cycle = 0.9 * np.sin(sample_index / 10.0 + zone_index * 1.7)
    depth_component = (depth_m / 120.0)  # rough scale so deeper mines run hotter
    temporal_trend = 0.08 * (sample_index / 60.0)
    baseline = 18.0 + depth_component + (vrt_c - 60.0) * 0.18 + noise_cycle + temporal_trend
    return float(baseline)


def _wet_bulb_estimate_c(reported_temp_c: float, zone_index: int, occupancy_count: int, sample_index: int) -> float:
    """Estimate a wet-bulb-like safety reading from the reported underground temperature."""
    occupancy_pressure = 0.18 * occupancy_count
    oscillation = 0.6 * np.sin(sample_index / 9.0 + zone_index)
    estimate = 14.0 + 0.34 * reported_temp_c + occupancy_pressure + oscillation
    return float(np.clip(estimate, 18.0, 33.0))


def _worker_snapshot(zone_name: str, sample_index: int, occupancy_base: int = 8) -> Dict[str, object]:
    """Create realistic worker badge IDs and occupancy density for a time slice."""
    raw_ids = [
        f"{zone_name.replace(' ', '').upper()}-{sample_index}-{i}"
        for i in range(max(3, int(np.random.poisson(occupancy_base))))
    ]
    hashed = hash_worker_ids(raw_ids)
    return {
        "raw_worker_ids": raw_ids,
        "hashed_worker_tags": hashed,
        "zone_occupancy_count": len(set(hashed)),
    }


def _build_tamper_offset(
    tamper_mode: str,
    sample_index: int,
    tamper_start_index: int,
) -> float:
    """Construct an offset that reflects either a gradual drift or abrupt jump."""
    if sample_index < tamper_start_index:
        return 0.0

    elapsed = sample_index - tamper_start_index
    mode = (tamper_mode or SIGNATURE_JUMP).upper()

    if mode == SIGNATURE_DRIFT:
        return 0.3 + (elapsed * 0.08)
    if mode == SIGNATURE_JUMP:
        return 1.6 + 0.7 * np.sin(elapsed / 3.0)
    return 0.9 + 0.05 * elapsed


def simulate_mine_telemetry(
    mine_name: str = DEFAULT_MINE,
    num_samples: int = 180,
    zones: Optional[Sequence[str]] = None,
    inject_physics_mismatch: bool = False,
    tamper_mode: str = SIGNATURE_JUMP,
    tamper_zone: Optional[str] = None,
    tamper_start_sample: int = 75,
    start_time: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Generate synthetic telemetry for a specific mine.

    Returns a DataFrame with columns suitable for downstream anomaly detection and dashboard display.
    """
    mine_cfg = get_mine_config(mine_name)
    active_zones = list(zones) if zones is not None else list(mine_cfg.get("default_zones", []))
    if not active_zones:
        active_zones = _default_zone_names(mine_name)

    if start_time is None:
        start_time = pd.Timestamp.now(tz=None).floor("min")

    records: List[Dict[str, object]] = []

    for sample_index in range(num_samples):
        for zone_index, zone_name in enumerate(active_zones):
            baseline = _baseline_temperature_c(mine_name, zone_index, sample_index)
            natural_variation = float(np.random.normal(0.0, 0.38))
            predicted_temp_c = baseline + natural_variation

            worker_snapshot = _worker_snapshot(zone_name, sample_index, occupancy_base=7 + zone_index)
            occupancy_count = int(worker_snapshot["zone_occupancy_count"])

            tamper_offset = 0.0
            tamper_applied = False
            if inject_physics_mismatch and (tamper_zone is None or tamper_zone == zone_name):
                tamper_offset = _build_tamper_offset(tamper_mode, sample_index, tamper_start_sample)
                tamper_applied = tamper_offset > 0.0

            reported_temp_c = predicted_temp_c + tamper_offset + float(np.random.normal(0.0, 0.12))
            mismatch_c = abs(reported_temp_c - predicted_temp_c)

            if mismatch_c >= PHYSICS_MISMATCH_THRESHOLD_C:
                if tamper_offset >= SIGNATURE_JUMP_THRESHOLD_C:
                    anomaly_signature = SIGNATURE_JUMP
                else:
                    anomaly_signature = SIGNATURE_DRIFT
            else:
                anomaly_signature = SIGNATURE_NORMAL

            # A simple zone-level alert signal so the dashboard can emphasize abnormal zones.
            alert_level = "normal"
            if anomaly_signature == SIGNATURE_JUMP:
                alert_level = "critical"
            elif anomaly_signature == SIGNATURE_DRIFT:
                alert_level = "warning"

            wet_bulb_c = _wet_bulb_estimate_c(reported_temp_c, zone_index, occupancy_count, sample_index)
            timestamp = start_time + pd.Timedelta(seconds=sample_index * TELEMETRY_INTERVAL_SECONDS)

            records.append(
                {
                    "timestamp": timestamp,
                    "mine": mine_name,
                    "zone": zone_name,
                    "sample_index": sample_index,
                    "predicted_temp_c": round(float(predicted_temp_c), 3),
                    "reported_temp_c": round(float(reported_temp_c), 3),
                    "temperature_delta_c": round(float(reported_temp_c - predicted_temp_c), 3),
                    "physics_mismatch_c": round(float(mismatch_c), 3),
                    "wet_bulb_c": round(float(wet_bulb_c), 3),
                    "tamper_applied": tamper_applied,
                    "tamper_mode": tamper_mode if tamper_applied else SIGNATURE_NORMAL,
                    "anomaly_signature": anomaly_signature,
                    "alert_level": alert_level,
                    "zone_occupancy_count": occupancy_count,
                    "raw_worker_ids": worker_snapshot["raw_worker_ids"],
                    "hashed_worker_tags": worker_snapshot["hashed_worker_tags"],
                    "prediction_lead_minutes": PREDICTION_LEAD_TIME_MINUTES,
                    "statutory_wet_bulb_limit_c": STATUTORY_WET_BULB_LIMIT,
                    "wet_bulb_caution_limit_c": WET_BULB_CAUTION_LIMIT,
                }
            )

    df = pd.DataFrame(records)
    if df.empty:
        return df

    df = df.sort_values(["mine", "zone", "timestamp"]).reset_index(drop=True)
    return df


def forecast_zone_temperature(
    reported_temps: List[float],
    lead_minutes: int = PREDICTION_LEAD_TIME_MINUTES,
    lookback: int = 10,
) -> Dict[str, Any]:
    """
    Forecast underground zone temperature ``lead_minutes`` ahead using ordinary
    least-squares linear regression over the most recent ``lookback`` samples
    (each sample = 1 minute at TELEMETRY_INTERVAL_SECONDS = 60 s).

    Why linear extrapolation?
    -------------------------
    Heat accumulation in a stope follows a near-linear ramp between ventilation
    cycles.  A linear model over 10 samples gives a defensible, auditable signal
    without requiring a trained model.  The residual standard error of the fit
    becomes the ±1σ uncertainty band reported alongside the point forecast.

    Returns
    -------
    dict with keys:
        forecast_temp_c     – point estimate at t + lead_minutes
        sigma_c             – ±1σ uncertainty from OLS residuals
        upper_c             – forecast_temp_c + sigma_c
        lower_c             – forecast_temp_c - sigma_c
        slope_c_per_min     – trend slope (positive = heating up)
        r_squared           – goodness-of-fit of the linear model
        is_breach_predicted – True if upper_c >= STATUTORY_WET_BULB_LIMIT
        breach_margin_c     – how far upper_c sits above/below the 28°C limit
        samples_used        – number of samples actually used (≤ lookback)
        lead_minutes        – echo of the requested horizon
    """
    n_available = len(reported_temps)
    samples_used = min(lookback, n_available)
    window = reported_temps[-samples_used:]

    # x = time in minutes (0 .. samples_used-1)
    x = list(range(samples_used))
    x_mean = sum(x) / samples_used
    y_mean = sum(window) / samples_used

    # OLS coefficients
    ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, window))
    ss_xx = sum((xi - x_mean) ** 2 for xi in x)

    if ss_xx < 1e-9:
        # Flat signal — no trend, forecast = last value
        slope = 0.0
        intercept = y_mean
    else:
        slope = ss_xy / ss_xx
        intercept = y_mean - slope * x_mean

    # Residual standard error (σ)
    residuals_sq = [(window[i] - (intercept + slope * x[i])) ** 2 for i in range(samples_used)]
    mse = sum(residuals_sq) / max(1, samples_used - 2)
    sigma = mse ** 0.5

    # R² (goodness of fit)
    ss_tot = sum((yi - y_mean) ** 2 for yi in window)
    r_squared = round(1.0 - sum(residuals_sq) / ss_tot, 4) if ss_tot > 1e-9 else 1.0

    # Forecast at t + lead_minutes (x_forecast extends beyond the window by lead_minutes)
    x_forecast = (samples_used - 1) + lead_minutes
    forecast_c = intercept + slope * x_forecast

    # Wet-bulb approximation for the forecasted dry-bulb temperature
    # (reuses the same simple 0.34 factor from _wet_bulb_estimate_c with no occupancy term)
    forecast_wb_c = 14.0 + 0.34 * forecast_c

    is_breach = forecast_wb_c >= STATUTORY_WET_BULB_LIMIT
    breach_margin = round(forecast_wb_c - STATUTORY_WET_BULB_LIMIT, 2)

    return {
        "forecast_temp_c": round(forecast_c, 2),
        "forecast_wb_c": round(forecast_wb_c, 2),
        "sigma_c": round(sigma, 3),
        "upper_c": round(forecast_c + sigma, 2),
        "lower_c": round(forecast_c - sigma, 2),
        "slope_c_per_min": round(slope, 4),
        "r_squared": r_squared,
        "is_breach_predicted": is_breach,
        "breach_margin_c": breach_margin,
        "samples_used": samples_used,
        "lead_minutes": lead_minutes,
    }


def generate_demo_data(
    mine_name: str = DEFAULT_MINE,
    inject_physics_mismatch: bool = True,
    tamper_mode: str = SIGNATURE_JUMP,
    tamper_zone: Optional[str] = None,
) -> pd.DataFrame:
    """Convenience wrapper for the primary demo flow described in the README."""
    active_zones = _default_zone_names(mine_name)
    if tamper_zone is None and len(active_zones) > 1:
        tamper_zone = active_zones[1]

    return simulate_mine_telemetry(
        mine_name=mine_name,
        num_samples=180,
        zones=active_zones,
        inject_physics_mismatch=inject_physics_mismatch,
        tamper_mode=tamper_mode,
        tamper_zone=tamper_zone,
        tamper_start_sample=75,
    )


if __name__ == "__main__":
    print("=== ThermalTwin simulator smoke test ===")
    demo_df = generate_demo_data(inject_physics_mismatch=True, tamper_mode=SIGNATURE_JUMP)
    print(demo_df[["timestamp", "mine", "zone", "predicted_temp_c", "reported_temp_c", "anomaly_signature"]].head(10).to_string(index=False))

    assert {"mine", "zone", "predicted_temp_c", "reported_temp_c", "anomaly_signature"}.issubset(demo_df.columns)
    assert demo_df["anomaly_signature"].isin([SIGNATURE_NORMAL, SIGNATURE_DRIFT, SIGNATURE_JUMP]).all()
    assert demo_df["reported_temp_c"].notna().all()
    assert demo_df["zone_occupancy_count"].gt(0).all()

    if demo_df["anomaly_signature"].eq(SIGNATURE_JUMP).any():
        print(f"Detected {int(demo_df['anomaly_signature'].eq(SIGNATURE_JUMP).sum())} jump-signature samples.")
    else:
        raise AssertionError("Expected at least one jump-signature sample during tamper injection.")

    print("Simulated telemetry validated successfully.")
