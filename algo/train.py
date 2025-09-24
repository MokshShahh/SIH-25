import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from spektral.layers import GINConv, GlobalSumPool
from dataclasses import dataclass, field
from typing import List, Tuple, Dict

# 1) Railway Infrastructure (unchanged)
@dataclass
class Block:
    name: str
    length_km: float
    single_track: bool = True

@dataclass
class Station:
    name: str
    platforms: int

@dataclass
class Train:
    tid: str
    origin: str
    dest: str
    route_blocks: List[str]            
    sched_departure_s: int
    sched_arrival_s: int
    priority: int                      
    dwell_rules: Dict[str, int] = field(default_factory=dict)  

def build_micro_corridor():
    stations = {
        "A": Station("A", platforms=2),
        "B": Station("B", platforms=2),  
        "C": Station("C", platforms=2),
    }
    blocks = {
        "A-B": Block("A-B", length_km=3.0, single_track=True),
        "B-C": Block("B-C", length_km=4.0, single_track=True),
    }
    speed_kmph = {"A-B": 70.0, "B-C": 60.0}
    headway_s = 180  
    return stations, blocks, speed_kmph, headway_s

def make_scenarios():
    base = [
        Train("E101", "A", "C", ["A-B","B-C"],  0,  35*60, priority=3, dwell_rules={"B":60}),
        Train("L205", "C", "A", ["B-C","A-B"][::-1],  2*60, 38*60, priority=2, dwell_rules={"B":90}),
        Train("F310", "A", "C", ["A-B","B-C"],  6*60, 42*60, priority=1, dwell_rules={"B":60}),
        Train("E111", "C", "A", ["B-C","A-B"][::-1], 10*60, 45*60, priority=3, dwell_rules={"B":60}),
        Train("L207", "A", "C", ["A-B","B-C"], 12*60, 44*60, priority=2, dwell_rules={"B":60}),
        Train("F318", "C", "A", ["B-C","A-B"][::-1], 14*60, 46*60, priority=1, dwell_rules={"B":60}),
    ]
    scenarios = []
    rng = np.random.default_rng(7)
    for k in range(10):
        trains = []
        for t in base:
            jitter = int(rng.integers(-60, 120))
            trains.append(Train(
                tid=f"{t.tid}_{k}",
                origin=t.origin, dest=t.dest,
                route_blocks=list(t.route_blocks),
                sched_departure_s=max(0, t.sched_departure_s + jitter),
                sched_arrival_s=t.sched_arrival_s + jitter,
                priority=t.priority,
                dwell_rules=dict(t.dwell_rules),
            ))
        scenarios.append(trains)
    return scenarios

# 2) GNN-Enhanced Environment
class RailEnvGNN:
    """
    Railway environment that represents the network as a graph.
    Nodes: stations + track sections
    Edges: physical connections between railway elements
    """
    def __init__(self, stations, blocks, speed_kmph, headway_s, tick_sec=10):
        self.stations = stations
        self.blocks = blocks
        self.speed_kmph = speed_kmph
        self.headway_s = headway_s
        self.tick = tick_sec
        self.K = 2  # max candidate trains
        self.action_dim = 4  # 2 trains * (proceed/hold)
        self.rng = np.random.default_rng(123)
        
        # Build graph structure
        self._build_graph_structure()
        
        # Graph dimensions
        self.N = len(self.node_names)  # number of nodes
        self.d_node = 8  # node feature dimension
        self.d_global = 6  # global feature dimension

    def _build_graph_structure(self):
        """Create graph representation of railway network"""
        # Nodes: stations + blocks (track sections)
        self.node_names = list(self.stations.keys()) + list(self.blocks.keys())
        self.node_to_idx = {name: i for i, name in enumerate(self.node_names)}
        self.N = len(self.node_names)
        
        # Build adjacency matrix
        self.adj_matrix = np.zeros((self.N, self.N), dtype=np.float32)
        
        # Connect stations to adjacent blocks
        for block_name, block in self.blocks.items():
            if "-" in block_name:
                station1, station2 = block_name.split("-")
                if station1 in self.node_to_idx and station2 in self.node_to_idx:
                    block_idx = self.node_to_idx[block_name]
                    s1_idx = self.node_to_idx[station1]
                    s2_idx = self.node_to_idx[station2]
                    
                    # Bidirectional connections
                    self.adj_matrix[s1_idx, block_idx] = 1.0
                    self.adj_matrix[block_idx, s1_idx] = 1.0
                    self.adj_matrix[s2_idx, block_idx] = 1.0
                    self.adj_matrix[block_idx, s2_idx] = 1.0

    def reset(self, trains: List[Train]):
        # Initialize simulation state (same as before)
        self.t = 0
        self.TMAX = 50*60  
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
            })
        
        self.occ = {b: {"free_at": 0, "tid": None} for b in self.blocks}
        self.last_exit = {b: -10**9 for b in self.blocks}
        self._last_reward = 0.0
        return self._obs_graph(), self._mask()

    def _obs_graph(self):
        """Return graph-structured observation: (node_features, adjacency, global_features)"""
        # Node features [N, d_node]
        node_feats = np.zeros((self.N, self.d_node), dtype=np.float32)
        
        for i, node_name in enumerate(self.node_names):
            if node_name in self.stations:
                # Station node features
                station = self.stations[node_name]
                node_feats[i, 0] = 1.0  # is_station
                node_feats[i, 1] = station.platforms / 5.0  # normalized platforms
                
                # Count trains at/near this station
                trains_here = sum(1 for tr in self.trains 
                                if not tr["done"] and node_name in tr["route"])
                node_feats[i, 2] = trains_here / max(1, len(self.trains))
                
            elif node_name in self.blocks:
                # Block/track node features
                block = self.blocks[node_name]
                node_feats[i, 0] = 0.0  # not a station
                node_feats[i, 1] = block.length_km / 10.0  # normalized length
                
                # Occupancy
                occupied = 1.0 if self.occ[node_name]["free_at"] > self.t else 0.0
                node_feats[i, 2] = occupied
                
                # Time until free
                free_in = max(0, self.occ[node_name]["free_at"] - self.t) / 300.0
                node_feats[i, 3] = min(free_in, 2.0)  # clamp at 10min
                
                # Speed limit
                node_feats[i, 4] = self.speed_kmph.get(node_name, 50.0) / 100.0
                
                # Headway constraint
                time_since_exit = (self.t - self.last_exit[node_name]) / 300.0
                node_feats[i, 5] = min(time_since_exit, 2.0)
        
        # Get candidate trains for priority encoding
        cands = self._candidates()
        for j, (tr, blk) in enumerate(cands[:2]):  # only first 2 candidates
            if blk in self.node_to_idx:
                blk_idx = self.node_to_idx[blk]
                node_feats[blk_idx, 6] = tr["priority"] / 3.0  # normalized priority
                node_feats[blk_idx, 7] = min((self.t - tr["ready_time"]) / 300.0, 2.0)  # lateness
        
        # Global features [d_global]
        finished = sum(1 for tr in self.trains if tr["done"]) / max(1, len(self.trains))
        time_norm = self.t / 3600.0
        sum_delay = self._sum_delay_min() / 30.0
        max_delay = self._max_delay_min() / 30.0
        congestion = len(cands) / self.K
        avg_priority = np.mean([tr["priority"] for tr in self.trains if not tr["done"]], initial=2.0) / 3.0
        
        global_feats = np.array([finished, time_norm, sum_delay, max_delay, congestion, avg_priority], 
                               dtype=np.float32)
        
        return node_feats, self.adj_matrix, global_feats

    # Keep all the helper methods from original RailEnv
    def _block_speed_s(self, block_name):
        km = self.blocks[block_name].length_km
        v = self.speed_kmph[block_name]
        return int((km / max(1e-6, v)) * 3600)

    def _candidates(self):
        cands = []
        for tr in self.trains:
            if tr["done"]: continue
            if tr["idx"] < 0:
                if self.t >= tr["ready_time"]:
                    next_blk = tr["route"][0]
                    cands.append((tr, next_blk))
            else:
                if tr["idx"] >= len(tr["route"]):
                    continue
                next_blk = tr["route"][tr["idx"]]
                cands.append((tr, next_blk))
        
        def lateness(tr):
            est = max(self.t, tr["ready_time"])
            return est - tr["ready_time"]
        cands.sort(key=lambda x: (-x[0]["priority"], -lateness(x[0])))
        return cands[:self.K]

    def _legal(self, tr, blk):
        free = (self.occ[blk]["free_at"] <= self.t)
        sep_ok = (self.t - self.last_exit[blk] >= self.headway_s)
        return free and sep_ok

    def _apply_action(self, a, cands):
        reward_delta = 0.0
        progressed = 0
        for i in range(len(cands)):
            tr, blk = cands[i]
            proceed = (a == 2*i)
            if proceed:
                if self._legal(tr, blk):
                    travel = self._block_speed_s(blk)
                    self.occ[blk]["free_at"] = self.t + travel
                    self.occ[blk]["tid"] = tr["tid"]
                    self.last_exit[blk] = self.t + travel
                    tr["idx"] += 1 if tr["idx"] >= 0 else 1
                    tr["ready_time"] = self.t + travel
                    progressed += 1
                else:
                    reward_delta -= 0.5
            else:
                reward_delta -= 0.01 * tr["priority"]
        
        # Mark finished trains
        finished_now = 0
        for tr in self.trains:
            if (not tr["done"]) and tr["idx"] >= len(tr["route"]):
                tr["done"] = True
                tr["actual_arrival"] = max(self.t, tr["ready_time"])
                finished_now += 1
        
        # Reward calculation
        reward = (1.0 * finished_now - 0.05 * self._sum_delay_min() 
                 - 0.02 * self._max_delay_min() - 0.03 * self._priority_delay()
                 + reward_delta + 0.05 * progressed)
        return reward

    def _sum_delay_min(self):
        s = 0.0
        for tr in self.trains:
            if tr["actual_arrival"] is not None:
                s += max(0, tr["actual_arrival"] - tr["sched_arrival"]) / 60.0
            else:
                s += max(0, self.t - tr["ready_time"]) / 60.0
        return s

    def _max_delay_min(self):
        m = 0.0
        for tr in self.trains:
            if tr["actual_arrival"] is not None:
                m = max(m, max(0, tr["actual_arrival"] - tr["sched_arrival"]) / 60.0)
            else:
                m = max(m, max(0, self.t - tr["ready_time"]) / 60.0)
        return m

    def _priority_delay(self):
        pd = 0.0
        for tr in self.trains:
            lat = (max(0, self.t - tr["ready_time"])) / 60.0
            pd += lat * (4 - tr["priority"]) * 0.2
        return pd

    def _mask(self):
        mask = np.zeros(self.action_dim, dtype=bool)
        cands = self._candidates()
        for i in range(self.K):
            if i < len(cands):
                tr, blk = cands[i]
                mask[2*i]   = self._legal(tr, blk)  # proceed
                mask[2*i+1] = True                  # hold
        return mask

    def step(self, a: int):
        cands = self._candidates()
        reward = self._apply_action(a, cands)
        self.t += self.tick
        done = all(tr["done"] for tr in self.trains) or self.t >= self.TMAX
        if self.t >= self.TMAX and not all(tr["done"] for tr in self.trains):
            reward -= 5.0
        return self._obs_graph(), reward, done, {}, self._mask()

# 3) GNN-Enhanced Dueling DQN
class DuelingGNNDQN(tf.keras.Model):
    def __init__(self, action_dim, hidden=64, glob_hidden=128):
        super().__init__()
        # GNN backbone
        self.gnn1 = GINConv(mlp=tf.keras.Sequential([
            layers.Dense(hidden, activation="relu"),
            layers.Dense(hidden, activation="relu")
        ]))
        self.gnn2 = GINConv(mlp=tf.keras.Sequential([
            layers.Dense(hidden, activation="relu"),
            layers.Dense(hidden, activation="relu")
        ]))
        self.pool = GlobalSumPool()
        
        # Fusion with global scalars
        self.fuse = tf.keras.Sequential([
            layers.LayerNormalization(),
            layers.Dense(glob_hidden, activation="relu"),
            layers.Dense(glob_hidden, activation="relu"),
        ])
        
        # Dueling streams
        self.V = tf.keras.Sequential([
            layers.Dense(128, activation="relu"),
            layers.Dense(1)
        ])
        self.A = tf.keras.Sequential([
            layers.Dense(128, activation="relu"),
            layers.Dense(action_dim)
        ])

    def call(self, inputs, training=False):
        x, a, u = inputs   # x:[B,N,d], a:[B,N,N], u:[B,dg]
        
        # GNN processing
        h = self.gnn1([x, a])
        h = self.gnn2([h, a])
        g = self.pool(h)          # [B, hidden] - global graph representation
        
        # Fuse graph embedding with global features
        z = tf.concat([g, u], axis=-1)
        z = self.fuse(z)
        
        # Dueling streams
        v = self.V(z)             # [B,1] - state value
        a_stream = self.A(z)      # [B,A] - action advantages
        a_stream = a_stream - tf.reduce_mean(a_stream, axis=1, keepdims=True)
        q = v + a_stream          # [B,A] - Q-values
        return q

# 4) Graph-Based Replay Buffer
class ReplayGNN:
    def __init__(self, cap, N, d_node, d_global, action_dim):
        self.cap = cap
        self.ptr = 0
        self.sz = 0
        
        # Graph states
        self.x = np.zeros((cap, N, d_node), np.float32)
        self.a = np.zeros((cap, N, N), np.float32)
        self.u = np.zeros((cap, d_global), np.float32)
        
        # Transitions
        self.act = np.zeros((cap,), np.int32)
        self.r = np.zeros((cap,), np.float32)
        
        # Next graph states
        self.x2 = np.zeros((cap, N, d_node), np.float32)
        self.a2 = np.zeros((cap, N, N), np.float32)
        self.u2 = np.zeros((cap, d_global), np.float32)
        
        self.done = np.zeros((cap,), np.float32)
        self.mask2 = np.zeros((cap, action_dim), np.bool_)

    def add(self, s, a, r, s2, done, mask2):
        x, A, u = s
        x2, A2, u2 = s2
        i = self.ptr
        
        self.x[i] = x
        self.a[i] = A
        self.u[i] = u
        self.act[i] = a
        self.r[i] = r
        self.x2[i] = x2
        self.a2[i] = A2
        self.u2[i] = u2
        self.done[i] = done
        self.mask2[i] = mask2
        
        self.ptr = (self.ptr + 1) % self.cap
        self.sz = min(self.sz + 1, self.cap)

    def sample(self, B):
        idx = np.random.randint(0, self.sz, size=B)
        return (self.x[idx], self.a[idx], self.u[idx], self.act[idx],
                self.r[idx], self.x2[idx], self.a2[idx], self.u2[idx],
                self.done[idx], self.mask2[idx])

# 5) Training Loop with GNN
def train_gnn(seed=0):
    stations, blocks, speed, headway = build_micro_corridor()
    scenarios = make_scenarios()
    env = RailEnvGNN(stations, blocks, speed, headway, tick_sec=10)

    action_dim = env.action_dim
    online = DuelingGNNDQN(action_dim)
    target = DuelingGNNDQN(action_dim)
    
    # Initialize networks with dummy data
    dummy_x = np.zeros((1, env.N, env.d_node), np.float32)
    dummy_a = np.zeros((1, env.N, env.N), np.float32) 
    dummy_u = np.zeros((1, env.d_global), np.float32)
    _ = online((dummy_x, dummy_a, dummy_u))
    _ = target((dummy_x, dummy_a, dummy_u))
    target.set_weights(online.get_weights())

    opt = tf.keras.optimizers.Adam(3e-4)
    gamma = 0.99
    batch = 64  # Smaller batch for GNN
    target_update = 1000
    buffer = ReplayGNN(cap=50_000, N=env.N, d_node=env.d_node, 
                      d_global=env.d_global, action_dim=action_dim)

    eps_start, eps_end, eps_decay_steps = 0.2, 0.02, 50_000
    global_step = 0
    rng = np.random.default_rng(seed)

    def select_action(s, mask, eps):
        x, a, u = s
        if (rng.random() < eps) or (not mask.any()):
            valid_idx = np.where(mask)[0]
            return int(rng.choice(valid_idx))
        
        q = online((x[None,...], a[None,...], u[None,...])).numpy()[0]
        q[~mask] = -1e9
        return int(np.argmax(q))

    steps_limit = 200_000  # Reduced for GNN complexity
    log_every = 2000
    eval_every = 20_000
    ep_returns = []
    best_eval = -1e9

    print("Starting GNN-DQN training...")
    while global_step < steps_limit:
        trains = scenarios[rng.integers(len(scenarios))]
        s, mask = env.reset(trains)
        done = False
        ep_ret, ep_len = 0.0, 0
        
        while not done:
            eps = max(eps_end, eps_start - (eps_start-eps_end)*min(1.0, global_step/eps_decay_steps))
            a = select_action(s, mask, eps)
            s2, r, done, _, mask2 = env.step(a)
            buffer.add(s, a, r, s2, float(done), mask2)
            s = s2
            mask = mask2
            ep_ret += r
            ep_len += 1
            global_step += 1

            # Learning update
            if buffer.sz >= 2000 and global_step % 4 == 0:
                bx, ba, bu, b_act, b_r, bx2, ba2, bu2, b_done, b_mask2 = buffer.sample(batch)
                
                with tf.GradientTape() as tape:
                    q = online((bx, ba, bu))                        # [B,A]
                    qa = tf.gather(q, b_act[:,None], batch_dims=1)[:,0]
                    
                    # Double DQN target with masking
                    q_next_online = online((bx2, ba2, bu2)).numpy()
                    q_next_online[~b_mask2] = -1e9
                    a_star = np.argmax(q_next_online, axis=1)
                    
                    q_next_target = target((bx2, ba2, bu2))
                    qn = tf.gather(q_next_target, a_star[:,None], batch_dims=1)[:,0]
                    
                    y = b_r + (1.0 - b_done) * gamma * qn
                    loss = tf.keras.losses.Huber()(y, qa)
                
                grads = tape.gradient(loss, online.trainable_variables)
                tf.clip_by_global_norm(grads, 1.0)
                opt.apply_gradients(zip(grads, online.trainable_variables))

            # Target network update
            if global_step % target_update == 0:
                target.set_weights(online.get_weights())

            if global_step % log_every == 0:
                print(f"step={global_step:7d}  eps={eps:.3f}  loss={float(loss):.4f}  ep_ret={ep_ret:.2f}")

            if global_step % eval_every == 0:
                eval_ret = evaluate_gnn(env, online, scenarios[:3])
                print(f"[EVAL] step={global_step}  return={eval_ret:.2f}")
                if eval_ret > best_eval:
                    best_eval = eval_ret
                    online.save_weights("best_rail_gnn_dqn_tf.h5")

            if global_step >= steps_limit:
                break

        ep_returns.append(ep_ret)

    print("GNN-DQN Training complete. Best eval return:", best_eval)

def evaluate_gnn(env, policy, scenario_subset):
    rng = np.random.default_rng(999)
    total = 0.0
    for _ in range(6):
        trains = scenario_subset[rng.integers(len(scenario_subset))]
        s, mask = env.reset(trains)
        done = False
        ep_ret = 0.0
        while not done:
            x, a, u = s
            q = policy((x[None,...], a[None,...], u[None,...])).numpy()[0]
            q[~mask] = -1e9
            action = int(np.argmax(q))
            s, r, done, _, mask = env.step(action)
            ep_ret += r
        total += ep_ret
    return total / 6.0

if __name__ == "__main__":
    tf.random.set_seed(0)
    np.random.seed(0)
    train_gnn()