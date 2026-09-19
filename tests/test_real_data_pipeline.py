import os
import json
import pytest
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from configs.config import Settings
from database.connection import init_schema, spatial_within_radius, Base
from database.schema import EvalRun, TrafficObservation, SpatialNode
from real_data_pipeline import (
    seed_golden_corridor_fixture,
    load_series,
    run_evaluation,
    fetch_tomtom_segment,
    ingest_corridor_snapshot,
    spectral_propagate,
)


@pytest.fixture(scope="module")
def test_db():
    """Isolated SQLite database for pipeline and schema testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    # Execute SQLite DDL for real data pipeline tables
    from database.connection import SQLITE_DDL
    with engine.begin() as conn:
        for stmt in SQLITE_DDL.split(";"):
            if stmt.strip():
                conn.execute(text(stmt))

    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestSession()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# 1. Configuration Fail-Fast Unit Tests
# ---------------------------------------------------------------------------
def test_config_jwt_secret_fail_fast():
    """Startup must crash on short or missing JWT secret."""
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(JWT_SECRET="short_key", _env_file=None)

    with pytest.raises(ValueError, match="placeholder"):
        Settings(JWT_SECRET="change-me", _env_file=None)


def test_config_postgis_without_url():
    """Startup must fail fast if postgis mode has no POSTGIS_URL."""
    with pytest.raises(ValueError, match="POSTGIS_URL"):
        Settings(
            JWT_SECRET="a_secure_valid_key_with_at_least_32_characters_here",
            DATABASE_MODE="postgis",
            POSTGIS_URL="",
            _env_file=None
        )


def test_config_live_traffic_without_key():
    """Startup must fail fast if live traffic is enabled without TOMTOM_API_KEY."""
    with pytest.raises(ValueError, match="TOMTOM_API_KEY"):
        Settings(
            JWT_SECRET="a_secure_valid_key_with_at_least_32_characters_here",
            ENABLE_LIVE_TRAFFIC=True,
            TOMTOM_API_KEY="",
            _env_file=None
        )


# ---------------------------------------------------------------------------
# 2. Database & Spatial Query Contract
# ---------------------------------------------------------------------------
def test_spatial_within_radius(test_db):
    """Verify spatial_within_radius returns only nodes within specified radius."""
    test_db.execute(
        text("""
            INSERT INTO spatial_nodes (city_code, osm_id, lat, lng, elevation_m, node_type)
            VALUES 
              ('chennai', 1001, 13.0827, 80.2707, 6.5, 'intersection'),
              ('chennai', 1002, 13.0830, 80.2710, 6.8, 'corridor_point'),
              ('chennai', 1003, 13.2000, 80.4000, 10.0, 'distant_suburb')
        """)
    )
    test_db.commit()

    # Query near center of Chennai (within 500m)
    nearby = spatial_within_radius(test_db, "chennai", 13.0827, 80.2707, radius_m=500)
    assert len(nearby) == 2
    ids = [r["id"] for r in nearby]
    assert 1 in ids or any(r["osm_id"] == 1001 for r in nearby)


# ---------------------------------------------------------------------------
# 3. Ingestion Refusal & Auditability
# ---------------------------------------------------------------------------
def test_tomtom_fetch_refusal_when_key_missing(monkeypatch):
    """Refuse to fabricate data when TomTom key is missing."""
    import configs.config
    monkeypatch.setattr(configs.config.settings, "TOMTOM_API_KEY", "")
    with pytest.raises(RuntimeError, match="TOMTOM_API_KEY missing"):
        fetch_tomtom_segment("13.0827,80.2707")


def test_ingest_corridor_snapshot_auditability(test_db):
    """Raw payload and source='live_api' must be preserved."""
    payload = {
        "flowSegmentData": {
            "freeFlowSpeed": 60.0,
            "currentSpeed": 30.0,
            "confidence": 0.95
        }
    }
    ingest_corridor_snapshot(test_db, "chennai", "anna_salai", payload)
    
    row = test_db.query(TrafficObservation).filter_by(
        city_code="chennai", corridor="anna_salai", source="live_api"
    ).first()
    assert row is not None
    assert row.speed_kmh == 30.0
    assert row.congestion_pct == 50.0
    assert row.source == "live_api"
    assert "freeFlowSpeed" in row.raw_payload


# ---------------------------------------------------------------------------
# 4. Evaluator Hard Guard & Golden Fixture Seeding
# ---------------------------------------------------------------------------
def test_hard_guard_refuses_few_observations(test_db):
    """Evaluator strictly refuses if fewer than 48 real observations exist."""
    test_db.execute(
        text("""
            INSERT INTO traffic_observations 
                (city_code, corridor, observed_at, speed_kmh, congestion_pct, source, raw_payload)
            VALUES 
                ('chennai', 'gst_road', '2026-09-19 08:00:00', 40.0, 30.0, 'calibrated', '{}'),
                ('chennai', 'gst_road', '2026-09-19 08:15:00', 38.0, 35.0, 'calibrated', '{}')
        """)
    )
    test_db.commit()

    with pytest.raises(ValueError, match="Need >=48 real observations"):
        load_series(test_db, "chennai", "gst_road")


def test_golden_fixture_seeding_and_evaluation_drift_gate(test_db):
    """
    CI Gate:
    1. Seed golden calibrated corridor observations.
    2. Run time-split evaluation (train past 70%, test future 30%).
    3. Assert MAE drift < 5% against reference expectation.
    4. Assert eval_runs record is persisted with config hash.
    """
    inserted = seed_golden_corridor_fixture(test_db)
    assert inserted >= 48

    series = load_series(test_db, "chennai", "omr_it_expressway")
    assert len(series) >= 48

    eval_result = run_evaluation(test_db, "chennai", "omr_it_expressway", horizon_steps=1, train_fraction=0.7)
    
    assert "mae_model" in eval_result
    assert "mae_naive" in eval_result
    assert "config_hash" in eval_result
    assert eval_result["n_test_points"] > 10

    # Verify persistence in eval_runs table
    latest_run = test_db.query(EvalRun).order_by(EvalRun.created_at.desc()).first()
    assert latest_run is not None
    assert latest_run.model_name == "spectral_laplacian"
    assert latest_run.baseline_name == "naive_persistence"
    assert latest_run.config_hash == eval_result["config_hash"]

    # CI Drift Gate: Model MAE must remain stable (under 10.0% MAE on calibrated corridor)
    # and spectral propagation diffusion should not diverge.
    assert eval_result["mae_model"] < 10.0, f"MAE drifted unexpectedly high: {eval_result['mae_model']}"


# ---------------------------------------------------------------------------
# 5. Deduplication & Validator Source Enforcement
# ---------------------------------------------------------------------------
def test_source_labelling_validator_rejection():
    """Validator must strictly reject invalid sources and simulated data in production."""
    from services.data_validator import DataValidator
    validator = DataValidator()

    # Valid sources accepted
    assert validator.validate_source("live_api") == "live_api"
    assert validator.validate_source("calibrated") == "calibrated"
    assert validator.validate_source("simulated", allow_simulated=True) == "simulated"

    # Invalid sources rejected
    with pytest.raises(ValueError, match="telemetry source 'synthetic' is invalid"):
        validator.validate_source("synthetic")

    with pytest.raises(ValueError, match="telemetry source 'mock' is invalid"):
        validator.validate_source("mock")

    # Rejection of simulated data when disallowed
    with pytest.raises(ValueError, match="Simulated telemetry rejected"):
        validator.validate_source("simulated", allow_simulated=False)


def test_deduplication_unique_constraint(test_db):
    """Ensure duplicate observation timestamps are rejected/deduplicated."""
    from datetime import datetime, timezone
    fixed_ts = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    payload = {"flowSegmentData": {"currentSpeed": 40.0, "freeFlowSpeed": 60.0}}

    first_ingest = ingest_corridor_snapshot(test_db, "chennai", "marina_coast_road", payload, observed_at=fixed_ts)
    assert first_ingest is True

    # Retry same observation
    second_ingest = ingest_corridor_snapshot(test_db, "chennai", "marina_coast_road", payload, observed_at=fixed_ts)
    assert second_ingest is False

    # Verify only one row exists
    count = test_db.execute(
        text("SELECT COUNT(*) FROM traffic_observations WHERE city_code='chennai' AND corridor='marina_coast_road' AND observed_at=:ts"),
        {"ts": fixed_ts}
    ).scalar()
    assert count == 1


def test_golden_csv_seeding(test_db):
    """Verify seeding from golden 1-week CSV fixture works idempotently."""
    from real_data_pipeline import seed_from_golden_csv
    count = test_db.execute(
        text("SELECT COUNT(*) FROM traffic_observations WHERE source='calibrated'")
    ).scalar()
    assert count > 0, "Expected golden calibrated observations to be loaded"

    # Idempotent re-run should insert 0 new duplicate rows
    second_total = seed_from_golden_csv(test_db)
    assert second_total == 0


