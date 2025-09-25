
#USING COMBINED APPROACH INSTEAD
from neo4j import GraphDatabase
import yaml, json, os
import random
from dotenv import load_dotenv

# Your existing functions
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
PLATFORM_MAP = {
    "CSMT": 18,
    "LTT": 7,
    "KYN": 8,
    "DR": 8,
    "TNA": 10,
    "PNVL": 7
}

def generate_features(stations, trains):
    """
    Generates estimated features for stations and trains.
    """
    station_features = {}
    for station in stations:
        station_code = station.get("code")
        num_platforms = PLATFORM_MAP.get(station_code, 2)
        station_features[station_code] = {
            "platforms": num_platforms,
            "capacity": num_platforms * 10,  
            "location": 0  
        }

    train_features = []
    for train in trains:
        train_type = train.get("type", "Other")
        priority = PRIORITY_MAP.get(train_type, 1)

        train_features.append({
            "priority": priority,
            "route": [train.get("origin"), train.get("dest")],
            "schedule": {
                "departure_s": train.get("sched_departure_s"),
                "arrival_s": train.get("sched_arrival_s")
            }
        })
    return station_features, train_features

def add_roadblocks(corridor, num_roadblocks=1, max_duration=3600, min_speed=10, max_speed=40):
    """
    Randomly adds roadblocks (speed limit reductions) to the corridor data.
    """
    blocks = corridor.get("blocks", [])
    roadblocks = []
    
    if len(blocks) < num_roadblocks:
        print("Warning: Not enough blocks to create the requested number of roadblocks.")
        return roadblocks

    roadblock_blocks = random.sample(blocks, num_roadblocks)
    
    for block in roadblock_blocks:
        new_speed_limit = random.randint(min_speed, max_speed)
        duration_s = random.randint(600, max_duration)
        start_time_s = random.randint(0, 1800)
        
        roadblock = {
            "block_name": block["name"],
            "new_speed_limit": new_speed_limit,
            "duration_s": duration_s,
            "start_time_s": start_time_s
        }
        roadblocks.append(roadblock)
        
        print(f"Roadblock added to {block['name']}: Speed reduced to {new_speed_limit} km/h for {duration_s} seconds starting at {start_time_s}s.")
    
    return roadblocks

def export_corridor(station_codes, corridor_yaml="configs/corridor.yaml"):
    with driver.session() as session:
        q = """
        MATCH (s1:Station)-[t:TRACK]->(s2:Station)
        WHERE s1.code IN $codes AND s2.code IN $codes
        RETURN s1.code AS from_code, s1.name AS from_name,
               s2.code AS to_code, s2.name AS to_name,
               t.distance AS dist
        """
        result = session.run(q, codes=station_codes)

        stations = {}
        blocks = []
        for r in result:
            stations[r["from_code"]] = {"code": r["from_code"], "name": r["from_name"], "platforms": 2}
            stations[r["to_code"]] = {"code": r["to_code"], "name": r["to_name"], "platforms": 2}
            blocks.append({
                "name": f"{r['from_code']}-{r['to_code']}",
                "from": r["from_code"],
                "to": r["to_code"],
                "length_km": r["dist"],
                "single_track": True,
                "speed_limit": 80
            })

        corridor = {
            "stations": list(stations.values()),
            "blocks": blocks,
            "headway_s": 180,
        }
        
        corridor["roadblocks"] = add_roadblocks(corridor, num_roadblocks=2)

        os.makedirs(os.path.dirname(corridor_yaml), exist_ok=True)
        with open(corridor_yaml, "w") as f:
            yaml.dump(corridor, f)

        print(f"Corridor saved to {corridor_yaml}")

def export_scenarios(station_codes, out_dir="data/scenarios"):
    with driver.session() as session:
        q = """
        MATCH (t:Train)
        WHERE t.source IN $codes OR t.destination IN $codes
        RETURN t.id AS tid, t.source AS origin, t.destination AS dest,
               t.type AS type, t.priority AS priority
        """
        trains = session.run(q, codes=station_codes)

        scenario = []
        start_time = 0
        for idx, tr in enumerate(trains):
            scenario.append({
                "tid": tr["tid"],
                "origin": tr["origin"],
                "dest": tr["dest"],
                "route_blocks": [],
                "sched_departure_s": start_time + idx*300,
                "sched_arrival_s": start_time + (idx+1)*1200,
                "priority": tr["priority"] or 3,
                "type": tr["type"] or "Other",
                "dwell_rules": {}
            })

        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "scenario1.json")
        with open(out_path, "w") as f:
            json.dump(scenario, f, indent=2)

        print(f"Scenario saved to {out_path}")

# New function to merge roadblock data into scenarios.json
def add_roadblocks_to_scenarios(corridor_yaml="configs/corridor.yaml", scenarios_json="data/scenarios/scenario1.json"):
    # Load roadblock data from corridor.yaml
    with open(corridor_yaml, "r") as f:
        corridor_data = yaml.safe_load(f)
        roadblocks = corridor_data.get("roadblocks", [])

    # Load existing train data from scenarios.json
    with open(scenarios_json, "r") as f:
        scenario_data = json.load(f)
    
    # Create the new dictionary to be saved
    combined_data = {
        "train_schedules": scenario_data,
        "roadblocks": roadblocks
    }
    
    # Overwrite the scenarios.json file with the combined data
    with open(scenarios_json, "w") as f:
        json.dump(combined_data, f, indent=2)

    print(f"Roadblock data successfully merged and saved to {scenarios_json}")


if __name__ == "__main__":
    
    corridor_stations = ["CSMT", "DR", "TNA","KYN","PNVL","LTT","TNA","THK", "DI", "KOPR","MBQ","ADH","CLA"]
    export_corridor(corridor_stations)
    export_scenarios(corridor_stations)
    add_roadblocks_to_scenarios()
    
    sample_trains = [
    {"tid": "1011", "origin": "CSMT", "dest": "NGP", "type": "Superfast", "sched_departure_s": 0, "sched_arrival_s": 1200},
    {"tid": "1037", "origin": "LTT", "dest": "SWV", "type": "Special", "sched_departure_s": 300, "sched_arrival_s": 2400},
    {"tid": "11007", "origin": "CSMT", "dest": "PUNE", "type": "Express", "sched_departure_s": 4500, "sched_arrival_s": 19200},
    {"tid": "12933", "origin": "BDTS", "dest": "ADI", "type": "Superfast", "sched_departure_s": 6000, "sched_arrival_s": 25200},
    {"tid": "99907", "origin": "PUNE", "dest": "TGN", "type": "Passenger (MEMU)", "sched_departure_s": 8000, "sched_arrival_s": 10000}
    ] 
    sample_stations = [{"code": "CSMT"}, {"code": "LTT"},
                        {"code": "DR"},
        {"code": "TNA"},
        {"code": "KYN"},
        {"code": "PNVL"},
        {"code": "ADH"},
        {"code": "PUNE"},
        {"code": "BDTS"}]

    station_features, train_features = generate_features(sample_stations, sample_trains)
    print("\nGenerated Station Features:", json.dumps(station_features, indent=2))
    print("\nGenerated Train Features:", json.dumps(train_features, indent=2))