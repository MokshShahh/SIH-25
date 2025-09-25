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

def generate_random_route_blocks(all_stations, origin, dest):
    """
    Generates a list of route blocks between origin and dest from a list of all stations.
    """
    try:
        start_idx = all_stations.index(origin)
        end_idx = all_stations.index(dest)
    except ValueError:
        print(f"Warning: Origin {origin} or Destination {dest} not found in corridor stations.")
        return []

    # Get all stations between origin and destination
    intermediate_stations = all_stations[min(start_idx, end_idx) + 1 : max(start_idx, end_idx)]
    
    # Randomly select some intermediate stations to be part of the route
    num_stops = random.randint(0, len(intermediate_stations))
    stops = random.sample(intermediate_stations, num_stops)
    
    # Combine origin, stops, and destination in correct order
    full_route_stations = [origin] + sorted(stops, key=lambda s: all_stations.index(s)) + [dest]

    # Convert the station list to a list of 'from-to' blocks
    route_blocks = []
    if len(full_route_stations) > 1:
        for i in range(len(full_route_stations) - 1):
            route_blocks.append(f"{full_route_stations[i]}-{full_route_stations[i+1]}")
    
    return route_blocks

def export_scenarios(station_codes, out_dir="data/scenarios"):
    with driver.session() as session:
        trains_q = """
        MATCH (t:Train)
        WHERE t.source IN $codes OR t.destination IN $codes
        RETURN t.id AS tid, t.source AS origin, t.destination AS dest,
               t.type AS type, t.priority AS priority
        """
        trains_result = session.run(trains_q, codes=station_codes)
        trains_data = list(trains_result)
        
        scenario = []
        start_time = 0
        for idx, tr in enumerate(trains_data):
            tid = str(tr["tid"])
            
            # Generate random route blocks for the train
            route_blocks = generate_random_route_blocks(station_codes, tr["origin"], tr["dest"])

            scenario.append({
                "tid": tid,
                "origin": tr["origin"],
                "dest": tr["dest"],
                "route_blocks": route_blocks,
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

if __name__ == "__main__":
    corridor_stations = [
    "SWV", "MAO", "DSJ", "AWB", "LKO", "SVDK", "SSA", "RJPB", "PNBE", "URK",
    "CSMT", "LTT", "AJNI", "KRMI", "NGP", "PUNE", "MAJN", "JBP", "BDTS", "ATT",
    "SRC", "REWA", "BPL", "TVC", "PLNI", "POY", "HYB", "JP", "RJT", "MAS",
    "HTE", "KOAA", "PURI", "ASN", "DHN", "KDS", "SZE", "PLJE", "JSME", "ANVT",
    "DLI", "NZM", "BKN", "HW", "HMH", "SGNR", "SDLP", "SOG", "PBC", "MKN",
    "JU", "MTD", "RTGH", "CUR", "SRE", "UMB", "PTK", "JAT", "GKP", "BNY",
    "CPR", "LJN", "BST", "CPA", "FBD", "BC", "LKU", "JMP", "SHC", "JLWC",
    "KOTA", "NLP", "MZS", "GHY", "SCL", "NJP", "KNE", "KIR", "SGUJ", "RNY",
    "RPAN", "MS", "TEN", "ERS", "PDY", "QLN", "KCVL", "CGL", "MDU", "CBE",
    "MKM", "BWT", "YPR", "PVR", "VSKP", "BGM", "HSRA", "WFD", "BYPL", "DHL",
    "KRBA", "BSP", "PGTN", "KIK", "NCR", "UBL", "BJP", "RXL", "SC", "DBG",
    "KCG", "TPTY", "COA", "BZA", "CCT", "KRMR", "NS", "NSL", "TATA", "ADB",
    "BIDR", "NBQ", "KJM", "NED", "NZB", "RU", "KGP", "JGM", "MDN", "BLS",
    "SHM", "BQA", "VSU", "CBSA", "CKP", "SBP", "BAND", "KRDL", "BPQ", "CAF",
    "RNC", "HWH", "DURG", "BCT", "NDLS", "GIMB", "AII", "UDZ", "SNSI", "DR",
    "BBS", "KOP", "BSL", "SUR", "MYS", "G", "MRJ", "ADI", "AMH", "ASR",
    "SA", "FD", "BSB", "KZJ", "BTI", "PTA", "PJP", "KK", "PAY"
   ]
    export_corridor(corridor_stations)
    export_scenarios(corridor_stations)