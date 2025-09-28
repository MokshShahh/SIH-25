from neo4j import GraphDatabase
import yaml, json, os
import random
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
uri = os.getenv("AURA_URI")
user = os.getenv("AURA_USER")
password = os.getenv("AURA_PASS")

driver = GraphDatabase.driver(uri, auth=(user, password))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

file_path = os.path.join(BASE_DIR, "mumbai-lines.xlsx")

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
HARBOUR_LINE_CODES = [
    # CSMT to Panvel stretch
    "CSMT", "MSD", "SNRD", "DKRD", "RRD", "CTGN", "SVE", "VDLR",
    "GTBN", "CHF", "CLA", "TKNG", "CMBR", "GV", "MNKD", "VSH", 
    "SNCR", "JNJ", "NEU", "SWDV", "BEPR", "KHAG", "MANR", "KNDS", "PNVL",
    # Wadala Road to Andheri/Goregaon stretch
    "MM", "BA", "KHR", "STC", "VLP", "ADH", "JOS", "RMAR", "GMN"
]

MUMBAI_STATION_PLATFORM_MAP = {
    # MAJOR HUBS 
    "CSMT": 18,  
    "KYN": 8,    
    "TNA": 10,   
    "DR": 8,    
    "PNVL": 7,   
    "LTT": 5,    
    "MMCT": 9,   
    "CCG": 4,    
    "ADH": 9,    
    "BVI": 9,    
    "CLA": 8,    
    "BSR": 7,    
    "DDR": 6,    
    
    #  Western Line Stations 
    "MEL": 4,    # Marine Lines
    "CYR": 4,    # Charni Road
    "GTR": 4,    # Grant Road
    "MX": 4,     # Mahalaxmi
    "PL": 4,     # Lower Parel
    "PBHD": 4,   # Prabhadevi (Formerly EPR)
    "MRU": 4,    # Matunga Road
    "MM": 4,     # Mahim Junction
    "BA": 4,     # Bandra
    "KHR": 4,    # Khar Road
    "STC": 4,    # Santacruz
    "VLP": 4,    # Vile Parle
    "JOS": 4,    # Jogeshwari
    "RMAR": 4,   # Ram Mandir
    "GMN": 4,    # Goregaon
    "MDD": 4,    # Malad
    "KILE": 4,   # Kandivali
    "DIC": 4,    # Dahisar
    "MIRA": 4,   # Mira Road
    "BYR": 6,    # Bhayandar
    "NIG": 4,    # Naigaon
    "NSP": 4,    # Nallasopara
    "VR": 4,     # Virar
    "VTN": 2,    # Vaitarna
    "SAH": 2,    # Saphale
    "KLV": 2,    # Kelve Road
    "PLG": 2,    # Palghar
    "UMR": 2,    # Umroli
    "BOR": 2,    # Boisar
    "VGN": 2,    # Vangaon
    "DRD": 2,    # Dahanu Road
    
    # Central Line 
    "MSD": 4,    # Masjid
    "SNRD": 4,   # Sandhurst Road
    "BY": 4,     # Byculla
    "CHG": 4,    # Chinchpokli
    "CRD": 4,    # Currey Road
    "PR": 4,     # Parel
    "MTN": 4,    # Matunga
    "SIN": 4,    # Sion
    "VVH": 4,    # Vidyavihar
    "GC": 4,     # Ghatkopar
    "VK": 4,     # Vikhroli
    "KJMG": 4,   # Kanjurmarg
    "BND": 4,    # Bhandup
    "NHU": 4,    # Nahur
    "MLND": 4,   # Mulund
    "KLVA": 4,   # Kalwa
    "MBQ": 4,    # Mumbra
    "DIVA": 4,   # Diva Junction
    "KOPR": 4,   # Kopar
    "DI": 4,     # Dombivli
    "THK": 4,    # Thakurli
    
    # Central Line (Kasara Branch) 
    "SHAD": 2,   # Shahad
    "ABY": 2,    # Ambivli
    "TLA": 2,    # Titwala
    "KDV": 2,    # Khadavli
    "VSD": 2,    # Vasind
    "ASO": 2,    # Asangaon
    "ATG": 2,    # Atgaon
    "KDI": 2,    # Khardi
    "KSRA": 3,   # Kasara (Terminal)
    
    #  Central Line 
    "VLDI": 2,   # Vithalwadi
    "ULNR": 2,   # Ulhasnagar
    "ABH": 2,    # Ambarnath
    "BUD": 2,    # Badlapur
    "VGI": 2,    # Vangani
    "SHLU": 2,   # Shelu
    "NRL": 2,    # Neral Junction
    "BVS": 2,    # Bhivpuri Road
    "KJT": 3,    # Karjat (Terminal/Branch)
    "PDI": 2,    # Palasdari
    "KLY": 2,    # Kelavli
    "DLV": 2,    # Dolavli
    "LWJ": 2,    # Lowjee
    "KPQ": 2,    # Khopoli (Terminal)
    
    # Harbour 
    "DKRD": 2,   # Dockyard Road
    "RRD": 2,    # Reay Road
}


STATION_TO_LINE_MAP = {
   
    **{code: "HARBOUR" for code in HARBOUR_LINE_CODES},
  
}

def load_stations_from_excel(file_path, sheet_name="HARBOUR"):
    """
    Load station codes from a given Excel sheet.
    Assumes station codes are in the first column.
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name)
   
    stations = df.iloc[:, 0].dropna().astype(str).tolist()
    return stations

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



def get_linear_route(origin, dest, all_line_data):
    """
    Finds the most appropriate strictly linear list for a given origin/destination pair.
    
    Args:
        origin (str): Origin station code.
        dest (str): Destination station code.
        all_line_data (dict): Dictionary containing the linear station lists.
        
    Returns:
        list: The sequential list of stations for the line, or [] if no clear line is found.
    """
    
    # Helper to check if both stations are on a given line and return that line's list
    def check_and_return(line_key):
        line_stations = all_line_data.get(line_key, [])
        if origin in line_stations and dest in line_stations:
            return line_stations
        return []

    # Prioritize the lines you've defined
    if route := check_and_return("CENTRAL"):
        return route
    if route := check_and_return("WESTERN"):
        return route
    if route := check_and_return("HARBOUR"):
        return route
        
    
    return []

def generate_simulated_scenarios(all_line_data, out_dir="data/scenarios", num_trains=20):
    """
    Generates a set of simulated train scenarios based on the linear Excel station lists.
    This replaces the Neo4j query.
    """

    linear_lists = [
        all_line_data.get("CENTRAL", []),
        all_line_data.get("WESTERN", []),
        all_line_data.get("HARBOUR", [])
    ]
    # Filter out any empty lists
    linear_lists = [lst for lst in linear_lists if lst]

    if not linear_lists:
        print("ERROR: No valid linear station lists loaded from Excel to simulate routes.")
        return

    scenario = []
    start_time = 0
    
    for idx in range(num_trains):
       
        line_stations = random.choice(linear_lists)
        
        origin = random.choice(line_stations)
        
        dest = random.choice([s for s in line_stations if s != origin])
   
        route_blocks = generate_random_route_blocks(line_stations, origin, dest)
        
        # Fallback to ensure we always have some block if O/D are adjacent
        if not route_blocks and origin != dest:
            route_blocks = [f"{origin}-{dest}"]

        # 5. Create the simulated train record
        scenario.append({
            "tid": f"SIM_{idx+1}",
            "origin": origin,
            "dest": dest,
            "route_blocks": route_blocks,
            "sched_departure_s": start_time + idx * 300, # Departure every 5 minutes
            "sched_arrival_s": start_time + (idx + 1) * 1200,
            "priority": random.randint(3, 9), # Random priority
            "type": "Passenger (MEMU)",
            "dwell_rules": {}
        })

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "scenario1.json")
    with open(out_path, "w") as f:
        json.dump(scenario, f, indent=2)

    print(f"Scenario saved to {out_path} with {len(scenario)} simulated trains.")

if __name__ == "__main__":
    
   
    
    print("Loading station codes from Excel...")
    
    # Dictionary to hold the three sequential lists
    all_line_data = {}
    
    try:
        
        western_stations = load_stations_from_excel(file_path, sheet_name="WESTERN")
        harbour_stations = load_stations_from_excel(file_path, sheet_name="HARBOUR")
        central_stations = load_stations_from_excel(file_path, sheet_name="CENTRAL")
        
        all_line_data["WESTERN"] = western_stations
        all_line_data["HARBOUR"] = harbour_stations
        all_line_data["CENTRAL"] = central_stations

        
        combined_stations = western_stations + harbour_stations + central_stations
        all_stations_set = set(combined_stations)
        corridor_stations = list(all_stations_set)
        
        print(f"Loaded {len(harbour_stations)} Harbour stations.")
        print(f"Loaded {len(central_stations)} Central stations.")
        print(f"Loaded {len(western_stations)} Western stations.")
        print(f"Total Unique Stations in Corridor: {len(corridor_stations)}")

    except Exception as e:
        print(f"ERROR: Could not load all Excel sheets: {e}. Cannot generate routes.")
        corridor_stations = []
        all_line_data = {}
        
    
    if corridor_stations:
        export_corridor(corridor_stations)
    
 
    generate_simulated_scenarios(all_line_data) 