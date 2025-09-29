import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
import json
import os
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from collections import deque
import random

@dataclass
class Train:
    tid: str
    origin: str
    dest: str
    route_blocks: List[str]
    sched_departure_s: int
    sched_arrival_s: int
    priority: int
    type: str
    dwell_rules: Dict[str, int] = field(default_factory=dict)

class ManualGCNLayer(tf.keras.layers.Layer):
    def __init__(self, units, **kwargs):
        super().__init__(**kwargs)
        self.units = units

    def build(self, input_shape):
        node_features = input_shape[0][-1]
        self.kernel = self.add_weight(
            name='kernel',
            shape=(node_features, self.units),
            initializer='glorot_uniform',
            trainable=True
        )
        self.bias = self.add_weight(
            name='bias',
            shape=(self.units,),
            initializer='zeros',
            trainable=True
        )
        super().build(input_shape)

    def call(self, inputs):
        x, a = inputs
        degree = tf.reduce_sum(a, axis=-1, keepdims=True)
        degree = tf.maximum(degree, 1.0)
        a_norm = a / degree
        ax = tf.matmul(a_norm, x)
        out = tf.matmul(ax, self.kernel) + self.bias
        return tf.nn.relu(out)

class ManualGlobalSumPool(tf.keras.layers.Layer):
    def call(self, x):
        return tf.reduce_sum(x, axis=1)

def setup_colab_environment():
    try:
        import google.colab
        from google.colab import drive
        IN_COLAB = True
        
        drive.mount('/content/drive')
        BASE_PATH = '/content/drive/MyDrive/mumbai_railway_dqn'
        
        os.makedirs(BASE_PATH, exist_ok=True)
        os.makedirs(f'{BASE_PATH}/models', exist_ok=True)
        os.makedirs(f'{BASE_PATH}/results', exist_ok=True)
        
        print("Google Colab environment setup complete")
        print(f"Base path: {BASE_PATH}")
        
        gpu_devices = tf.config.list_physical_devices('GPU')
        print(f"GPU Available: {len(gpu_devices) > 0}")
        
        return BASE_PATH, IN_COLAB
        
    except ImportError:
        print("Running locally")
        return '.', False

def load_scenario_files_from_upload():
    from google.colab import files
    import glob
    import json
    import os
    import re

    def find_best_path(prefix: str) -> Optional[str]:
        """
        Look for files named like:
          prefix.json
          prefix (1).json
          prefix (2).json
        Prefer the most recently modified one.
        """
        pattern = f"{prefix}*.json"  # e.g., 'central_karjat_scenario*.json'
        candidates = glob.glob(pattern)
        if not candidates:
            return None
        # pick most recent mtime
        candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return candidates[0]

    print("Please upload your JSON files:")
    uploaded = files.upload()  # may re-name duplicates with ' (1).json'
    print(f"{len(uploaded)} files")
    print("Uploaded keys:", list(uploaded.keys()))

    # Save uploaded bytes to disk (Colab already prints a “Saving … to …” line, but this ensures we have copies)
    for name, content in uploaded.items():
        with open(name, "wb") as f:
            f.write(content)
        # print(f"Saved {name}")

    # Helper to robustly load a JSON given a base prefix
    def load_json_by_prefix(prefix: str):
        path = find_best_path(prefix)
        if not path:
            raise FileNotFoundError(f"Could not find file for prefix '{prefix}' (tried '{prefix}*.json').")
        with open(path, "r") as f:
            return json.load(f), path

    # Load network/topology file (accepts mumbai_railway_graph_csv.json and its suffixed variants)
    graph_data, graph_path = load_json_by_prefix("mumbai_railway_graph_csv")
    print(f"Loaded network topology from: {graph_path}")

    # Load scenarios (each accepts suffixed variants)
    scenario_prefixes = [
        "central_karjat_scenario",
        "central_kasara_scenario",
        "central_main_scenario",
        "harbour_scenario",
        "western_scenario",
    ]

    all_scenarios = []
    for prefix in scenario_prefixes:
        try:
            data, path = load_json_by_prefix(prefix)
            trains = []
            for train_data in data:
                train = Train(
                    tid=train_data['tid'],
                    origin=train_data['origin'],
                    dest=train_data['dest'],
                    route_blocks=train_data['route_blocks'],
                    sched_departure_s=train_data['sched_departure_s'],
                    sched_arrival_s=train_data['sched_arrival_s'],
                    priority=train_data['priority'],
                    type=train_data['type'],
                    dwell_rules=train_data.get('dwell_rules', {})
                )
                trains.append(train)
            all_scenarios.append(trains)
            print(f"Loaded {len(trains)} trains from {os.path.basename(path)}")
        except Exception as e:
            print(f"Warning: failed to load scenario for prefix '{prefix}': {e}")

    if not all_scenarios:
        raise ValueError("No valid scenario files were loaded")

    return all_scenarios, graph_data


def create_network_from_graph_data(graph_data):
    if graph_data is None:
        return None
    
    try:
        stations = graph_data.get('stations', {})
        blocks = graph_data.get('blocks', {})
        speed_kmph = graph_data.get('speed_kmph', {})
        
        if 'node_features' in graph_data and 'adjacency_matrix' in graph_data:
            print("Using pre-processed graph features")
            node_features = np.array(graph_data['node_features'], dtype=np.float32)
            adjacency_matrix = np.array(graph_data['adjacency_matrix'], dtype=np.float32)
            if node_features.ndim != 2:
              raise ValueError(f"node_features must be 2D [N, F], got shape {node_features.shape}")
            F = node_features.shape[1]
            if F < 12:
              # pad zeros on the right up to 12 columns
              node_features = np.pad(node_features, ((0, 0), (0, 12 - F)), mode='constant')
              print(f"Padded node_features from {F} → 12 dims to match model.")
              F = 12
            elif F > 12:
              # (Option A) keep them and update d_node to F, but then update all index assumptions;
              # (Option B) truncate to 12 to keep current code unchanged:
              node_features = node_features[:, :12]
              print(f"Truncated node_features from {F} → 12 dims to match model.")
              F = 12
            if 'node_mapping' in graph_data:
                node_mapping = graph_data['node_mapping']
                all_nodes = graph_data.get('all_nodes', list(node_mapping.keys()))
            else:
                all_nodes = list(stations.keys()) + list(blocks.keys())
                node_mapping = {name: i for i, name in enumerate(all_nodes)}
            
            N = graph_data.get('N', len(node_mapping))
            
        else:
            print("Building graph features from raw data")
            all_nodes = list(stations.keys()) + list(blocks.keys())
            node_mapping = {name: i for i, name in enumerate(all_nodes)}
            N = len(all_nodes)
            
            node_features = np.zeros((N, 12), dtype=np.float32)
            
            for i, node_name in enumerate(all_nodes):
                if node_name in stations:
                    station = stations[node_name]
                    node_features[i, 0] = 1.0
                    platforms = station.get('platforms', 4)
                    node_features[i, 2] = min(platforms / 20.0, 1.0)
                    
                    line = station.get('line', 'UNKNOWN')
                    if line == 'HARBOUR':
                        node_features[i, 3] = 1.0
                    elif line == 'WESTERN':
                        node_features[i, 4] = 1.0
                    elif 'CENTRAL' in line:
                        node_features[i, 5] = 1.0
                        
                else:
                    block = blocks[node_name]
                    node_features[i, 1] = 1.0
                    length = block.get('length_km', 5.0)
                    node_features[i, 2] = min(length / 50.0, 1.0)
                    node_features[i, 7] = speed_kmph.get(node_name, 80) / 160.0
                    node_features[i, 8] = 1.0 if block.get('single_track', False) else 0.0
            
            adjacency_matrix = np.zeros((N, N), dtype=np.float32)
            
            for block_name, block_data in blocks.items():
                if block_name in node_mapping:
                    from_station = block_data.get('from_station')
                    to_station = block_data.get('to_station')
                    
                    if from_station in node_mapping and to_station in node_mapping:
                        block_idx = node_mapping[block_name]
                        from_idx = node_mapping[from_station]
                        to_idx = node_mapping[to_station]
                        
                        adjacency_matrix[from_idx, block_idx] = 1.0
                        adjacency_matrix[block_idx, from_idx] = 1.0
                        adjacency_matrix[to_idx, block_idx] = 1.0
                        adjacency_matrix[block_idx, to_idx] = 1.0
        
        network_data = {
            'stations': stations,
            'blocks': blocks,
            'speed_kmph': speed_kmph,
            'node_features': node_features,
            'adjacency_matrix': adjacency_matrix,
            'node_mapping': node_mapping,
            'all_nodes': all_nodes,
            'N': N,
            'd_node': 12,
            'd_global': 8
        }
        
        print(f"Network created: {len(stations)} stations, {len(blocks)} blocks")
        return network_data
        
    except Exception as e:
        print(f"Error creating network: {e}")
        return None

def create_mumbai_network_from_scenarios(scenarios):
    all_stations = set()
    all_blocks = set()
    block_connections = {}
    
    for scenario in scenarios:
        for train in scenario:
            all_stations.add(train.origin)
            all_stations.add(train.dest)
            
            for block in train.route_blocks:
                all_blocks.add(block)
                
                if '-' in block:
                    parts = block.split('-')
                    if len(parts) == 2:
                        from_station, to_station = parts
                        all_stations.add(from_station)
                        all_stations.add(to_station)
                        block_connections[block] = {
                            'from_station': from_station,
                            'to_station': to_station,
                            'length_km': np.random.uniform(3, 15),
                            'single_track': np.random.choice([True, False], p=[0.3, 0.7])
                        }
    
    stations = {}
    for station in all_stations:
        line = "CENTRAL_MAIN"
        if station in ["KYN", "BVS", "KJT", "BUD", "VGI", "VLDI", "ULNR", "ABH", "SHLU", "NRL"]:
            line = "CENTRAL_KARJAT"
        elif station in ["KSRA", "VSD", "ASO", "ATG", "KDI", "SHAD", "ABY", "TLA", "KDV"]:
            line = "CENTRAL_KASARA"
        elif station in ["PNVL", "KHAG", "KNDS", "DKRD", "RRD", "CTGN", "SVE", "VDLR", "GTBN"]:
            line = "HARBOUR"
        elif station in ["DRD", "VGN", "PLG", "UMR", "BOR", "MEL", "CYR", "GTR", "MX", "PL"]:
            line = "WESTERN"
        
        major_stations = ["CSMT", "KYN", "DR", "TNA", "PNVL", "DRD", "BYR"]
        platforms = np.random.randint(8, 18) if station in major_stations else np.random.randint(3, 8)
        
        stations[station] = {
            'name': station,
            'platforms': platforms,
            'line': line
        }
    
    blocks = {}
    for block in all_blocks:
        if block in block_connections:
            blocks[block] = block_connections[block]
        else:
            parts = block.split('-') if '-' in block else [block, block]
            blocks[block] = {
                'name': block,
                'length_km': np.random.uniform(3, 12),
                'from_station': parts[0],
                'to_station': parts[1] if len(parts) > 1 else parts[0],
                'single_track': False
            }
    
    speed_kmph = {}
    for block in blocks.keys():
        if any(st in ['CSMT', 'KYN', 'DR'] for st in [blocks[block]['from_station'], blocks[block]['to_station']]):
            speed_kmph[block] = np.random.randint(60, 100)
        else:
            speed_kmph[block] = np.random.randint(40, 80)
    
    all_nodes = list(stations.keys()) + list(blocks.keys())
    N = len(all_nodes)
    node_mapping = {node: i for i, node in enumerate(all_nodes)}
    
    node_features = np.zeros((N, 12), dtype=np.float32)
    
    for i, node_id in enumerate(all_nodes):
        if node_id in stations:
            station = stations[node_id]
            node_features[i, 0] = 1.0
            node_features[i, 2] = min(station['platforms'] / 20.0, 1.0)
            
            if station['line'] == 'HARBOUR':
                node_features[i, 3] = 1.0
            elif station['line'] == 'WESTERN':
                node_features[i, 4] = 1.0
            elif 'CENTRAL' in station['line']:
                node_features[i, 5] = 1.0
                
        else:
            block = blocks[node_id]
            node_features[i, 1] = 1.0
            node_features[i, 2] = min(block['length_km'] / 50.0, 1.0)
            node_features[i, 7] = speed_kmph.get(node_id, 80) / 160.0
            node_features[i, 8] = 1.0 if block.get('single_track', False) else 0.0
    
    adjacency_matrix = np.zeros((N, N), dtype=np.float32)
    
    for block_id, block_data in blocks.items():
        if block_id in node_mapping:
            from_station = block_data.get('from_station')
            to_station = block_data.get('to_station')
            
            if from_station in node_mapping and to_station in node_mapping:
                block_idx = node_mapping[block_id]
                from_idx = node_mapping[from_station]
                to_idx = node_mapping[to_station]
                
                adjacency_matrix[from_idx, block_idx] = 1.0
                adjacency_matrix[block_idx, from_idx] = 1.0
                adjacency_matrix[to_idx, block_idx] = 1.0
                adjacency_matrix[block_idx, to_idx] = 1.0
    
    return {
        'stations': stations,
        'blocks': blocks,
        'speed_kmph': speed_kmph,
        'node_features': node_features,
        'adjacency_matrix': adjacency_matrix,
        'node_mapping': node_mapping,
        'all_nodes': all_nodes,
        'N': N,
        'd_node': 12,
        'd_global': 8
    }

class ProperMaskedRailwayEnv:
    def __init__(self, network_data, tick_sec=10):
        self.stations = network_data['stations']
        self.blocks = network_data['blocks']
        self.speed_kmph = network_data.get('speed_kmph', {})
        self.node_features_template = network_data['node_features']
        self.adj_matrix = network_data['adjacency_matrix']
        self.node_mapping = network_data['node_mapping']
        self.all_nodes = network_data['all_nodes']
        self.N = network_data['N']
        
        self.headway_s = 180
        self.tick = tick_sec
        self.action_dim = 12
        self.d_node = network_data['d_node']
        self.d_global = network_data['d_global']
        
        self.ACTIONS = {
            0: "dispatch_highest_priority_train",
            1: "dispatch_longest_waiting_train", 
            2: "dispatch_shortest_route_train",
            3: "dispatch_by_route_efficiency",
            4: "dispatch_emergency_train",
            5: "dispatch_multiple_high_priority",
            6: "hold_all_trains_short",
            7: "hold_all_trains_long", 
            8: "dispatch_first_ready_train",
            9: "dispatch_by_destination_priority",
            10: "adaptive_dispatch",
            11: "do_nothing"
        }
        
        self.rng = np.random.default_rng(123)

    def reset(self, trains: List[Train]):
        self.t = 0
        self.TMAX = 40 * 60
        self.trains = []
        
        for t in trains:
            self.trains.append({
                "tid": t.tid,
                "route": list(t.route_blocks),
                "idx": -1,
                "pos_in_block": 0.0,
                "ready_time": t.sched_departure_s,
                "priority": t.priority,
                "dwell": dict(t.dwell_rules),
                "done": False,
                "actual_arrival": None,
                "sched_arrival": t.sched_arrival_s,
                "origin": t.origin,
                "dest": t.dest,
                "delay_accumulation": 0.0,
                "last_decision_time": -1
            })
        
        self.occ = {b: {"free_at": 0, "tid": None, "reserved_by": None} for b in self.blocks}
        self.last_exit = {b: -10**9 for b in self.blocks}
        
        return self._create_graph_state(), self._compute_action_mask()

    def _create_graph_state(self):
        node_feats = self.node_features_template.copy()
        node_feats[:, -3:] = 0.0
        
        decision_trains = self._get_decision_trains()
        
        for i, (train, current_block, _) in enumerate(decision_trains):
            if current_block in self.node_mapping:
                node_idx = self.node_mapping[current_block]
                node_feats[node_idx, -3] = min(train["priority"] / 10.0, 1.0)
                delay = max(0, self.t - train["ready_time"])
                node_feats[node_idx, -2] = min(delay / 600.0, 1.0)
                node_feats[node_idx, -1] = 1.0
        
        for block_id, occ_info in self.occ.items():
            if (occ_info["tid"] is not None or occ_info["reserved_by"] is not None) and block_id in self.node_mapping:
                node_idx = self.node_mapping[block_id]
                if node_feats.shape[1] > 8:
                    node_feats[node_idx, 8] = 1.0
        
        total_trains = len(self.trains)
        active_trains = len(decision_trains)
        completed_trains = sum(1 for tr in self.trains if tr["done"])
        
        completion_rate = completed_trains / max(1, total_trains)
        time_progress = self.t / self.TMAX
        total_delay = self._calculate_total_weighted_delay()
        
        occupied_blocks = sum(1 for occ in self.occ.values() 
                            if occ["tid"] is not None or occ["reserved_by"] is not None)
        congestion_rate = occupied_blocks / max(1, len(self.blocks))
        
        avg_priority = (np.mean([tr[0]["priority"] for tr in decision_trains]) / 10.0 
                       if decision_trains else 0.0)
        
        urgent_trains = sum(1 for tr, _, _ in decision_trains 
                          if (self.t - tr["ready_time"]) > 300)
        urgency_ratio = urgent_trains / max(1, len(decision_trains))
        
        global_feats = np.array([
            completion_rate, time_progress, total_delay, congestion_rate,
            avg_priority, urgency_ratio, active_trains / max(1, total_trains), 0.0
        ], dtype=np.float32)
        
        return node_feats, self.adj_matrix, global_feats

    def _get_decision_trains(self):
        decision_trains = []
        
        for train in self.trains:
            if train["done"]:
                continue
                
            current_node = None
            next_options = []
            
            if train["idx"] < 0 and self.t >= train["ready_time"]:
                if train["route"]:
                    current_node = train["route"][0]
                    next_options = [current_node]
                    
            elif (train["idx"] >= 0 and 
                  train["idx"] < len(train["route"]) and 
                  self.t >= train["ready_time"]):
                if train["idx"] < len(train["route"]):
                    current_node = train["route"][train["idx"]]
                    next_options = [current_node]
            
            if current_node and next_options:
                decision_trains.append((train, current_node, next_options))
        
        decision_trains.sort(key=lambda x: (-x[0]["priority"], -(self.t - x[0]["ready_time"])))
        return decision_trains

    def _compute_action_mask(self):
        mask = np.zeros(self.action_dim, dtype=bool)
        decision_trains = self._get_decision_trains()
        
        if not decision_trains:
            mask[11] = True
            return mask
        
        mask[0] = self._can_dispatch_highest_priority(decision_trains)
        mask[1] = self._can_dispatch_longest_waiting(decision_trains)
        mask[2] = self._can_dispatch_shortest_route(decision_trains)
        mask[3] = self._can_dispatch_by_efficiency(decision_trains)
        mask[4] = self._can_dispatch_emergency(decision_trains)
        mask[5] = self._can_dispatch_multiple_priority(decision_trains)
        mask[6] = True
        mask[7] = True
        mask[8] = self._can_dispatch_first_ready(decision_trains)
        mask[9] = self._can_dispatch_by_destination(decision_trains)
        mask[10] = self._can_adaptive_dispatch(decision_trains)
        mask[11] = True
        
        if not np.any(mask):
            mask[11] = True
            
        return mask

    def _can_dispatch_highest_priority(self, decision_trains):
        if not decision_trains:
            return False
        train, current_node, _ = decision_trains[0]
        return self._is_dispatch_legal(train, current_node)

    def _can_dispatch_longest_waiting(self, decision_trains):
        if not decision_trains:
            return False
        longest_wait = max(decision_trains, key=lambda x: self.t - x[0]["ready_time"])
        train, current_node, _ = longest_wait
        return self._is_dispatch_legal(train, current_node)

    def _can_dispatch_shortest_route(self, decision_trains):
        if not decision_trains:
            return False
        shortest = min(decision_trains, key=lambda x: len(x[0]["route"]) - max(0, x[0]["idx"]))
        train, current_node, _ = shortest
        return self._is_dispatch_legal(train, current_node)

    def _can_dispatch_by_efficiency(self, decision_trains):
        if not decision_trains:
            return False
        efficiencies = []
        for train, current_node, _ in decision_trains:
            remaining_blocks = len(train["route"]) - max(0, train["idx"])
            efficiency = train["priority"] / max(1, remaining_blocks)
            efficiencies.append((efficiency, train, current_node))
        
        efficiencies.sort(reverse=True)
        
        if efficiencies:
            _, train, current_node = efficiencies[0]
            return self._is_dispatch_legal(train, current_node)
        
        return False

    def _can_dispatch_emergency(self, decision_trains):
        if not decision_trains:
            return False
        for train, current_node, _ in decision_trains:
            wait_time = self.t - train["ready_time"]
            if wait_time > 600:
                return self._is_dispatch_legal(train, current_node)
        return False

    def _can_dispatch_multiple_priority(self, decision_trains):
        if len(decision_trains) < 2:
            return False
        high_priority_count = 0
        for train, current_node, _ in decision_trains:
            if train["priority"] >= 7 and self._is_dispatch_legal(train, current_node):
                high_priority_count += 1
                if high_priority_count >= 2:
                    return True
        return False

    def _can_dispatch_first_ready(self, decision_trains):
        if not decision_trains:
            return False
        earliest_ready = min(decision_trains, key=lambda x: x[0]["ready_time"])
        train, current_node, _ = earliest_ready
        return self._is_dispatch_legal(train, current_node)

    def _can_dispatch_by_destination(self, decision_trains):
        if not decision_trains:
            return False
        for train, current_node, _ in decision_trains:
            if self._is_dispatch_legal(train, current_node):
                return True
        return False

    def _can_adaptive_dispatch(self, decision_trains):
        if not decision_trains:
            return False
        congestion = sum(1 for occ in self.occ.values() if occ["tid"] is not None)
        congestion_ratio = congestion / len(self.blocks)
        
        if congestion_ratio > 0.7:
            for train, current_node, _ in decision_trains:
                remaining = len(train["route"]) - max(0, train["idx"])
                if remaining <= 2 and self._is_dispatch_legal(train, current_node):
                    return True
        else:
            return self._can_dispatch_highest_priority(decision_trains)
        
        return False

    def _is_dispatch_legal(self, train, block):
        if block not in self.blocks:
            return False
        
        block_free = self.occ[block]["free_at"] <= self.t
        not_reserved = self.occ[block]["reserved_by"] is None
        headway_ok = (self.t - self.last_exit[block]) >= self.headway_s
        
        return block_free and not_reserved and headway_ok

    def _calculate_travel_time(self, block_name):
        if block_name not in self.blocks:
            return 300
        
        length_km = self.blocks[block_name].get('length_km', 5)
        speed_kmph = self.speed_kmph.get(block_name, 80)
        
        travel_time_hours = length_km / max(speed_kmph, 1)
        return int(travel_time_hours * 3600)

    def _execute_action(self, action):
        decision_trains = self._get_decision_trains()
        reward = 0.0
        
        if not decision_trains:
            return -0.1
        
        trains_to_dispatch = []
        
        if action == 0:
            trains_to_dispatch = [decision_trains[0]]
        elif action == 1:
            longest_wait = max(decision_trains, key=lambda x: self.t - x[0]["ready_time"])
            trains_to_dispatch = [longest_wait]
        elif action == 2:
            shortest = min(decision_trains, key=lambda x: len(x[0]["route"]) - max(0, x[0]["idx"]))
            trains_to_dispatch = [shortest]
        elif action == 3:
            efficiencies = []
            for train_info in decision_trains:
                train, current_node, _ = train_info
                remaining = len(train["route"]) - max(0, train["idx"])
                wait_time = self.t - train["ready_time"]
                eff = (train["priority"] * (1 + wait_time / 300.0)) / max(1, remaining)
                efficiencies.append((eff, train_info))
            
            if efficiencies:
                efficiencies.sort(reverse=True)
                trains_to_dispatch = [efficiencies[0][1]]
        elif action == 4:
            emergency_trains = [info for info in decision_trains 
                              if (self.t - info[0]["ready_time"]) > 600]
            if emergency_trains:
                trains_to_dispatch = [emergency_trains[0]]
        elif action == 5:
            high_priority = [info for info in decision_trains[:3] 
                           if info[0]["priority"] >= 7]
            trains_to_dispatch = high_priority[:2]
        elif action == 6:
            return -0.02 * len(decision_trains)
        elif action == 7:
            return -0.05 * len(decision_trains)
        elif action == 8:
            earliest = min(decision_trains, key=lambda x: x[0]["ready_time"])
            trains_to_dispatch = [earliest]
        elif action == 9:
            trains_to_dispatch = [decision_trains[0]]
        elif action == 10:
            congestion = sum(1 for occ in self.occ.values() if occ["tid"] is not None)
            if congestion > len(self.blocks) * 0.7:
                shortest_remaining = min(decision_trains,
                                       key=lambda x: len(x[0]["route"]) - max(0, x[0]["idx"]))
                trains_to_dispatch = [shortest_remaining]
            else:
                trains_to_dispatch = [decision_trains[0]]
        elif action == 11:
            return -0.01
        
        dispatched_count = 0
        for train_info in trains_to_dispatch:
            train, block, _ = train_info
            if self._dispatch_train(train, block):
                dispatched_count += 1
                reward += 0.5 * train["priority"]
                
                if train["priority"] >= 8:
                    reward += 0.3
                
                delay = max(0, self.t - train["ready_time"])
                if delay > 300:
                    reward += 0.2
        
        completed_this_step = 0
        for train in self.trains:
            if not train["done"] and train["idx"] >= len(train["route"]):
                train["done"] = True
                train["actual_arrival"] = self.t
                completed_this_step += 1
                
                reward += 2.0
                
                if train["actual_arrival"] <= train["sched_arrival"]:
                    reward += 1.0
        
        delay_penalty = 0.005 * self._calculate_total_weighted_delay()
        
        return reward - delay_penalty

    def _dispatch_train(self, train, block):
        if not self._is_dispatch_legal(train, block):
            return False
        
        travel_time = self._calculate_travel_time(block)
        
        self.occ[block]["free_at"] = self.t + travel_time
        self.occ[block]["tid"] = train["tid"]
        self.last_exit[block] = self.t + travel_time
        
        if train["idx"] < 0:
            train["idx"] = 0
        else:
            train["idx"] += 1
            
        train["ready_time"] = self.t + travel_time
        train["last_decision_time"] = self.t
        
        return True

    def _calculate_total_weighted_delay(self):
        total_delay = 0.0
        for train in self.trains:
            if not train["done"]:
                delay = max(0, self.t - train["ready_time"]) / 60.0
                total_delay += delay * train["priority"]
        return total_delay

    def step(self, action: int):
        reward = self._execute_action(action)
        self.t += self.tick
        
        all_done = all(train["done"] for train in self.trains)
        timeout = self.t >= self.TMAX
        done = all_done or timeout
        
        if timeout and not all_done:
            incomplete_trains = sum(1 for train in self.trains if not train["done"])
            reward -= 3.0 * incomplete_trains
        
        next_state = self._create_graph_state()
        next_mask = self._compute_action_mask()
        
        info = {
            'trains_completed': sum(1 for train in self.trains if train["done"]),
            'total_trains': len(self.trains),
            'total_delay_min': self._calculate_total_weighted_delay(),
            'time_elapsed': self.t,
            'active_decisions': len(self._get_decision_trains())
        }
        
        return next_state, reward, done, info, next_mask

class ProperMaskedDQN(tf.keras.Model):
    def __init__(self, action_dim, d_node=12, d_global=8, hidden=64, gnn_hidden=32):
        super().__init__()
        
        self.action_dim = action_dim
        self.hidden = hidden
        self.gnn_hidden = gnn_hidden
        
        self.gnn1 = ManualGCNLayer(gnn_hidden)
        self.gnn2 = ManualGCNLayer(gnn_hidden)
        self.global_pool = ManualGlobalSumPool()
        
        self.built_manually = False

    def build(self, input_shape):
        if self.built_manually:
            return
            
        d_global = input_shape[2][-1]
        combined_dim = self.gnn_hidden + d_global
        
        self.fusion1_w = self.add_weight(
            shape=(combined_dim, self.hidden),
            initializer='glorot_uniform',
            name='fusion1_w'
        )
        self.fusion1_b = self.add_weight(
            shape=(self.hidden,),
            initializer='zeros',
            name='fusion1_b'
        )
        
        self.fusion2_w = self.add_weight(
            shape=(self.hidden, self.hidden),
            initializer='glorot_uniform',
            name='fusion2_w'
        )
        self.fusion2_b = self.add_weight(
            shape=(self.hidden,),
            initializer='zeros',
            name='fusion2_b'
        )
        
        self.value_w1 = self.add_weight(
            shape=(self.hidden, self.hidden//2),
            initializer='glorot_uniform',
            name='value_w1'
        )
        self.value_b1 = self.add_weight(
            shape=(self.hidden//2,),
            initializer='zeros',
            name='value_b1'
        )
        
        self.value_w2 = self.add_weight(
            shape=(self.hidden//2, 1),
            initializer='glorot_uniform',
            name='value_w2'
        )
        self.value_b2 = self.add_weight(
            shape=(1,),
            initializer='zeros',
            name='value_b2'
        )
        
        self.advantage_w1 = self.add_weight(
            shape=(self.hidden, self.hidden//2),
            initializer='glorot_uniform',
            name='advantage_w1'
        )
        self.advantage_b1 = self.add_weight(
            shape=(self.hidden//2,),
            initializer='zeros',
            name='advantage_b1'
        )
        
        self.advantage_w2 = self.add_weight(
            shape=(self.hidden//2, self.action_dim),
            initializer='glorot_uniform',
            name='advantage_w2'
        )
        self.advantage_b2 = self.add_weight(
            shape=(self.action_dim,),
            initializer='zeros',
            name='advantage_b2'
        )
        
        self.built_manually = True
        super().build(input_shape)

    def call(self, inputs, training=None):
        node_features, adjacency, global_features = inputs
        
        h1 = self.gnn1([node_features, adjacency])
        h2 = self.gnn2([h1, adjacency])
        
        graph_embedding = self.global_pool(h2)
        
        combined = tf.concat([graph_embedding, global_features], axis=-1)
        
        x = tf.matmul(combined, self.fusion1_w) + self.fusion1_b
        x = tf.nn.relu(x)
        x = tf.matmul(x, self.fusion2_w) + self.fusion2_b
        x = tf.nn.relu(x)
        
        v = tf.matmul(x, self.value_w1) + self.value_b1
        v = tf.nn.relu(v)
        v = tf.matmul(v, self.value_w2) + self.value_b2
        
        a = tf.matmul(x, self.advantage_w1) + self.advantage_b1
        a = tf.nn.relu(a)
        a = tf.matmul(a, self.advantage_w2) + self.advantage_b2
        
        a_mean = tf.reduce_mean(a, axis=1, keepdims=True)
        a_normalized = a - a_mean
        
        q_values = v + a_normalized
        
        return q_values

    def select_action(self, state, mask, epsilon=0.0):
        if np.random.random() < epsilon:
            valid_actions = np.where(mask)[0]
            if len(valid_actions) == 0:
                return self.action_dim - 1
            return np.random.choice(valid_actions)
        else:
            q_values = self(state).numpy()[0]
            masked_q_values = np.where(mask, q_values, -np.inf)
            
            if np.all(masked_q_values == -np.inf):
                return self.action_dim - 1
                
            return np.argmax(masked_q_values)

class PrioritizedReplayBuffer:
    def __init__(self, capacity=10000, alpha=0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer = []
        self.priorities = deque(maxlen=capacity)
        self.position = 0
        
    def add(self, state, action, reward, next_state, done, mask, next_mask):
        max_priority = max(self.priorities) if self.priorities else 1.0
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
            
        self.buffer[self.position] = (state, action, reward, next_state, done, mask, next_mask)
        self.priorities.append(max_priority)
        
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size, beta=0.4):
        if len(self.buffer) < batch_size:
            return None
            
        priorities = np.array(self.priorities)
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
        samples = [self.buffer[idx] for idx in indices]
        
        weights = (len(self.buffer) * probabilities[indices]) ** (-beta)
        weights /= weights.max()
        
        return samples, indices, weights
    
    def update_priorities(self, indices, priorities):
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority
    
    def __len__(self):
        return len(self.buffer)

def train_step(online_net, target_net, replay_buffer, optimizer, batch_size, gamma):
    batch_data = replay_buffer.sample(batch_size)
    if batch_data is None:
        return None
        
    batch, indices, weights = batch_data
    
    states, actions, rewards, next_states, dones, masks, next_masks = zip(*batch)
    
    batch_rewards = np.array(rewards, dtype=np.float32)
    batch_dones = np.array(dones, dtype=np.float32)
    batch_actions = np.array(actions, dtype=np.int32)
    weights = np.array(weights, dtype=np.float32)
    
    batch_states = (
        np.stack([s[0] for s in states]),
        np.stack([s[1] for s in states]),
        np.stack([s[2] for s in states])
    )
    
    batch_next_states = (
        np.stack([s[0] for s in next_states]),
        np.stack([s[1] for s in next_states]),
        np.stack([s[2] for s in next_states])
    )
    
    with tf.GradientTape() as tape:
        current_q = online_net(batch_states)
        
        next_q_online = online_net(batch_next_states)
        next_q_target = target_net(batch_next_states)
        
        masked_next_q_online = []
        masked_next_q_target = []
        
        for i, mask in enumerate(next_masks):
            masked_online = np.where(mask, next_q_online[i].numpy(), -np.inf)
            masked_target = np.where(mask, next_q_target[i].numpy(), -np.inf)
            masked_next_q_online.append(masked_online)
            masked_next_q_target.append(masked_target)
        
        masked_next_q_online = tf.constant(masked_next_q_online, dtype=tf.float32)
        masked_next_q_target = tf.constant(masked_next_q_target, dtype=tf.float32)
        
        next_actions = tf.argmax(masked_next_q_online, axis=1)
        next_q_values = tf.gather(masked_next_q_target, next_actions, axis=1, batch_dims=1)
        
        targets = batch_rewards + gamma * next_q_values * (1 - batch_dones)
        
        action_indices = tf.stack([tf.range(batch_size), batch_actions], axis=1)
        current_q_values = tf.gather_nd(current_q, action_indices)
        
        td_errors = targets - current_q_values
        
        loss = tf.reduce_mean(weights * tf.square(td_errors))
    
    gradients = tape.gradient(loss, online_net.trainable_variables)
    gradients = [tf.clip_by_norm(g, 1.0) for g in gradients]
    optimizer.apply_gradients(zip(gradients, online_net.trainable_variables))
    
    new_priorities = np.abs(td_errors.numpy()) + 1e-6
    replay_buffer.update_priorities(indices, new_priorities)
    
    return loss.numpy()

def train_proper_masked_dqn(network_data, scenarios, episodes=2000, batch_size=128, save_interval=100):
    env = ProperMaskedRailwayEnv(network_data)
    
    online_net = ProperMaskedDQN(env.action_dim)
    target_net = ProperMaskedDQN(env.action_dim)
    
    dummy_state = (
        np.zeros((1, env.N, env.d_node), dtype=np.float32),
        np.zeros((1, env.N, env.N), dtype=np.float32),
        np.zeros((1, env.d_global), dtype=np.float32)
    )
    
    _ = online_net(dummy_state)
    _ = target_net(dummy_state)
    target_net.set_weights(online_net.get_weights())
    
    optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3, clipnorm=1.0)
    replay_buffer = PrioritizedReplayBuffer(capacity=50000)
    
    epsilon_start = 0.9
    epsilon_end = 0.05
    epsilon_decay_episodes = episodes // 2
    
    gamma = 0.99
    target_update_freq = 25
    
    episode_rewards = []
    episode_delays = []
    episode_completions = []
    losses = []
    epsilon_history = []
    
    best_reward = -float('inf')
    no_improvement_count = 0
    early_stopping_patience = 200
    
    print(f"Starting Enhanced Masked GNN-DQN Training")
    print(f"Episodes: {episodes}, Batch Size: {batch_size}")
    print("=" * 60)
    
    for episode in range(episodes):
        if episode < epsilon_decay_episodes:
            epsilon = epsilon_start - (epsilon_start - epsilon_end) * (episode / epsilon_decay_episodes)
        else:
            epsilon = epsilon_end
        
        epsilon_history.append(epsilon)
        
        scenario = scenarios[episode % len(scenarios)]
        state, mask = env.reset(scenario)
        
        episode_reward = 0.0
        episode_losses = []
        step_count = 0
        
        while step_count < 150:
            formatted_state = (
                state[0][np.newaxis, ...],
                state[1][np.newaxis, ...],
                state[2][np.newaxis, ...]
            )
            
            action = online_net.select_action(formatted_state, mask, epsilon)
            
            next_state, reward, done, info, next_mask = env.step(action)
            
            replay_buffer.add(state, action, reward, next_state, done, mask, next_mask)
            
            episode_reward += reward
            
            if len(replay_buffer) >= batch_size and step_count % 2 == 0:
                loss = train_step(online_net, target_net, replay_buffer, 
                                optimizer, batch_size, gamma)
                if loss is not None:
                    episode_losses.append(loss)
            
            state = next_state
            mask = next_mask
            step_count += 1
            
            if done:
                break
        
        if episode % target_update_freq == 0:
            target_net.set_weights(online_net.get_weights())
        
        episode_rewards.append(episode_reward)
        episode_delays.append(info['total_delay_min'])
        completion_rate = info['trains_completed'] / info['total_trains']
        episode_completions.append(completion_rate)
        
        if episode_losses:
            losses.append(np.mean(episode_losses))
        
        if episode_reward > best_reward:
            best_reward = episode_reward
            no_improvement_count = 0
        else:
            no_improvement_count += 1
        
        if episode % 20 == 0:
            recent_rewards = episode_rewards[-20:] if len(episode_rewards) >= 20 else episode_rewards
            recent_delays = episode_delays[-20:] if len(episode_delays) >= 20 else episode_delays
            recent_completions = episode_completions[-20:] if len(episode_completions) >= 20 else episode_completions
            recent_losses = losses[-20:] if len(losses) >= 20 else losses
            
            print(f"Episode {episode:4d}: "
                  f"Reward={np.mean(recent_rewards):7.2f}, "
                  f"Delay={np.mean(recent_delays):6.2f}min, "
                  f"Completion={np.mean(recent_completions):4.2f}, "
                  f"Loss={np.mean(recent_losses):6.4f}, "
                  f"ε={epsilon:.3f}, "
                  f"Buffer={len(replay_buffer)}")
        
        if episode > 0 and episode % save_interval == 0:
            try:
                base_path, _ = setup_colab_environment()
                checkpoint_path = f"{base_path}/models/checkpoint_episode_{episode}.weights.h5"
                online_net.save_weights(checkpoint_path)
                
                checkpoint_data = {
                    'episode': episode,
                    'episode_rewards': episode_rewards,
                    'episode_delays': episode_delays,
                    'episode_completions': episode_completions,
                    'losses': losses,
                    'epsilon_history': epsilon_history,
                    'best_reward': best_reward
                }
                
                checkpoint_json_path = f"{base_path}/results/checkpoint_episode_{episode}.json"
                with open(checkpoint_json_path, 'w') as f:
                    json.dump(checkpoint_data, f, indent=2)
                
                print(f"    Checkpoint saved at episode {episode}")
                
            except Exception as e:
                print(f"    Warning: Could not save checkpoint: {e}")
        
        if no_improvement_count >= early_stopping_patience and episode > 500:
            print(f"\nEarly stopping at episode {episode}")
            break
    
    print(f"\nTraining Complete!")
    print(f"Final average reward (last 50): {np.mean(episode_rewards[-50:]):.2f}")
    print(f"Final average delay (last 50): {np.mean(episode_delays[-50:]):.2f} min")
    print(f"Final completion rate (last 50): {np.mean(episode_completions[-50:]):.2f}")
    print(f"Best reward achieved: {best_reward:.2f}")
    
    return online_net, {
        'rewards': episode_rewards,
        'delays': episode_delays,
        'completions': episode_completions,
        'losses': losses,
        'epsilon_history': epsilon_history,
        'best_reward': best_reward,
        'episodes_trained': len(episode_rewards)
    }

def evaluate_masked_model(network_data, scenarios, model, num_episodes=50):
    env = ProperMaskedRailwayEnv(network_data)
    
    results = {
        'rewards': [],
        'delays': [],
        'completions': [],
        'episode_info': []
    }
    
    print("\nEvaluating Trained Model")
    print("=" * 30)
    
    for episode in range(num_episodes):
        scenario = scenarios[episode % len(scenarios)]
        state, mask = env.reset(scenario)
        
        episode_reward = 0.0
        step_count = 0
        
        while step_count < 100:
            formatted_state = (
                state[0][np.newaxis, ...],
                state[1][np.newaxis, ...],
                state[2][np.newaxis, ...]
            )
            
            action = model.select_action(formatted_state, mask, epsilon=0.0)
            
            next_state, reward, done, info, next_mask = env.step(action)
            
            episode_reward += reward
            state = next_state
            mask = next_mask
            step_count += 1
            
            if done:
                break
        
        results['rewards'].append(episode_reward)
        results['delays'].append(info['total_delay_min'])
        completion_rate = info['trains_completed'] / info['total_trains']
        results['completions'].append(completion_rate)
        results['episode_info'].append(info)
        
        if episode % 10 == 0:
            print(f"Episode {episode:2d}: "
                  f"Reward={episode_reward:6.2f}, "
                  f"Delay={info['total_delay_min']:6.2f}min, "
                  f"Completion={completion_rate:4.2f}")
    
    print(f"\nEvaluation Summary:")
    print(f"Average Reward: {np.mean(results['rewards']):.2f} ± {np.std(results['rewards']):.2f}")
    print(f"Average Delay: {np.mean(results['delays']):.2f} ± {np.std(results['delays']):.2f} min")
    print(f"Average Completion: {np.mean(results['completions']):.2f} ± {np.std(results['completions']):.2f}")
    
    return results

def plot_training_results(results):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    axes[0, 0].plot(results['rewards'])
    axes[0, 0].set_title('Episode Rewards')
    axes[0, 0].set_xlabel('Episode')
    axes[0, 0].set_ylabel('Total Reward')
    axes[0, 0].grid(True)
    
    axes[0, 1].plot(results['delays'])
    axes[0, 1].set_title('Total Delay per Episode')
    axes[0, 1].set_xlabel('Episode')
    axes[0, 1].set_ylabel('Delay (minutes)')
    axes[0, 1].grid(True)
    
    axes[1, 0].plot(results['completions'])
    axes[1, 0].set_title('Train Completion Rate')
    axes[1, 0].set_xlabel('Episode')
    axes[1, 0].set_ylabel('Completion Rate')
    axes[1, 0].grid(True)
    
    if results['losses']:
        axes[1, 1].plot(results['losses'])
        axes[1, 1].set_title('Training Loss')
        axes[1, 1].set_xlabel('Training Step')
        axes[1, 1].set_ylabel('Loss')
        axes[1, 1].grid(True)
    
    plt.tight_layout()
    plt.show()

def main_colab_training():
    print("Mumbai Railway GNN-DQN Training System")
    print("=" * 50)
    
    base_path, in_colab = setup_colab_environment()
    
    print("\nLoading Mumbai railway data from files...")
    try:
        scenarios, graph_data = load_scenario_files_from_upload()
        
    except Exception as e:
        print(f"Error loading files: {e}")
        raise ValueError("Could not load required files. Please check your files and try again.")
    
    print("\nBuilding network topology...")
    if graph_data is not None:
        network_data = create_network_from_graph_data(graph_data)
        if network_data is None:
            print("Failed to create network from graph data. Creating from scenarios...")
            network_data = create_mumbai_network_from_scenarios(scenarios)
    else:
        print("Creating network topology from scenario data...")
        network_data = create_mumbai_network_from_scenarios(scenarios)
    
    print(f"\nNetwork Statistics:")
    print(f"   • Stations: {len(network_data['stations'])}")
    print(f"   • Blocks: {len(network_data['blocks'])}")
    print(f"   • Total Nodes: {network_data['N']}")
    print(f"   • Scenarios: {len(scenarios)}")
    print(f"   • Total Trains: {sum(len(scenario) for scenario in scenarios)}")
    
    training_config = {
        'episodes': 2000 if in_colab else 200,
        'batch_size': 128 if in_colab else 64,
        'buffer_size': 50000 if in_colab else 15000,
        'target_update_freq': 25 if in_colab else 15,
        'save_interval': 100,
        'eval_interval': 50,
        'early_stopping_patience': 200
    }
    
    print(f"\nTraining Configuration:")
    for key, value in training_config.items():
        print(f"   • {key}: {value}")
    
    print(f"\nStarting training...")
    trained_model, training_results = train_proper_masked_dqn(
        network_data, scenarios, 
        episodes=training_config['episodes'],
        batch_size=training_config['batch_size'],
        save_interval=training_config['save_interval']
    )
    
    print(f"\nPlotting results...")
    plot_training_results(training_results)
    
    model_path = f"{base_path}/models/mumbai_masked_gnn_dqn_final.weights.h5"
    trained_model.save_weights(model_path)
    print(f"Model saved: {model_path}")
    
    results_path = f"{base_path}/results/training_results_final.json"
    with open(results_path, 'w') as f:
        json.dump({
            'episode_rewards': training_results['rewards'],
            'episode_delays': training_results['delays'], 
            'episode_completions': training_results['completions'],
            'config': training_config,
            'network_stats': {
                'stations': len(network_data['stations']),
                'blocks': len(network_data['blocks']),
                'total_nodes': network_data['N']
            },
            'episodes_trained': training_results['episodes_trained'],
            'best_reward': training_results['best_reward']
        }, f, indent=2)
    print(f"Results saved: {results_path}")
    
    print(f"\nEvaluating trained model...")
    eval_results = evaluate_masked_model(
        network_data, scenarios, trained_model, num_episodes=30
    )
    
    print(f"\nTraining Complete!")
    print(f"   • Episodes Trained: {training_results['episodes_trained']}")
    print(f"   • Final Avg Reward: {np.mean(training_results['rewards'][-50:]):.2f}")
    print(f"   • Final Avg Delay: {np.mean(training_results['delays'][-50:]):.2f} min")
    print(f"   • Final Completion Rate: {np.mean(training_results['completions'][-50:]):.2f}")
    print(f"   • Best Reward Achieved: {training_results['best_reward']:.2f}")
    print(f"   • Evaluation Avg Reward: {np.mean(eval_results['rewards']):.2f}")
    
    return trained_model, training_results, eval_results, network_data

if __name__ == "__main__":
    tf.random.set_seed(42)
    np.random.seed(42)
    random.seed(42)
    
    model, train_results, eval_results, network = main_colab_training()