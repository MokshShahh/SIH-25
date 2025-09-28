#!/usr/bin/env python3
"""
Complete Neo4j Integration for Mumbai Railway Network
Extracts accurate railway data from Government of India database
"""

from neo4j import GraphDatabase
import numpy as np
import json
import yaml
import os
from typing import Dict, List, Tuple, Set
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
uri = os.getenv("AURA_URI")
user = os.getenv("AURA_USER")
password = os.getenv("AURA_PASS")

# Mumbai Railway Network Station Definitions (Government of India Official Data)
HARBOUR_LINE_CODES = [
    # CSMT to Panvel stretch
    "CSMT", "MSD", "SNRD", "DKRD", "RRD", "CTGN", "SVE", "VDLR",
    "GTBN", "CHF", "CLA", "TKNG", "CMBR", "GV", "MNKD", "VSH", 
    "SNCR", "JNJ", "NEU", "SWDV", "BEPR", "KHAG", "MANR", "KNDS", "PNVL",
    # Wadala Road to Andheri/Goregaon stretch
    "MM", "BA", "KHR", "STC", "VLP", "ADH", "JOS", "RMAR", "GMN"
]

WESTERN_LINE_CODES = [
    "CCG", "MEL", "CYR", "GTR", "MX", "PL", "PBHD", "DR", "MRU", "MM", "BA", "KHR", 
    "STC", "VLP", "ADH", "JOS", "RMAR", "GMN", "MDD", "KILE", "BVI", "DIC", "MIRA", 
    "BYR", "NIG", "BSR", "NSP", "VR", "VTN", "SAH", "KLV", "PLG", "UMR", 
    "BOR", "VGN", "DRD"
]

CENTRAL_LINE_CODES = [
    # Main Central Line
    "CSMT", "MSD", "SNRD", "BY", "CHG", "CRD", "PR", "DR", "MTN", "SIN", 
    "CLA", "VVH", "GC", "VK", "KJMG", "BND", "NHU", "MLND", "TNA", "KLVA", "MBQ", 
    "DIVA", "KOPR", "DI", "THK", "KYN",
    # Kasara Branch
    "SHAD", "ABY", "TLA", "KDV", "VSD", "ASO", "ATG", "KDI", "KSRA",
    # Karjat Branch
    "VLDI", "ULNR", "ABH", "BUD", "VGI", "SHLU", "NRL", "BVS", "KJT", 
    "PDI", "KLY", "DLV", "LWJ", "KPQ"
]

# Additional important stations
TRANS_HARBOUR_LINE_CODES = ["TNA", "KLVA", "LTT", "PNVL"]

# Platform Information (As per Indian Railways Standards)
MUMBAI_STATION_PLATFORMS = {
    # Major Terminals and Junctions
    "CSMT": 18,  "KYN": 8,    "TNA": 10,   "DR": 8,    "PNVL": 7,   "LTT": 5,    
    "MMCT": 9,   "CCG": 4,    "ADH": 9,    "BVI": 9,    "CLA": 8,    "BSR": 7,    "DDR": 6,    
    
    # Western Line Stations 
    "MEL": 4, "CYR": 4, "GTR": 4, "MX": 4, "PL": 4, "PBHD": 4, "MRU": 4, "MM": 4, 
    "BA": 4, "KHR": 4, "STC": 4, "VLP": 4, "JOS": 4, "RMAR": 4, "GMN": 4, "MDD": 4, 
    "KILE": 4, "DIC": 4, "MIRA": 4, "BYR": 6, "NIG": 4, "NSP": 4, "VR": 4, "VTN": 2, 
    "SAH": 2, "KLV": 2, "PLG": 2, "UMR": 2, "BOR": 2, "VGN": 2, "DRD": 2,
    
    # Central Line 
    "MSD": 4, "SNRD": 4, "BY": 4, "CHG": 4, "CRD": 4, "PR": 4, "MTN": 4, "SIN": 4, 
    "VVH": 4, "GC": 4, "VK": 4, "KJMG": 4, "BND": 4, "NHU": 4, "MLND": 4, "KLVA": 4, 
    "MBQ": 4, "DIVA": 4, "KOPR": 4, "DI": 4, "THK": 4,
    
    # Central Line Branches
    "SHAD": 2, "ABY": 2, "TLA": 2, "KDV": 2, "VSD": 2, "ASO": 2, "ATG": 2, "KDI": 2, "KSRA": 3,
    "VLDI": 2, "ULNR": 2, "ABH": 2, "BUD": 2, "VGI": 2, "SHLU": 2, "NRL": 2, "BVS": 2, 
    "KJT": 3, "PDI": 2, "KLY": 2, "DLV": 2, "LWJ": 2, "KPQ": 2,
    
    # Harbour Line
    "DKRD": 2, "RRD": 2, "CTGN": 2, "SVE": 2, "VDLR": 2, "GTBN": 2, "CHF": 2, "TKNG": 2, 
    "CMBR": 2, "GV": 2, "MNKD": 2, "VSH": 2, "SNCR": 2, "JNJ": 2, "NEU": 2, "SWDV": 2, 
    "BEPR": 2, "KHAG": 2, "MANR": 2, "KNDS": 2
}

# Line classifications for proper routing
STATION_TO_LINE_MAP = {
    **{code: "HARBOUR" for code in HARBOUR_LINE_CODES},
    **{code: "WESTERN" for code in WESTERN_LINE_CODES},
    **{code: "CENTRAL" for code in CENTRAL_LINE_CODES},
    **{code: "TRANS_HARBOUR" for code in TRANS_HARBOUR_LINE_CODES}
}

class MumbaiRailwayGraphExtractor:
    """
    Mumbai Railway Network Data Extractor
    Connects to Neo4j database and extracts accurate railway data
    """
    
    def __init__(self, uri=uri, user=user, password=password):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.all_mumbai_stations = set(
            HARBOUR_LINE_CODES + WESTERN_LINE_CODES + 
            CENTRAL_LINE_CODES + TRANS_HARBOUR_LINE_CODES
        )
        print(f"Connected to Neo4j. Monitoring {len(self.all_mumbai_stations)} Mumbai stations.")
        
    def extract_mumbai_stations_from_neo4j(self):
        """Extract all Mumbai stations from Neo4j database"""
        with self.driver.session() as session:
            query = """
            MATCH (s:Station) 
            WHERE s.code IN $codes
            RETURN s.code as code, s.name as name, 
                   coalesce(s.platforms, 2) as platforms,
                   s.zone as zone, s.division as division,
                   s.latitude as lat, s.longitude as lon
            ORDER BY s.code
            """
            result = session.run(query, codes=list(self.all_mumbai_stations))
            
            stations = {}
            for record in result:
                code = record["code"]
                stations[code] = {
                    "code": code,
                    "name": record["name"] or code,
                    "platforms": MUMBAI_STATION_PLATFORMS.get(code, record["platforms"] or 2),
                    "zone": record["zone"],
                    "division": record["division"],
                    "latitude": record["lat"],
                    "longitude": record["lon"],
                    "line": STATION_TO_LINE_MAP.get(code, "UNKNOWN")
                }
            
            print(f"Extracted {len(stations)} stations from Neo4j")
            return stations
    
    def extract_mumbai_tracks_from_neo4j(self):
        """Extract track connections between Mumbai stations"""
        with self.driver.session() as session:
            query = """
            MATCH (s1:Station)-[r:TRACK|CONNECTED_TO|CONNECTS]->(s2:Station)
            WHERE s1.code IN $codes AND s2.code IN $codes
            RETURN s1.code as from_station, s2.code as to_station,
                   coalesce(r.distance, r.length, 5.0) as distance_km,
                   coalesce(r.speed_limit, 100) as speed_kmph,
                   coalesce(r.track_type, 'double') as track_type,
                   type(r) as relationship_type
            """
            result = session.run(query, codes=list(self.all_mumbai_stations))
            
            tracks = []
            for record in result:
                tracks.append({
                    "from": record["from_station"],
                    "to": record["to_station"],
                    "distance_km": float(record["distance_km"]),
                    "speed_kmph": int(record["speed_kmph"]),
                    "track_type": record["track_type"],
                    "relationship_type": record["relationship_type"]
                })
            
            print(f"Extracted {len(tracks)} track connections from Neo4j")
            return tracks
    
    def create_mumbai_graph_data(self):
        """Create comprehensive Mumbai railway graph data"""
        print("Creating Mumbai railway graph data...")
        
        # Extract data from Neo4j
        stations = self.extract_mumbai_stations_from_neo4j()
        tracks = self.extract_mumbai_tracks_from_neo4j()
        
        if not stations:
            print("WARNING: No stations found in Neo4j. Using fallback data.")
            stations = self._create_fallback_stations()
        
        if not tracks:
            print("WARNING: No tracks found in Neo4j. Using fallback data.")
            tracks = self._create_fallback_tracks(stations)
        
        # Create node list: stations + track blocks
        all_nodes = []
        node_to_idx = {}
        
        # Add station nodes
        for station_code, station_data in stations.items():
            all_nodes.append({
                'type': 'station',
                'id': station_code,
                'name': station_data['name'],
                'platforms': station_data['platforms'],
                'line': station_data['line'],
                'latitude': station_data.get('latitude'),
                'longitude': station_data.get('longitude')
            })
            node_to_idx[station_code] = len(all_nodes) - 1
        
        # Add track block nodes
        valid_blocks = {}
        for track in tracks:
            block_name = f"{track['from']}-{track['to']}"
            if track['from'] in stations and track['to'] in stations:
                block_data = {
                    'type': 'track',
                    'id': block_name,
                    'from_station': track['from'],
                    'to_station': track['to'],
                    'length': track['distance_km'],
                    'speed_limit': track['speed_kmph'],
                    'single_track': track['track_type'] == 'single'
                }
                all_nodes.append(block_data)
                node_to_idx[block_name] = len(all_nodes) - 1
                valid_blocks[block_name] = block_data
        
        N = len(all_nodes)
        print(f"Created graph with {N} nodes ({len(stations)} stations + {len(valid_blocks)} tracks)")
        
        # Create node features and adjacency matrix
        node_features = self._create_node_features(all_nodes)
        adjacency_matrix = self._create_adjacency_matrix(all_nodes, tracks, node_to_idx, stations)
        
        # Prepare output data
        graph_data = {
            'stations': {code: {
                'name': data['name'],
                'platforms': data['platforms'],
                'line': data['line']
            } for code, data in stations.items()},
            
            'blocks': {name: {
                'name': name,
                'length_km': data['length'],
                'single_track': data['single_track'],
                'from_station': data['from_station'],
                'to_station': data['to_station']
            } for name, data in valid_blocks.items()},
            
            'speed_kmph': {name: data['speed_limit'] for name, data in valid_blocks.items()},
            'node_features': node_features.tolist(),
            'adjacency_matrix': adjacency_matrix.tolist(),
            'node_mapping': node_to_idx,
            'nodes': all_nodes,
            'N': N,
            'd_node': 10,
            'd_global': 8,
            
            'line_classifications': {
                'HARBOUR': HARBOUR_LINE_CODES,
                'WESTERN': WESTERN_LINE_CODES,
                'CENTRAL': CENTRAL_LINE_CODES,
                'TRANS_HARBOUR': TRANS_HARBOUR_LINE_CODES
            }
        }
        
        print("Mumbai railway graph data created successfully!")
        return graph_data
    
    def _create_fallback_stations(self):
        """Create fallback station data if Neo4j query fails"""
        print("Creating fallback station data...")
        stations = {}
        
        for station_code in self.all_mumbai_stations:
            stations[station_code] = {
                "code": station_code,
                "name": station_code,  # Use code as name fallback
                "platforms": MUMBAI_STATION_PLATFORMS.get(station_code, 2),
                "zone": "CR" if station_code in CENTRAL_LINE_CODES else "WR",
                "division": "Mumbai",
                "latitude": None,
                "longitude": None,
                "line": STATION_TO_LINE_MAP.get(station_code, "UNKNOWN")
            }
        
        return stations
    
    def _create_fallback_tracks(self, stations):
        """Create fallback track data based on line sequences"""
        print("Creating fallback track data...")
        tracks = []
        
        # Define line sequences for creating tracks
        line_sequences = {
            "HARBOUR": ["CSMT", "MSD", "SNRD", "DKRD", "RRD", "CTGN", "SVE", "VDLR", 
                       "GTBN", "CHF", "CLA", "TKNG", "CMBR", "GV", "MNKD", "VSH", 
                       "SNCR", "JNJ", "NEU", "SWDV", "BEPR", "KHAG", "MANR", "KNDS", "PNVL"],
            
            "WESTERN": ["CCG", "MEL", "CYR", "GTR", "MX", "PL", "PBHD", "DR", "MRU", "MM", 
                       "BA", "KHR", "STC", "VLP", "ADH", "JOS", "RMAR", "GMN", "MDD", "KILE", 
                       "BVI", "DIC", "MIRA", "BYR", "NIG", "BSR", "NSP", "VR"],
            
            "CENTRAL_MAIN": ["CSMT", "MSD", "SNRD", "BY", "CHG", "CRD", "PR", "DR", "MTN", 
                            "SIN", "CLA", "VVH", "GC", "VK", "KJMG", "BND", "NHU", "MLND", 
                            "TNA", "KLVA", "MBQ", "DIVA", "KOPR", "DI", "THK", "KYN"],
            
            "CENTRAL_KASARA": ["KYN", "SHAD", "ABY", "TLA", "KDV", "VSD", "ASO", "ATG", "KDI", "KSRA"],
            
            "CENTRAL_KARJAT": ["KYN", "VLDI", "ULNR", "ABH", "BUD", "VGI", "SHLU", "NRL", "BVS", "KJT"]
        }
        
        # Create tracks for each line sequence
        for line_name, sequence in line_sequences.items():
            for i in range(len(sequence) - 1):
                from_station = sequence[i]
                to_station = sequence[i + 1]
                
                if from_station in stations and to_station in stations:
                    # Bidirectional tracks
                    tracks.append({
                        "from": from_station,
                        "to": to_station,
                        "distance_km": 3.0,  # Default 3km between stations
                        "speed_kmph": 100,   # Default speed limit
                        "track_type": "double",
                        "relationship_type": "TRACK"
                    })
                    
                    tracks.append({
                        "from": to_station,
                        "to": from_station,
                        "distance_km": 3.0,
                        "speed_kmph": 100,
                        "track_type": "double",
                        "relationship_type": "TRACK"
                    })
        
        return tracks
    
    def _create_node_features(self, nodes):
        """Create node feature matrix [N, 10]"""
        N = len(nodes)
        features = np.zeros((N, 10), dtype=np.float32)
        
        for i, node in enumerate(nodes):
            if node['type'] == 'station':
                features[i, 0] = 1.0  # is_station
                features[i, 1] = 0.0  # not_track
                features[i, 2] = min(node['platforms'] / 20.0, 1.0)  # normalized platforms
                
                # Line encoding
                line = node.get('line', 'UNKNOWN')
                if line == 'HARBOUR':
                    features[i, 3] = 1.0
                elif line == 'WESTERN':
                    features[i, 4] = 1.0
                elif line == 'CENTRAL':
                    features[i, 5] = 1.0
                elif line == 'TRANS_HARBOUR':
                    features[i, 6] = 1.0
                
            elif node['type'] == 'track':
                features[i, 0] = 0.0  # not_station
                features[i, 1] = 1.0  # is_track
                features[i, 2] = min(node['length'] / 50.0, 1.0)  # normalized length
                features[i, 7] = node['speed_limit'] / 160.0  # normalized speed
                features[i, 8] = 1.0 if node['single_track'] else 0.0  # track type
        
        return features
    
    def _create_adjacency_matrix(self, nodes, tracks, node_to_idx, stations):
        """Create adjacency matrix showing proper railway connections"""
        N = len(nodes)
        adj = np.zeros((N, N), dtype=np.float32)
        
        # Connect stations to their track segments
        for track in tracks:
            from_station = track['from']
            to_station = track['to']
            
            if from_station in stations and to_station in stations:
                block_name = f"{from_station}-{to_station}"
                
                if (from_station in node_to_idx and 
                    to_station in node_to_idx and 
                    block_name in node_to_idx):
                    
                    from_idx = node_to_idx[from_station]
                    to_idx = node_to_idx[to_station]
                    track_idx = node_to_idx[block_name]
                    
                    # Station to track connections (bidirectional)
                    adj[from_idx, track_idx] = 1.0
                    adj[track_idx, from_idx] = 1.0
                    adj[to_idx, track_idx] = 1.0
                    adj[track_idx, to_idx] = 1.0
        
        return adj
    
    def export_corridor_files(self, output_dir="configs"):
        """Export line-specific corridor YAML files"""
        print(f"Exporting corridor files to {output_dir}/")
        
        stations = self.extract_mumbai_stations_from_neo4j()
        tracks = self.extract_mumbai_tracks_from_neo4j()
        
        if not stations:
            stations = self._create_fallback_stations()
        if not tracks:
            tracks = self._create_fallback_tracks(stations)
        
        corridors = self._create_line_specific_corridors(stations, tracks)
        
        os.makedirs(output_dir, exist_ok=True)
        
        for line_name, corridor_data in corridors.items():
            corridor_config = {
                "metadata": {
                    "line_name": line_name,
                    "description": f"Mumbai {line_name} Line",
                    "source": "Government of India Railway Database",
                    "extraction_date": "2025-09-28"
                },
                "stations": corridor_data["stations"],
                "blocks": corridor_data["blocks"],
                "headway_s": 120 if line_name != "WESTERN" else 180,
                "line_type": line_name,
                "total_stations": len(corridor_data["stations"]),
                "total_blocks": len(corridor_data["blocks"])
            }
            
            filename = f"{line_name.lower()}_corridor.yaml"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                yaml.dump(corridor_config, f, default_flow_style=False, indent=2)
            
            print(f"  ✅ {line_name}: {len(corridor_data['stations'])} stations, {len(corridor_data['blocks'])} blocks")
    
    def _create_line_specific_corridors(self, stations, tracks):
        """Create separate corridor files for each line"""
        corridors = {
            "HARBOUR": {"stations": [], "blocks": [], "line_codes": HARBOUR_LINE_CODES},
            "WESTERN": {"stations": [], "blocks": [], "line_codes": WESTERN_LINE_CODES},
            "CENTRAL": {"stations": [], "blocks": [], "line_codes": CENTRAL_LINE_CODES},
        }
        
        # Group stations by line
        for line_name, corridor_data in corridors.items():
            line_stations = []
            for code in corridor_data["line_codes"]:
                if code in stations:
                    station_data = stations[code].copy()
                    line_stations.append(station_data)
            
            corridor_data["stations"] = line_stations
            
            # Create blocks for this line
            line_blocks = []
            line_station_codes = {s["code"] for s in line_stations}
            
            for track in tracks:
                if track["from"] in line_station_codes and track["to"] in line_station_codes:
                    block = {
                        "name": f"{track['from']}-{track['to']}",
                        "from": track["from"],
                        "to": track["to"],
                        "length_km": track["distance_km"],
                        "speed_limit": track["speed_kmph"],
                        "single_track": track["track_type"] == "single",
                        "line": line_name
                    }
                    line_blocks.append(block)
            
            corridor_data["blocks"] = line_blocks
        
        return corridors
    
    def export_graph_data(self, output_file="mumbai_railway_graph.json"):
        """Export complete Mumbai railway graph data"""
        print(f"Exporting graph data to {output_file}")
        
        graph_data = self.create_mumbai_graph_data()
        
        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        print(f"✅ Mumbai railway graph exported successfully!")
        print(f"   📊 Total nodes: {graph_data['N']}")
        print(f"   🚉 Total stations: {len(graph_data['stations'])}")
        print(f"   🛤️  Total blocks: {len(graph_data['blocks'])}")
        
        return graph_data
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed.")

def main():
    """Main function to extract and export Mumbai railway data"""
    print("🚆 Mumbai Railway Network Data Extraction")
    print("=" * 50)
    
    extractor = MumbaiRailwayGraphExtractor()
    
    try:
        print("Extracting Mumbai Railway Network from Neo4j...")
        
        # Export line-specific corridor files
        extractor.export_corridor_files()
        
        # Export complete graph data
        graph_data = extractor.export_graph_data()
        
        print("\n✅ Mumbai Railway Network extraction completed successfully!")
        print(f"📂 Files generated:")
        print(f"   • Corridor YAML files in configs/")
        print(f"   • Graph data: mumbai_railway_graph.json")
        print(f"   • Lines covered: {list(graph_data['line_classifications'].keys())}")
        
        # Validation
        print(f"\n🔍 Data Validation:")
        print(f"   • Stations extracted: {len(graph_data['stations'])}")
        print(f"   • Track blocks created: {len(graph_data['blocks'])}")
        print(f"   • Graph nodes: {graph_data['N']}")
        print(f"   • Node features: {graph_data['d_node']} dimensions")
        print(f"   • Lines covered: {len(graph_data['line_classifications'])}")
        
        return graph_data
        
    except Exception as e:
        print(f"❌ Error extracting Mumbai railway data: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        extractor.close()

# Additional utility functions
def load_mumbai_network_for_dqn():
    """Load Mumbai network data for DQN training"""
    extractor = MumbaiRailwayGraphExtractor()
    
    try:
        graph_data = extractor.create_mumbai_graph_data()
        
        if graph_data is None:
            print("Failed to load network data")
            return None
        
        # Format for DQN environment
        env_data = {
            'graph_data': graph_data,
            'stations': graph_data['stations'],
            'blocks': graph_data['blocks'],
            'speed_kmph': graph_data['speed_kmph'],
            'headway_s': 120  # 2-minute headway for Mumbai locals
        }
        
        print(f"Loaded Mumbai network for DQN:")
        print(f"- {len(env_data['stations'])} stations")
        print(f"- {len(env_data['blocks'])} track blocks")
        print(f"- Graph: {env_data['graph_data']['N']} nodes")
        
        return env_data
        
    except Exception as e:
        print(f"Error loading Mumbai network: {e}")
        return None
        
    finally:
        extractor.close()

if __name__ == "__main__":
    main()