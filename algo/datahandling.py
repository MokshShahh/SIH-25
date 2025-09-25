from neo4j import GraphDatabase
import yaml, json, os
import random
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("AURA_URI")
user = os.getenv("AURA_USER")
password = os.getenv("AURA_PASS")

driver = GraphDatabase.driver(uri, auth=(user, password))

PRIORITY_MAP = {
    "Superfast": 9,
    "AC Express": 9,
    "Express": 8,
    "Weekly Express": 8,
    "Special": 7,
    "Tourist": 6,
    "Fully Tariffed Rake": 5,
    "Passenger (MEMU)": 4,
    "Luxury Tourist": 10,
    "Other": 1
}

MUMBAI_PLATFORM_MAP = {
    "CSMT": 18, "LTT": 7, "KYN": 8, "DR": 8, "TNA": 10, "PNVL": 7,
    "BYR": 4, "KR": 6, "GTB": 4, "MLV": 3, "BVI": 4, "VR": 5, "ADH": 3, "JOS": 2, "BND": 4
}

def export_mumbai_corridor(corridor_yaml="configs/mumbai_corridor.yaml"):
    mumbai_stations = ["CSMT", "BYR", "DR", "KR", "GTB", "TNA", "KYN", "LTT", "BND", "ADH", "JOS", "MLV", "BVI", "VR", "PNVL"]
    
    with driver.session() as session:
        # Simplified query - only use properties that exist
        q = """
        MATCH (s1:Station)-[t:TRACK]->(s2:Station)
        WHERE s1.code IN $codes AND s2.code IN $codes
        RETURN s1.code AS from_code, s1.name AS from_name,
               s2.code AS to_code, s2.name AS to_name,
               coalesce(t.distance, 8.0) AS dist
        ORDER BY s1.code, s2.code
        """
        result = session.run(q, codes=mumbai_stations)
        records = list(result)

        if not records:
            print("No tracks found. Creating fallback network...")
            return create_fallback_corridor(corridor_yaml)

        stations = {}
        blocks = []
        
        for r in records:
            from_code = r["from_code"]
            to_code = r["to_code"]
            
            stations[from_code] = {"code": from_code, "name": r["from_name"], "platforms": MUMBAI_PLATFORM_MAP.get(from_code, 3)}
            stations[to_code] = {"code": to_code, "name": r["to_name"], "platforms": MUMBAI_PLATFORM_MAP.get(to_code, 3)}
            
            blocks.append({
                "name": f"{from_code}-{to_code}",
                "from": from_code,
                "to": to_code,
                "length_km": r["dist"],
                "single_track": False,
                "speed_limit": 100
            })

        corridor = {
            "stations": list(stations.values()),
            "blocks": blocks,
            "headway_s": 120
        }

        os.makedirs(os.path.dirname(corridor_yaml), exist_ok=True)
        with open(corridor_yaml, "w") as f:
            yaml.dump(corridor, f, default_flow_style=False)

        print(f"Mumbai corridor with {len(stations)} stations saved to {corridor_yaml}")
        return corridor

def create_fallback_corridor(corridor_yaml):
    """Create a basic Mumbai corridor when Neo4j data is limited"""
    stations = [
        {"code": "CSMT", "name": "Mumbai CSM Terminus", "platforms": 18},
        {"code": "DR", "name": "Dadar", "platforms": 8},
        {"code": "KR", "name": "Kurla", "platforms": 6},
        {"code": "TNA", "name": "Thane", "platforms": 10},
        {"code": "KYN", "name": "Kalyan", "platforms": 8}
    ]
    
    blocks = [
        {"name": "CSMT-DR", "from": "CSMT", "to": "DR", "length_km": 12, "single_track": False, "speed_limit": 100},
        {"name": "DR-KR", "from": "DR", "to": "KR", "length_km": 8, "single_track": False, "speed_limit": 100},
        {"name": "KR-TNA", "from": "KR", "to": "TNA", "length_km": 15, "single_track": False, "speed_limit": 100},
        {"name": "TNA-KYN", "from": "TNA", "to": "KYN", "length_km": 12, "single_track": False, "speed_limit": 100}
    ]
    
    corridor = {"stations": stations, "blocks": blocks, "headway_s": 120}
    
    os.makedirs(os.path.dirname(corridor_yaml), exist_ok=True)
    with open(corridor_yaml, "w") as f:
        yaml.dump(corridor, f, default_flow_style=False)
    
    print(f"Fallback corridor created with {len(stations)} stations")
    return corridor

def export_mumbai_scenarios(out_dir="data/scenarios"):
    mumbai_stations = ["CSMT", "DR", "KR", "TNA", "KYN"]
    
    # Create synthetic Mumbai suburban trains since Neo4j query returned 0
    synthetic_trains = [
        {"origin": "CSMT", "dest": "KYN", "type": "Other"},
        {"origin": "KYN", "dest": "CSMT", "type": "Other"},
        {"origin": "CSMT", "dest": "TNA", "type": "Express"},
        {"origin": "TNA", "dest": "CSMT", "type": "Express"},
        {"origin": "DR", "dest": "KYN", "type": "Other"},
        {"origin": "KYN", "dest": "DR", "type": "Other"},
        {"origin": "CSMT", "dest": "DR", "type": "Other"},
        {"origin": "DR", "dest": "CSMT", "type": "Other"},
    ]
    
    scenario = []
    base_time = 6 * 3600  # 6 AM
    
    for idx, train_data in enumerate(synthetic_trains):
        origin = train_data["origin"]
        dest = train_data["dest"]
        train_type = train_data["type"]
        
        # Generate route blocks
        route_blocks = generate_simple_route(mumbai_stations, origin, dest)
        if not route_blocks:
            continue
            
        departure_time = base_time + idx * 300  # 5-minute intervals
        travel_duration = len(route_blocks) * 600  # 10 minutes per block
        
        scenario.append({
            "tid": f"T{1000 + idx}",
            "origin": origin,
            "dest": dest,
            "route_blocks": route_blocks,
            "sched_departure_s": departure_time,
            "sched_arrival_s": departure_time + travel_duration,
            "priority": PRIORITY_MAP.get(train_type, 1),
            "type": train_type,
            "dwell_rules": {}
        })

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "mumbai_scenario.json")
    with open(out_path, "w") as f:
        json.dump(scenario, f, indent=2)

    print(f"Mumbai scenario with {len(scenario)} trains saved to {out_path}")
    return scenario

def generate_simple_route(all_stations, origin, dest):
    """Generate simple route between two stations"""
    try:
        start_idx = all_stations.index(origin)
        end_idx = all_stations.index(dest)
    except ValueError:
        return []
    
    if start_idx == end_idx:
        return []
    
    if start_idx < end_idx:
        stations = all_stations[start_idx:end_idx + 1]
    else:
        stations = all_stations[end_idx:start_idx + 1]
        stations.reverse()
    
    route_blocks = []
    for i in range(len(stations) - 1):
        route_blocks.append(f"{stations[i]}-{stations[i+1]}")
    
    return route_blocks

if __name__ == "__main__":
    print("Exporting Mumbai suburban railway corridor...")
    corridor = export_mumbai_corridor()
    
    print("Generating Mumbai train scenarios...")
    scenarios = export_mumbai_scenarios()
    
    print(f"Mumbai prototype ready with {len(corridor['stations'])} stations and {len(scenarios)} trains")