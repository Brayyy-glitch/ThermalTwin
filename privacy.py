"""
Privacy layer: worker identifiers are hashed at the edge before anything
leaves the sensor layer. Backs the POPIA claim made in app.py's Data Privacy
panel — "no PII is stored or transmitted."
 
Salt and hash length live in config.py, not here, so a salt rotation only
ever has to happen in one place — the same rule the detection thresholds
already follow (see config.py's module docstring).
"""
 
import hashlib
from config import EDGE_HASH_SALT, WORKER_HASH_LENGTH
 
 
def hash_worker_id(raw_id: str, salt: str = EDGE_HASH_SALT) -> str:
    """
    One-way hash of a raw worker identifier, applied at edge ingestion.
    Deterministic per raw_id (same worker -> same tag across timesteps)
    but not reversible back to identity.
    """
    if not raw_id:
        raise ValueError("raw_id must be a non-empty string")
    return hashlib.sha256(f"{salt}:{raw_id}".encode()).hexdigest()[:WORKER_HASH_LENGTH]
 
 
def hash_worker_ids(raw_ids: list, salt: str = EDGE_HASH_SALT) -> list:
    """Batch version of hash_worker_id — the same edge-hashing step, many workers at once."""
    return [hash_worker_id(rid, salt=salt) for rid in raw_ids]
 
 
def zone_occupancy_density(hashed_tags: list) -> int:
    """
    The only thing that should leave the edge layer per the privacy spec:
    a count of distinct hashed tags present, never the tags' source identity.
    De-duplicated with set() in case the same badge is read twice in one poll
    (e.g. two sensors both pick it up).
    """
    return len(set(hashed_tags))
 
 
def zone_occupancy_report(raw_ids_by_zone: dict) -> dict:
    """
    Multi-zone convenience wrapper: hashes every zone's raw IDs at the edge
    and returns only the resulting counts, so a caller (e.g. app.py) never
    has to hold a zone's raw IDs and its occupancy count side by side.
    """
    return {
        zone: zone_occupancy_density(hash_worker_ids(raw_ids))
        for zone, raw_ids in raw_ids_by_zone.items()
    }
 
 
if __name__ == "__main__":
    sample_ids = [f"W-{i}" for i in range(5)]
    hashed = hash_worker_ids(sample_ids)
    print("Raw IDs (never transmitted):", sample_ids)
    print("Hashed tags (what the platform actually sees):", hashed)
    print("Zone occupancy density:", zone_occupancy_density(hashed))
 
    # Self-checks: hashing must be deterministic and must not collide trivially.
    assert hash_worker_id("W-0") == hash_worker_id("W-0"), "hash must be deterministic"
    assert hash_worker_id("W-0") != hash_worker_id("W-1"), "different workers must hash differently"
    assert zone_occupancy_density(hash_worker_ids(["W-0", "W-0", "W-1"])) == 2, "duplicate reads must not double-count"
    try:
        hash_worker_id("")
        raise AssertionError("empty raw_id should have raised ValueError")
    except ValueError:
        pass
    print("\nSelf-check passed: deterministic, salted, de-duplicated, validates input.")
 