from neo4j import GraphDatabase
import os

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://b7b8c686.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "tFPg8hJxJqZ4qJLQhWQ1ncI2YdTxJJwuQoi2zsKcg9c")
NEO4J_DB   = os.getenv("NEO4J_DB", "neo4j")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def verify_connection():
    """Verify connectivity to the database."""
    try:
        driver.verify_connectivity()
        print(f"Connected to Neo4j at {NEO4J_URI} (DB: {NEO4J_DB})")
    except Exception as e:
        print("Neo4j connection failed:", e)
        raise e

def run_cypher(query: str, params: dict = None):
    """Run a Cypher query and return a list of dicts."""
    with driver.session(database=NEO4J_DB) as session:
        try:
            result = session.run(query, params or {})
            return [record.data() for record in result]
        except Exception as e:
            print(f"Error running query: {query}\n{e}")
            return []

def close_driver():
    """Close the Neo4j driver."""
    driver.close()
