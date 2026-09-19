import json
import os
import sys
# Add parent directory to path so database imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from database.connection import Base, engine, SessionLocal
from database.schema import User, Scenario, MapElement, SimulationResult, AuditLog
from configs.security import hash_password

# Define coordinates centered around San Francisco
CENTER_LAT = 37.7749
CENTER_LNG = -122.4194
COORD_SPACING = 0.005  # roughly 500 meters

def generate_city_graph():
    """Generate a 6x6 grid graph representation for the baseline city 'Neo-Vidia'."""
    nodes = []
    edges = []
    
    # Types for the nodes to represent city zoning
    node_types = {
        (0, 0): "industrial", (0, 1): "industrial", (0, 2): "commercial", (0, 3): "commercial", (0, 4): "residential", (0, 5): "residential",
        (1, 0): "industrial", (1, 1): "school",      (1, 2): "commercial", (1, 3): "residential", (1, 4): "residential", (1, 5): "residential",
        (2, 0): "commercial", (2, 1): "commercial",  (2, 2): "hospital",    (2, 3): "park",        (2, 4): "residential", (2, 5): "residential",
        (3, 0): "commercial", (3, 1): "station",     (3, 2): "park",        (3, 3): "residential", (3, 4): "school",      (3, 5): "residential",
        (4, 0): "residential", (4, 1): "residential", (4, 2): "residential", (4, 3): "residential", (4, 4): "residential", (4, 5): "industrial",
        (5, 0): "residential", (5, 1): "residential", (5, 2): "residential", (5, 3): "residential", (5, 4): "industrial",  (5, 5): "industrial",
    }

    names = {
        "industrial": "Industrial Node",
        "commercial": "Downtown Crossroads",
        "residential": "Suburban Intersection",
        "school": "Academy Crossing",
        "hospital": "Medical Plaza",
        "park": "Greenway Junction",
        "station": "Transit Hub Hub"
    }

    # Generate Nodes
    for r in range(6):
        for c in range(6):
            node_id = f"node_{r}_{c}"
            lat = CENTER_LAT + (r - 2.5) * COORD_SPACING
            lng = CENTER_LNG + (c - 2.5) * COORD_SPACING
            ntype = node_types.get((r, c), "residential")
            
            nodes.append({
                "id": node_id,
                "name": f"{names[ntype]} ({r},{c})",
                "lat": lat,
                "lng": lng,
                "type": ntype,
                "population_density": 80 if ntype == "residential" else (50 if ntype == "commercial" else 30),
                "energy_demand": 75 if ntype == "industrial" else (60 if ntype == "commercial" else 40),
                "pollution_level": 90 if ntype == "industrial" else (40 if ntype == "park" else 60)
            })

    # Generate Edges (streets connecting adjacent grid cells)
    for r in range(6):
        for c in range(6):
            current_id = f"node_{r}_{c}"
            # Connect East
            if c < 5:
                east_id = f"node_{r}_{c+1}"
                edges.append({
                    "from_node": current_id,
                    "to_node": east_id,
                    "name": f"East-West St {r}",
                    "length_m": 520,
                    "speed_limit_kph": 50,
                    "lanes": 2,
                    "base_congestion": 0.3 if r in [2, 3] else 0.1
                })
            # Connect South
            if r < 5:
                south_id = f"node_{r+1}_{c}"
                edges.append({
                    "from_node": current_id,
                    "to_node": south_id,
                    "name": f"North-South Ave {c}",
                    "length_m": 550,
                    "speed_limit_kph": 50,
                    "lanes": 2,
                    "base_congestion": 0.25 if c in [2, 3] else 0.12
                })

    return {"nodes": nodes, "edges": edges}

def seed_database():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Check if users already seeded
        if db.query(User).filter_by(email="admin@mirrorcity.gov").first():
            print("Database already seeded. Skipping.")
            return

        print("Seeding users (with forced password reset on first login)...")
        users = [
            User(email="admin@mirrorcity.gov", password_hash=hash_password("adminpassword"), role="Administrator", must_change_password=True),
            User(email="planner@mirrorcity.gov", password_hash=hash_password("plannerpassword"), role="Planner", must_change_password=True),
            User(email="citizen@mirrorcity.gov", password_hash=hash_password("citizenpassword"), role="Citizen", must_change_password=True),
            User(email="officer@mirrorcity.gov", password_hash=hash_password("officerpassword"), role="Government Official", must_change_password=True),
            User(email="researcher@mirrorcity.gov", password_hash=hash_password("researcherpassword"), role="Researcher", must_change_password=True),
        ]
        db.add_all(users)
        db.commit()

        # Retrieve admin for scenario creation
        admin_user = db.query(User).filter_by(email="admin@mirrorcity.gov").first()

        print("Generating city baseline graph...")
        graph_data = generate_city_graph()
        
        # Save baseline graph structure to configs directory
        os.makedirs(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "configs")), exist_ok=True)
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "configs", "city_graph_baseline.json"))
        with open(config_path, "w") as f:
            json.dump(graph_data, f, indent=4)
        print(f"City baseline graph saved to {config_path}")

        print("Seeding baseline scenario...")
        baseline = Scenario(
            name="Baseline (Current City State)",
            description="Representing the current infrastructure, traffic networks, and carbon parameters of Neo-Vidia.",
            created_by=admin_user.id,
            status="baseline"
        )
        db.add(baseline)
        db.commit()
        db.refresh(baseline)

        # Seed map elements for the baseline (e.g. existing assets)
        print("Seeding baseline map elements...")
        elements = [
            MapElement(
                scenario_id=baseline.id,
                type="hospital",
                name="Saint Francis General Hospital",
                location_geojson=json.dumps({"type": "Point", "coordinates": [CENTER_LNG + 0.01, CENTER_LAT]}),
                radius=1500.0,
                capacity=500.0,
                cost=120000000.0,
                status="active"
            ),
            MapElement(
                scenario_id=baseline.id,
                type="metro",
                name="Downtown Central Subway Station",
                location_geojson=json.dumps({"type": "Point", "coordinates": [CENTER_LNG, CENTER_LAT]}),
                radius=800.0,
                capacity=15000.0,
                cost=75000000.0,
                status="active"
            ),
            MapElement(
                scenario_id=baseline.id,
                type="green_space",
                name="Dolores Greenway Park",
                location_geojson=json.dumps({"type": "Point", "coordinates": [CENTER_LNG - 0.005, CENTER_LAT + 0.005]}),
                radius=1000.0,
                capacity=0.0,
                cost=8000000.0,
                status="active"
            )
        ]
        db.add_all(elements)
        db.commit()

        # Seed baseline simulation results (base city metrics)
        print("Seeding baseline simulation results...")
        baseline_metrics = {
            "traffic_score": 72.5,
            "cost": 0.0,
            "carbon_footprint": 1450.2, # metric tons CO2/day
            "travel_time": 24.3, # average commute in mins
            "emergency_response": 8.4, # mins
            "economic_growth": 0.0, # percentage delta
            "population_coverage": 85.0, # healthcare percentage coverage
            "construction_cost": 0.0,
            "risk_level": 12.4, # flood/disaster risk index
            "sustainability_score": 64.0,
            "roi": 0.0
        }
        
        baseline_recommendation = {
            "summary": "The baseline city has high traffic congestion in the commercial downtown core. Medical accessibility in the western sectors is sub-optimal.",
            "actions": [
                {"title": "Improve Healthcare Access", "description": "Consider building a hospital or healthcare center in the coordinates (-122.4244, 37.7799) to optimize coverage of the residential block.", "priority": "High"},
                {"title": "De-congest Downtown Corridor", "description": "Adding a new metro station or widening the central lanes will reduce travel time by up to 15%.", "priority": "Medium"}
            ]
        }
        
        result = SimulationResult(
            scenario_id=baseline.id,
            metrics_json=json.dumps(baseline_metrics),
            recommendations_json=json.dumps(baseline_recommendation)
        )
        db.add(result)
        db.commit()
        
        print("Database seed complete successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
