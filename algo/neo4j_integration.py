# Add to your project (create neo4j_integration.py)
from neo4j import GraphDatabase
import numpy as np
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import os

load_dotenv()
uri = os.getenv("AURA_URI")
user = os.getenv("AURA_USER")
password = os.getenv("AURA_PASS")
driver = GraphDatabase.driver(uri, auth=(user, password))

class Neo4jGNNExtractor:
    def __init__(self, uri=uri, user=user, password=password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def extract_mumbai_central_corridor(self, station_codes: List[str]):
        """
        Extract Mumbai Central line corridor from Neo4j
        Args: station_codes like ['CSMT', 'DR', 'KR', 'TNA'] for Central line
        """
        with self.driver.session() as session:
            # Extract stations
            stations_query = """
            MATCH (s:Station) 
            WHERE s.code IN $codes
            RETURN s.code as code, s.name as name, 
                   coalesce(s.platforms, 3) as platforms,
                   s.zone as zone, s.division as division
            ORDER BY s.code
            """
            stations = list(session.run(stations_query, codes=station_codes))
            
            # Extract track connections
            tracks_query = """
            MATCH (s1:Station)-[r:TRACK|CONNECTED_TO]->(s2:Station)
            WHERE s1.code IN $codes AND s2.code IN $codes
            RETURN s1.code as from_station, s2.code as to_station,
                   coalesce(r.distance, 10.0) as distance_km,
                   coalesce(r.speed_limit, 100) as speed_kmph,
                   coalesce(r.track_type, 'single') as track_type
            """
            tracks = list(session.run(tracks_query, codes=station_codes))
            
            # Extract block sections (if available)
            blocks_query = """
            MATCH (b:Block)-[:CONNECTS]-(s:Station)
            WHERE s.code IN $codes
            RETURN b.name as block_name, b.length as length,
                   collect(s.code) as connected_stations
            """
            try:
                blocks = list(session.run(blocks_query, codes=station_codes))
            except:
                blocks = []  # Fallback if Block nodes don't exist
            
            return self._convert_to_gnn_format(stations, tracks, blocks)
    
    def _convert_to_gnn_format(self, stations, tracks, blocks):
        """Convert Neo4j results to GNN input format"""
        
        # Build comprehensive node list
        all_nodes = []
        node_to_idx = {}
        
        # Add station nodes
        for station in stations:
            node_id = station['code']
            all_nodes.append({
                'type': 'station',
                'id': node_id,
                'name': station['name'],
                'platforms': station['platforms'],
                'raw_data': station
            })
            node_to_idx[node_id] = len(all_nodes) - 1
        
        # Add track segment nodes
        for track in tracks:
            track_id = f"{track['from_station']}-{track['to_station']}"
            all_nodes.append({
                'type': 'track',
                'id': track_id,
                'from_station': track['from_station'],
                'to_station': track['to_station'],
                'distance': track['distance_km'],
                'speed_limit': track['speed_kmph'],
                'raw_data': track
            })
            node_to_idx[track_id] = len(all_nodes) - 1
        
        # Add block nodes if available
        for block in blocks:
            if len(block['connected_stations']) >= 2:
                block_id = block['block_name']
                all_nodes.append({
                    'type': 'block',
                    'id': block_id,
                    'length': block.get('length', 5.0),
                    'stations': block['connected_stations'],
                    'raw_data': block
                })
                node_to_idx[block_id] = len(all_nodes) - 1
        
        N = len(all_nodes)
        
        # Create node features [N, 10] - expanded for centralized approach
        node_features = np.zeros((N, 10), dtype=np.float32)
        
        for i, node in enumerate(all_nodes):
            if node['type'] == 'station':
                node_features[i, 0] = 1.0  # is_station
                node_features[i, 1] = 0.0  # not_track
                node_features[i, 2] = node['platforms'] / 6.0  # normalized platforms
                node_features[i, 3] = 0.0  # current_occupancy (set at runtime)
                node_features[i, 4] = 0.0  # platform_usage (set at runtime)
                
            elif node['type'] == 'track':
                node_features[i, 0] = 0.0  # not_station
                node_features[i, 1] = 1.0  # is_track
                node_features[i, 2] = node['distance'] / 25.0  # normalized distance
                node_features[i, 3] = 0.0  # track_occupied (set at runtime)
                node_features[i, 4] = node['speed_limit'] / 160.0  # normalized speed
                node_features[i, 5] = 0.0  # time_until_free (set at runtime)
                node_features[i, 6] = 0.0  # headway_satisfied (set at runtime)
                
            # Features 7-9 reserved for runtime train information
            node_features[i, 7] = 0.0  # train_priority (set when train present)
            node_features[i, 8] = 0.0  # train_delay (set when train present)
            node_features[i, 9] = 0.0  # decision_required (set at runtime)
        
        # Create adjacency matrix [N, N]
        adjacency = np.zeros((N, N), dtype=np.float32)
        
        # Connect stations to their track segments
        for track in tracks:
            from_idx = node_to_idx[track['from_station']]
            to_idx = node_to_idx[track['to_station']]
            track_idx = node_to_idx[f"{track['from_station']}-{track['to_station']}"]
            
            # Bidirectional connections: station <-> track
            adjacency[from_idx, track_idx] = 1.0
            adjacency[track_idx, from_idx] = 1.0
            adjacency[to_idx, track_idx] = 1.0
            adjacency[track_idx, to_idx] = 1.0
        
        return {
            'node_features': node_features,
            'adjacency_matrix': adjacency,
            'node_mapping': node_to_idx,
            'nodes': all_nodes,
            'stations': {s['code']: s for s in stations},
            'tracks': tracks
        }

# Usage function
def load_mumbai_network_from_neo4j():
    """Load Mumbai railway network for DQN training"""
    extractor = Neo4jGNNExtractor(
        uri="bolt://localhost:7687",  # Update with your Neo4j details
        user="neo4j",
        password="your_password"
    )
    
    # Define corridor for prototype - Central line key stations
    central_line_stations = ['CSMT', 'DR', 'KR', 'TNA', 'MAS', 'LTT']
    
    try:
        graph_data = extractor.extract_mumbai_central_corridor(central_line_stations)
        print(f"Extracted {len(graph_data['nodes'])} nodes from Neo4j")
        print(f"Stations: {list(graph_data['stations'].keys())}")
        return graph_data
        
    except Exception as e:
        print(f"Neo4j extraction failed: {e}")
        print("Falling back to simulated network...")
        return create_fallback_network()

def create_fallback_network():
    """Fallback network if Neo4j is unavailable"""
    stations = {
        'CSMT': {'code': 'CSMT', 'name': 'Mumbai CSM Terminus', 'platforms': 6},
        'DR': {'code': 'DR', 'name': 'Dadar', 'platforms': 4},
        'KR': {'code': 'KR', 'name': 'Kurla', 'platforms': 3},
        'TNA': {'code': 'TNA', 'name': 'Thane', 'platforms': 4}
    }
    
    tracks = [
        {'from_station': 'CSMT', 'to_station': 'DR', 'distance_km': 12, 'speed_kmph': 100},
        {'from_station': 'DR', 'to_station': 'KR', 'distance_km': 8, 'speed_kmph': 90},
        {'from_station': 'KR', 'to_station': 'TNA', 'distance_km': 15, 'speed_kmph': 110}
    ]
    
    extractor = Neo4jGNNExtractor("", "", "")  # Dummy instance for conversion
    return extractor._convert_to_gnn_format(
        [stations[k] for k in stations], 
        tracks, 
        []
    )