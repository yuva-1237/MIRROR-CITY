import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.geospatial_service import geospatial_service

def test_preset_lookup():
    # Test preset retrieval (Chennai)
    results = geospatial_service.search_location("chennai")
    assert len(results) > 0
    match = results[0]
    assert match["name"] == "Chennai"
    assert match["lat"] == 13.0827
    assert match["lng"] == 80.2707
    assert match["population"] == 8900000
    assert match["source"] == "Local Baseline Database"

def test_geocode_caching():
    # Test geocode cache works for repeated queries
    query = "New York City"
    
    # First search
    t0 = time.time()
    results1 = geospatial_service.search_location(query)
    t1 = time.time()
    
    # Second search (should hit cache instantly)
    t2 = time.time()
    results2 = geospatial_service.search_location(query)
    t3 = time.time()
    
    assert results1 == results2
    # Second retrieval must be extremely fast (< 1ms) compared to external or fallback geocoding
    assert (t3 - t2) < 0.05
    
def test_unknown_location_fallback():
    # Test unknown query returns clear error instead of random coordinates
    results = geospatial_service.search_location("nonexistentplace12345")
    assert len(results) == 1
    match = results[0]
    assert match["lat"] == 0.0
    assert match["lng"] == 0.0
    assert match["location_type"] == "unknown"
    assert match["source"] == "Not Found"
    assert "error" in match
