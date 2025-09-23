from fastapi import FastAPI
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

app = FastAPI()

uri = os.getenv("NEO4J_URI")
user = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        driver.verify_connectivity()
        print("Successfully connected to database.")
    except Exception as e:
        print(f"Failed to connect to db: {e}")
    yield
    driver.close()
    print("Neo4j database connection closed.")

def get_stations_and_connections():
    query = """
    MATCH p=(s1:Station)-[:CONNECTS_TO]->(s2:Station) RETURN p LIMIT 25;
    """
    with driver.session() as session:
        result = session.run(query)
        data = []
        for record in result:
            res=record.data()
            data.append([res["p"][0]["name"],res["p"][2]["name"]])
        
        return data
    
def get_arriving_trains(station_name: str):
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
        return data


@app.get("/stations/map")
def get_map_data():
    data = get_stations_and_connections()
    if not data:
        return {"error": "No records found. Please ensure the database is populated."}
    return {"stations": data}

@app.get("/stations/{station_name}/arrivals")
def get_train_arrivals(station_name: str):
    data = get_arriving_trains(station_name)
    if not data:
        return {"error": f"No arriving trains found for station: {station_name}"}
    return {"arrivals": data}