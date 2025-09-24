import asyncio
import os
from fastapi import FastAPI, WebSocket, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from MILP import optimize_train_schedule_milp
from typing import Dict

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500"
]

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("DB_USERNAME") 
password = os.getenv("DB_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password))

WS_CONNECTIONS: List[WebSocket] = []

SIM_RUNNING = False
TIME_FACTOR = 60 
SIM_STEP_SEC = 0.2 

def time_to_minutes(time_str: str) -> int:
    try:
        if ':' not in time_str:
            return -1
        parts = time_str.split(':')
        if len(parts) >= 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2]) if len(parts) > 2 else 0
            return hours * 60 + minutes + seconds / 60
        return -1
    except (ValueError, IndexError):
        return -1

def run_cypher(query: str, params: dict = None):
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        driver.verify_connectivity()
        print("Successfully connected to Neo4j database.")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
    
    asyncio.create_task(sim_loop())
    
    yield
    
    driver.close()
    print("Neo4j database connection closed.")

app = FastAPI(
    title="Unified Train Management System", 
    description="Combined train simulator and station management API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/updates")
async def ws_updates(ws: WebSocket):
    await ws.accept()
    WS_CONNECTIONS.append(ws)
    try:
        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=10)
            except asyncio.TimeoutError:
                pass  
    except Exception:
        pass
    finally:
        if ws in WS_CONNECTIONS:
            WS_CONNECTIONS.remove(ws)
        try:
            await ws.close()
        except:
            pass

async def broadcast(msg: dict):
    for ws in WS_CONNECTIONS.copy():
        try:
            await ws.send_json(msg)
        except Exception:
            WS_CONNECTIONS.remove(ws)
            try:
                await ws.close()
            except:
                pass

@app.get("/stations")
def get_stations():
    query = """
    MATCH (s:Station)
    RETURN coalesce(s.code, "") AS code, coalesce(s.name, "Unknown") AS name
    ORDER BY code
    """
    return run_cypher(query)

@app.get("/stations/map")
def get_map_data():
    query = """
    MATCH p=(s1:Station)-[:TRACK]->(s2:Station) 
    RETURN p LIMIT 25
    """
    with driver.session() as session:
        result = session.run(query)
        data = []
        for record in result:
            res = record.data()
            data.append([res["p"][0]["name"], res["p"][2]["name"]])
    
    if not data:
        return {"error": "No records found. Please ensure the database is populated."}
    return {"stations": data}

@app.get("/stations/network")
def get_station_network():
    query = """
    MATCH (s1:Station)-[e:TRACK]->(s2:Station)
    RETURN coalesce(s1.code, "") AS from,
           coalesce(s2.code, "") AS to,
           coalesce(e.distance, 0) AS distance
    """
    return run_cypher(query)

@app.get("/stations/{station_identifier}/trains")
def get_trains_for_station(station_identifier: str):
    """Get trains for a station (supports both code and name)"""
    query = """
    MATCH (t:Train)-[r:ROUTE]->(s:Station {code: $station_code})
    RETURN t.id AS train_id,
           coalesce(t.name, "Unnamed Train") AS train_name,
           coalesce(r.arrival, "NA") AS arrival,
           coalesce(r.departure, "NA") AS departure,
           coalesce(r.seq, -1) AS seq
    ORDER BY r.seq
    """
    result = run_cypher(query, {"station_code": station_identifier})
    
    if result:
        return result

    query = """
    MATCH (t:Train)-[r:ROUTE]->(s:Station {name: $station_name})
    RETURN t.id AS train_id,
           coalesce(t.name, "Unnamed Train") AS train_name,
           coalesce(r.arrival, "NA") AS arrival,
           coalesce(r.departure, "NA") AS departure,
           coalesce(r.seq, -1) AS seq
    ORDER BY r.seq
    """
    return run_cypher(query, {"station_name": station_identifier})

@app.get("/stations/{station_name}/arrivals")
def get_train_arrivals(station_name: str):
    query = """
    MATCH (train:Train)-[:ORIGINATES_FROM]->(origin:Station),
           (train)-[arrival:SCHEDULED_ARRIVAL]->(destination:Station)
    WHERE destination.name = $station_name
    RETURN train, origin, arrival
    """
    with driver.session() as session:
        result = session.run(query, station_name=station_name)
        data = []
        for record in result:
            data.append({
                "train_name": record["train"]["name"],
                "train_type": record["train"]["type"],
                "origin": record["origin"]["name"],
                "scheduled_arrival": record["arrival"]["arrival_time"],
                "scheduled_platform": record["arrival"]["scheduled_platform"]
            })
    
    if not data:
        return {"error": f"No arriving trains found for station: {station_name}"}
    return {"arrivals": data}

@app.get("/trains/all")
def get_all_trains():
    """Get all trains with their complete routes"""
    query = """
    MATCH (t:Train)-[r:ROUTE]->(s:Station)
    WHERE t.id IS NOT NULL
      AND t.name IS NOT NULL
      AND r.seq IS NOT NULL
      AND r.arrival IS NOT NULL
      AND r.departure IS NOT NULL
      AND s.code IS NOT NULL
    WITH t, r, s
    ORDER BY r.seq
    WITH t, collect({
        station_code: s.code,
        station_name: coalesce(s.name, "Unknown Station"),
        arrival: r.arrival,
        departure: r.departure,
        seq: r.seq,
        distance: coalesce(r.distance, 0)
    }) AS route
    RETURN t.id AS train_id,
           t.name AS train_name,
           t.source AS source,
           t.destination AS destination,
           route
    """
    try:
        trains = run_cypher(query)
        if not trains:
            raise HTTPException(status_code=404, detail="No trains with complete ROUTE data found")
        return trains
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trains/{train_id}")
def get_train_details(train_id: str):
    query = """
    MATCH (t:Train {id: $train_id})-[r:ROUTE]->(s:Station)
    WITH t, r, s
    ORDER BY r.seq
    WITH t, collect({
        station_code: s.code,
        station_name: coalesce(s.name, "Unknown Station"),
        arrival: r.arrival,
        departure: r.departure,
        seq: r.seq,
        distance: coalesce(r.distance, 0)
    }) AS route
    RETURN t.id AS train_id,
           t.name AS train_name,
           t.source AS source,
           t.destination AS destination,
           route
    """
    result = run_cypher(query, {"train_id": train_id})
    if not result:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return result[0]

@app.post("/simulate/start")
def start_simulation():
    global SIM_RUNNING
    SIM_RUNNING = True
    return {"ok": True, "message": "Simulation started"}

@app.post("/simulate/stop")
def stop_simulation():
    global SIM_RUNNING
    SIM_RUNNING = False
    return {"ok": True, "message": "Simulation stopped"}

@app.get("/simulate/status")
def get_simulation_status():
    return {
        "running": SIM_RUNNING,
        "time_factor": TIME_FACTOR,
        "step_seconds": SIM_STEP_SEC,
        "connected_clients": len(WS_CONNECTIONS)
    }

async def sim_loop():
    sim_time = datetime.now()
    while True:
        try:
            if not SIM_RUNNING:
                await asyncio.sleep(SIM_STEP_SEC)
                continue

            sim_time += timedelta(seconds=SIM_STEP_SEC * TIME_FACTOR)
            current_minutes = sim_time.hour * 60 + sim_time.minute + sim_time.second / 60

            trains_query = """
            MATCH (t:Train)-[r:ROUTE]->(s:Station)
            WHERE r.seq IS NOT NULL
            WITH t, r, s
            ORDER BY t.id, toInteger(r.seq)
            WITH t, collect({
                station_code: s.code,
                station_name: coalesce(s.name, "Unknown Station"),
                arrival: r.arrival,
                departure: r.departure,
                seq: toInteger(r.seq),
                distance: toInteger(coalesce(r.distance, 0))
            }) AS route
            WHERE size(route) > 0
            RETURN t.id AS train_id, coalesce(t.name, "Unnamed Train") AS train_name, route
            """
            train_records = run_cypher(trains_query)
            if not train_records:
                await asyncio.sleep(SIM_STEP_SEC)
                continue

            for train in train_records:
                try:
                    route = train.get("route", [])
                    tid = train.get("train_id")
                    tname = train.get("train_name")

                    status = "scheduled"
                    progress = 0
                    current_station = None
                    next_station = None

                    for i, stop in enumerate(route):
                        arrival_time = stop.get("arrival")
                        departure_time = stop.get("departure")
                        if not arrival_time or not departure_time:
                            continue

                        arr_min = time_to_minutes(arrival_time)
                        dep_min = time_to_minutes(departure_time)
                        if arr_min < 0 or dep_min < 0:
                            continue

                        if current_minutes <= dep_min:
                            current_station = stop.get("station_name", "Unknown Station")
                            next_station = route[i+1].get("station_name") if i+1 < len(route) else None

                            if next_station and i+1 < len(route):
                                next_arrival_time = route[i+1].get("arrival")
                                if next_arrival_time:
                                    next_arrival = time_to_minutes(next_arrival_time)
                                    travel_time = max(1, next_arrival - dep_min)
                                    progress = (current_minutes - dep_min) / travel_time
                                    progress = max(0, min(progress, 1))
                                    status = "enroute"
                            else:
                                status = "at_station"
                                progress = 1
                            break

                    await broadcast({
                        "type": "status_update",
                        "train_id": tid,
                        "train_name": tname,
                        "current_station": current_station,
                        "next_station": next_station,
                        "status": status,
                        "progress": round(progress, 6),
                        "sim_time": sim_time.strftime("%H:%M:%S")
                    })

                except Exception as e_train:
                    print(f"[Train Processing Error] {train.get('train_id')}: {e_train}")

        except Exception as e:
            print(f"[Simulation Loop Error] {e}")

        await asyncio.sleep(SIM_STEP_SEC)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        driver.verify_connectivity()
        return {
            "status": "healthy",
            "database": "connected",
            "simulation": "running" if SIM_RUNNING else "stopped",
            "websocket_connections": len(WS_CONNECTIONS)
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }

def minutes_to_hhmmss(minutes: float) -> str:
    total_seconds = int(round(minutes * 60))
    h = (total_seconds // 3600) % 24
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def fetch_train_route(train_id: str):
    query = """
    MATCH (t:Train {id: $train_id})-[r:ROUTE]->(s:Station)
    RETURN r.seq AS seq, r.arrival AS arrival, r.departure AS departure
    ORDER BY r.seq
    """
    route = run_cypher(query, {"train_id": train_id})
    if not route:
        raise RuntimeError(f"No route found for train {train_id}")
    return route

def check_conflicts(proposed_schedule: dict) -> List[dict]:
    conflicts = []
    segment_times = {} 
    for train_id, train_data in proposed_schedule.items():
        stops = train_data["stops"]
        for i in range(len(stops)-1):
            from_stop = stops[i]
            to_stop = stops[i+1]
            start_min = time_to_minutes(from_stop["new_departure"])
            end_min = time_to_minutes(to_stop["new_arrival"])
            key = (from_stop["station_name"], to_stop["station_name"])
            segment_times.setdefault(key, []).append((train_id, start_min, end_min))
    
    for seg, intervals in segment_times.items():
        intervals.sort(key=lambda x: x[1])
        for i in range(len(intervals)):
            t1, s1, e1 = intervals[i]
            for j in range(i+1, len(intervals)):
                t2, s2, e2 = intervals[j]
                if s2 < e1:
                    conflicts.append({"train1": t1, "train2": t2, "segment": seg})
    return conflicts

def apply_train_departure_to_db(train_id: str, new_dep_minutes: float):
    route = fetch_train_route(train_id)
    orig_dep = next((time_to_minutes(stop["departure"]) for stop in route if stop.get("departure")), None)
    if orig_dep is None:
        raise RuntimeError(f"Origin departure not found for train {train_id}")
    delta = new_dep_minutes - orig_dep

    updates = []
    for stop in route:
        seq = stop["seq"]
        arr_min = time_to_minutes(stop["arrival"]) if stop.get("arrival") else None
        dep_min = time_to_minutes(stop["departure"]) if stop.get("departure") else None

        new_arr = minutes_to_hhmmss(arr_min + delta) if arr_min is not None else None
        new_dep = minutes_to_hhmmss(dep_min + delta) if dep_min is not None else None

        update_q = """
        MATCH (t:Train {id: $train_id})-[r:ROUTE {seq: $seq}]->(s:Station)
        SET r.arrival = $new_arr, r.departure = $new_dep
        """
        run_cypher(update_q, {"train_id": train_id, "seq": seq, "new_arr": new_arr, "new_dep": new_dep})
        updates.append({"seq": seq, "new_arrival": new_arr, "new_departure": new_dep})
    return updates

@app.post("/optimize/apply")
async def apply_optimized_schedule(schedule: dict):
    milp_input = {}

    for train_id in schedule:
        try:
            route = fetch_train_route(train_id)
            if not route:
                continue
            eta = time_to_minutes(route[0]["departure"])
            priority = 10  # can customize per train if needed
            milp_input[train_id] = {"eta": eta, "priority": priority}
        except Exception as e:
            print(f"[MILP Input Error] {train_id}: {e}")
            continue

    optimized_times, precedence_decisions = optimize_train_schedule_milp(milp_input)
    if not optimized_times:
        return {"status": "error", "message": "No optimal solution found"}

    applied_trains = []
    for train_id, opt in optimized_times.items():
        try:
            route = fetch_train_route(train_id)
            delta = opt['new_arrival_time'] - milp_input[train_id]['eta']
            updates = []
            for stop in route:
                seq = stop["seq"]
                arr_min = time_to_minutes(stop.get("arrival")) if stop.get("arrival") else None
                dep_min = time_to_minutes(stop.get("departure")) if stop.get("departure") else None

                new_arr = minutes_to_hhmmss(arr_min + delta) if arr_min is not None else None
                new_dep = minutes_to_hhmmss(dep_min + delta) if dep_min is not None else None

                update_q = """
                MATCH (t:Train {id: $train_id})-[r:ROUTE {seq: $seq}]->(s:Station)
                SET r.arrival = $new_arr, r.departure = $new_dep
                """
                run_cypher(update_q, {"train_id": train_id, "seq": seq, "new_arr": new_arr, "new_dep": new_dep})
                updates.append({"seq": seq, "new_arrival": new_arr, "new_departure": new_dep})

            applied_trains.append({"train_id": train_id, "updates": updates})
        except Exception as e:
            return {"status": "error", "message": f"Failed to apply train {train_id}: {e}"}

    for train in applied_trains:
        await broadcast({
            "type": "schedule_update",
            "train_id": train["train_id"],
            "stops": train["updates"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    print(f"[MILP Schedule Applied] {datetime.now().isoformat()} - Trains updated: {[t['train_id'] for t in applied_trains]}")

    return {
        "status": "ok",
        "applied_trains": applied_trains,
        "precedence_decisions": precedence_decisions
    }


@app.post("/optimize/station")
async def optimize_at_station():
    station_code = "DR"
    current_minutes = 120
    if not station_code or current_minutes is None:
        raise HTTPException(
            status_code=400,
            detail="`station_code` and `current_minutes` are required"
        )
    
    query = """
    MATCH (t:Train)-[r:ROUTE]->(s:Station)
    WHERE s.code="DR"
    WITH t, r, s
    ORDER BY t.id, toInteger(r.seq)
    RETURN t.id AS train_id,
        t.name AS train_name,
        t.priority AS priority,
        collect(s.name) AS stations_in_path,
        collect(r.arrival) AS arrival_times,
        collect(r.departure) AS departure_times
    """
    
    incoming_trains = run_cypher(query, {"station_code": station_code, "current_minutes": current_minutes})

    if not incoming_trains:
        return {
            "status": "info",
            "message": f"No incoming trains found for station {station_code} at the current time."
        }

    milp_input = {}
    for train_record in incoming_trains:
        train_id = train_record.get("train_id")
        eta_str = train_record.get("estimated_arrival")
        priority = train_record.get("priority")
        
        eta = time_to_minutes(eta_str)
        
        if train_id and eta is not None and priority is not None:
            milp_input[train_id] = {
                "eta": eta,
                "priority": priority
            }

    if not milp_input:
        return {
            "status": "error",
            "message": "Failed to process train data for optimization."
        }
        
    optimized_times, precedence_decisions = optimize_train_schedule_milp(milp_input)
    
    if not optimized_times:
        return {
            "status": "error",
            "message": "MILP solver could not find an optimal solution."
        }
        
    return {
        "status": "ok",
        "optimized_schedule": optimized_times,
        "precedence_decisions": precedence_decisions
    }

@app.post("/optimize/propose")
def propose_optimized_schedule(schedule: dict):
    milp_input = {}

    for train_id in schedule:
        try:
            route = fetch_train_route(train_id)
            if not route: 
                continue
            eta = time_to_minutes(route[0]["departure"])
            priority = 10 
            milp_input[train_id] = {"eta": eta, "priority": priority}
        except Exception as e:
            print(f"[MILP Input Error] {train_id}: {e}")
            continue

    optimized_times, precedence_decisions = optimize_train_schedule_milp(milp_input)
    if not optimized_times:
        return {"status": "error", "message": "No optimal solution found"}

    proposed = {}
    for train_id, opt in optimized_times.items():
        try:
            route = fetch_train_route(train_id)
            delta = opt['new_arrival_time'] - milp_input[train_id]['eta']
            stops = []
            for stop in route:
                arr_min = time_to_minutes(stop.get("arrival")) if stop.get("arrival") else None
                dep_min = time_to_minutes(stop.get("departure")) if stop.get("departure") else None
                stops.append({
                    "seq": stop["seq"],
                    "station_name": stop.get("station_name") or stop.get("code") or "Unknown",
                    "orig_arrival": stop.get("arrival"),
                    "new_arrival": minutes_to_hhmmss(arr_min + delta) if arr_min is not None else None,
                    "orig_departure": stop.get("departure"),
                    "new_departure": minutes_to_hhmmss(dep_min + delta) if dep_min is not None else None
                })
            proposed[train_id] = {"departure_minutes": schedule[train_id]["departure_minutes"], "stops": stops}
        except Exception as e:
            print(f"[Proposed Schedule Error] Train {train_id}: {e}")
            continue

    conflicts = check_conflicts(proposed)

    return {
        "status": "proposed",
        "schedule": proposed,
        "conflicts": conflicts,
        "precedence_decisions": precedence_decisions
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    