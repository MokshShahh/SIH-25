from neo4j import GraphDatabase
import numpy as np
<<<<<<< HEAD
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
=======
import yaml, json
import os
from dotenv import load_dotenv

load_dotenv()

class Neo4jToGNN:
    def __init__(self):
        self.uri = os.getenv("AURA_URI")
        self.user = os.getenv("AURA_USER") 
        self.password = os.getenv("AURA_PASS")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
>>>>>>> cea37b0c018244dd7f55b0f5ac4049315f7c575c
    
    def extract_mumbai_graph(self):
        """Extract Mumbai railway network and convert to GNN format"""
        
        # Load the corridor data we created
        try:
            with open('configs/mumbai_corridor.yaml', 'r') as f:
                corridor_data = yaml.safe_load(f)
        except FileNotFoundError:
            print("Run datahandling.py first to create corridor data")
            return None
        
        stations = corridor_data['stations']
        blocks = corridor_data['blocks']
        
        # Build node list: stations + track blocks
        all_nodes = []
        node_to_idx = {}
        
        # Add station nodes
        for station in stations:
            node_id = station['code']
            all_nodes.append({
                'type': 'station',
                'id': node_id,
                'name': station['name'],
                'platforms': station['platforms']
            })
            node_to_idx[node_id] = len(all_nodes) - 1
        
        # Add track block nodes
        for block in blocks:
            node_id = block['name']  # e.g., "CSMT-DR"
            all_nodes.append({
                'type': 'track',
                'id': node_id,
                'from_station': block['from'],
                'to_station': block['to'],
                'length': block['length_km'],
                'speed_limit': block['speed_limit']
            })
            node_to_idx[node_id] = len(all_nodes) - 1
        
        N = len(all_nodes)
        print(f"Created graph with {N} nodes ({len(stations)} stations + {len(blocks)} tracks)")
        
        # Create node features [N, 10]
        node_features = self._create_node_features(all_nodes)
        
        # Create adjacency matrix [N, N]  
        adjacency_matrix = self._create_adjacency_matrix(all_nodes, blocks, node_to_idx)
        
        return {
            'node_features': node_features,
            'adjacency_matrix': adjacency_matrix,
            'node_mapping': node_to_idx,
            'nodes': all_nodes,
            'N': N,
            'd_node': 10,
            'd_global': 8
        }
    
    def _create_node_features(self, nodes):
        """Create node feature matrix [N, 10]"""
        N = len(nodes)
        features = np.zeros((N, 10), dtype=np.float32)
        
        for i, node in enumerate(nodes):
            if node['type'] == 'station':
                features[i, 0] = 1.0  # is_station
                features[i, 1] = 0.0  # not_track
                features[i, 2] = node['platforms'] / 20.0  # normalized platforms
                # Features 3-4: runtime occupancy data (filled during simulation)
                
            elif node['type'] == 'track':
                features[i, 0] = 0.0  # not_station
                features[i, 1] = 1.0  # is_track
                features[i, 2] = node['length'] / 30.0  # normalized length
                features[i, 3] = node['speed_limit'] / 160.0  # normalized speed
                # Features 4-6: runtime track occupancy data
            
            # Features 7-9: runtime train information (priority, delay, decision_flag)
            # These will be filled during DQN simulation
        
        return features
    
    def _create_adjacency_matrix(self, nodes, blocks, node_to_idx):
        """Create adjacency matrix [N, N] showing connections"""
        N = len(nodes)
        adj = np.zeros((N, N), dtype=np.float32)
        
        # Connect stations to their track segments
        for block in blocks:
            from_station = block['from']
            to_station = block['to']
            track_name = block['name']
            
            # Get indices
            from_idx = node_to_idx[from_station]
            to_idx = node_to_idx[to_station]
            track_idx = node_to_idx[track_name]
            
            # Connections: station <-> track (bidirectional)
            adj[from_idx, track_idx] = 1.0
            adj[track_idx, from_idx] = 1.0
            adj[to_idx, track_idx] = 1.0
            adj[track_idx, to_idx] = 1.0
        
        return adj
    
    def create_environment_data(self):
        """Create data structure for the DQN environment"""
        graph_data = self.extract_mumbai_graph()
        
        if graph_data is None:
            return None
        
        # Extract station and block info for environment
        stations = {}
        blocks = {}
        speed_kmph = {}
        
        for node in graph_data['nodes']:
            if node['type'] == 'station':
                stations[node['id']] = {
                    'name': node['name'],
                    'platforms': node['platforms']
                }
            elif node['type'] == 'track':
                block_name = node['id']
                blocks[block_name] = {
                    'name': block_name,
                    'length_km': node['length'],
                    'single_track': False  # Mumbai has multiple tracks
                }
                speed_kmph[block_name] = node['speed_limit']
        
        return {
            'graph_data': graph_data,
            'stations': stations,
            'blocks': blocks,
            'speed_kmph': speed_kmph,
            'headway_s': 120  # 2-minute headway for Mumbai locals
        }
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

def load_mumbai_network_for_dqn():
    """Main function to load Mumbai network for DQN training"""
    
    neo4j_connector = Neo4jToGNN()
    
    try:
        env_data = neo4j_connector.create_environment_data()
        
        if env_data is None:
            print("Failed to load network data")
            return None
        
        print(f"Loaded Mumbai network:")
        print(f"- {len(env_data['stations'])} stations")
        print(f"- {len(env_data['blocks'])} track blocks")
        print(f"- Graph: {env_data['graph_data']['N']} nodes")
        print(f"- Features: {env_data['graph_data']['d_node']} dimensions per node")
        
        return env_data
        
    except Exception as e:
        print(f"Error loading Mumbai network: {e}")
        return None
        
    finally:
        neo4j_connector.close()

def test_graph_structure():
    """Test function to verify graph structure"""
    env_data = load_mumbai_network_for_dqn()
    
    if env_data:
        graph = env_data['graph_data']
        print(f"\nGraph structure test:")
        print(f"Node features shape: {graph['node_features'].shape}")
        print(f"Adjacency matrix shape: {graph['adjacency_matrix'].shape}")
        print(f"Total connections: {np.sum(graph['adjacency_matrix'])}")
        
        # Show first few nodes
        print(f"\nFirst 3 nodes:")
        for i, node in enumerate(graph['nodes'][:3]):
            print(f"  {i}: {node['type']} - {node['id']}")


if __name__ == "__main__":
    test_graph_structure()

def export_graph_data(output_file="mumbai_graph_data.json"):
    """Export your Neo4j graph data to JSON for Colab"""
    env_data = load_mumbai_network_for_dqn()
    
    if env_data:
        # Convert numpy arrays to lists for JSON serialization
        export_data = {
            'stations': env_data['stations'],
            'blocks': env_data['blocks'],
            'speed_kmph': env_data['speed_kmph'],
            'node_features': env_data['graph_data']['node_features'].tolist(),
            'adjacency_matrix': env_data['graph_data']['adjacency_matrix'].tolist(),
            'node_mapping': env_data['graph_data']['node_mapping'],
            'nodes': env_data['graph_data']['nodes'],
            'N': env_data['graph_data']['N'],
            'd_node': env_data['graph_data']['d_node'],
            'd_global': env_data['graph_data']['d_global']
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Graph data exported to {output_file}")
        return export_data
    return None

if __name__ == "__main__":
    # Export your graph data
    export_graph_data("mumbai_graph_data.json")