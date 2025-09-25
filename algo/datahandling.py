from neo4j import GraphDatabase
import yaml, json, os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("AURA_URI")
user = os.getenv("AURA_USER")
password = os.getenv("AURA_PASS")

driver = GraphDatabase.driver(uri, auth=(user, password))

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
            "headway_s": 180
        }

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
        LIMIT 10
        """
        trains = session.run(q, codes=station_codes)

        scenario = []
        start_time = 0
        for idx, tr in enumerate(trains):
            scenario.append({
                "tid": tr["tid"],
                "origin": tr["origin"],
                "dest": tr["dest"],
                "route_blocks": [],  # you can fill this by traversing TRACK edges
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
    # Pick 3–4 adjacent stations manually for now
    corridor_stations = ["THVM", "KRMI", "MAO"]
    export_corridor(corridor_stations)
    export_scenarios(corridor_stations)
