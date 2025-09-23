# app/main.py
import asyncio
from fastapi import FastAPI, WebSocket, HTTPException
from typing import List
from datetime import datetime, timedelta

from neo4j_driver import run_cypher
from utils import time_to_minutes

app = FastAPI(title="Nationwide Train Simulator (Neo4j)")

WS_CONNECTIONS: List[WebSocket] = []

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

@app.get("/trains/{station_code}")
def get_trains_for_station(station_code: str):
    query = """
    MATCH (t:Train)-[r:ROUTE]->(s:Station {code: $station_code})
    RETURN t.id AS train_id,
           coalesce(t.name, "Unnamed Train") AS train_name,
           coalesce(r.arrival, "NA") AS arrival,
           coalesce(r.departure, "NA") AS departure,
           coalesce(r.seq, -1) AS seq
    ORDER BY r.seq
    """
    return run_cypher(query, {"station_code": station_code})

@app.get("/station-map")
def get_station_map():
    query = """
    MATCH (s1:Station)-[e:TRACK]->(s2:Station)
    RETURN coalesce(s1.code, "") AS from,
           coalesce(s2.code, "") AS to,
           coalesce(e.distance, 0) AS distance
    """
    return run_cypher(query)

SIM_RUNNING = False

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


TIME_FACTOR = 60 
SIM_STEP_SEC = 0.2 

@app.on_event("startup")
async def start_sim_loop():
    asyncio.create_task(sim_loop())

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
                        "progress": round(progress, 6)
                    })

                except Exception as e_train:
                    print(f"[Train Processing Error] {train.get('train_id')}: {e_train}")

        except Exception as e:
            print(f"[Simulation Loop Error] {e}")

        await asyncio.sleep(SIM_STEP_SEC)

@app.get("/trains/all")
def get_all_trains():
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
