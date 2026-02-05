import os
import sys
import numpy as np
import uuid
import sumolib
import traci
from gymnasium import spaces
import pettingzoo

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("SUMO_HOME'u ayarlayın")

class raw_env(pettingzoo.ParallelEnv):
    metadata = {"name": "multi_agent_traffic_hybrid_v4"}

    def __init__(self, sumo_cfg_path, use_gui=False, max_steps=1000, label="default"):
        super().__init__()
        self.sumo_cfg = sumo_cfg_path
        self.use_gui = use_gui
        self.max_steps = max_steps
        self.current_step = 0
        self.connection_label = f"env_{uuid.uuid4().hex[:8]}" if label == "default" else label
        
        # İlk bağlantıyı kur ve temel bilgileri al
        self._start_sumo()
        
        # Libsumo desteği için kontrol
        try:
            self.conn = traci.getConnection(self.connection_label)
        except AttributeError:
            # Libsumo modulu kullaniyorsak direkt traci'yi kullan
            self.conn = traci
        
        # --- AJANLAR ---
        self.tls_agents = list(self.conn.trafficlight.getIDList())
        self.agents = self.tls_agents
        
        # --- HIZ TABELALARI (VSL) ---
        net_path = sumo_cfg_path.replace(".sumocfg", ".net.xml")
        net = sumolib.net.readNet(net_path)
        self.vsl_zones = {}
        
        all_tls_ids = set(self.conn.trafficlight.getIDList())
        for node in net.getNodes():
            n_id = node.getID()
            if n_id not in all_tls_ids and len(node.getIncoming()) >= 2:
                lanes = []
                for edge in node.getIncoming():
                    e_id = edge.getID()
                    for i in range(self.conn.edge.getLaneNumber(e_id)):
                        l_id = f"{e_id}_{i}"
                        target_tls = None
                        for tls in self.tls_agents:
                            if e_id in self.conn.trafficlight.getControlledLanes(tls):
                                target_tls = tls
                                break
                        lanes.append({"id": l_id, "orig_speed": self.conn.lane.getMaxSpeed(l_id), "target_tls": target_tls})
                self.vsl_zones[n_id] = lanes

        self.junction_incoming_lanes = {a: set(self.conn.trafficlight.getControlledLanes(a)) for a in self.tls_agents}
        
        # Komşu Takibi
        self.neighbors = {}
        for agent in self.agents:
            pos = self.conn.junction.getPosition(agent)
            distances = []
            for other in self.agents:
                if agent != other:
                    other_pos = self.conn.junction.getPosition(other)
                    dist = np.sqrt((pos[0]-other_pos[0])**2 + (pos[1]-other_pos[1])**2)
                    distances.append((other, dist))
            distances.sort(key=lambda x: x[1])
            self.neighbors[agent] = [d[0] for d in distances[:2]]
        
        # Uzaylar
        self.action_spaces = {a: spaces.Discrete(len(self.conn.trafficlight.getCompleteRedYellowGreenDefinition(a)[0].phases)) for a in self.agents}
        self.observation_space_shared = spaces.Box(low=0, high=10000, shape=(5,), dtype=np.float32)

        self.yellow_time = 3
        self.yellow_timers = {agent: 0 for agent in self.tls_agents}
        self.pending_phases = {agent: None for agent in self.tls_agents}
        self.current_phases = {agent: self.conn.trafficlight.getPhase(agent) for agent in self.tls_agents}

    def observation_space(self, agent: str): return self.observation_space_shared
    def action_space(self, agent: str): return self.action_spaces[agent]
        
    def _start_sumo(self):
        sumo_binary = sumolib.checkBinary("sumo-gui" if self.use_gui else "sumo")
        # Kaggle hizi icin kritik optimizasyonlar
        sumo_cmd = [
            sumo_binary, "-c", self.sumo_cfg, 
            "--no-warnings", "--no-step-log",
            "--ignore-route-errors", "true",
            "--waiting-time-memory", "1000",
            "--time-to-teleport", "300" # Takilan araclar simülasyonu kilitlemesin
        ]
        if self.use_gui: sumo_cmd.extend(["--start", "--quit-on-end"])
        traci.start(sumo_cmd, label=self.connection_label)

    def _get_obs(self):
        obs_dict = {}
        for agent in self.agents:
            lanes = self.junction_incoming_lanes[agent]
            v = sum(self.conn.lane.getLastStepVehicleNumber(l) for l in lanes)
            w = sum(self.conn.lane.getWaitingTime(l) for l in lanes)
            h = sum(self.conn.lane.getLastStepHaltingNumber(l) for l in lanes)
            n_v = [sum(self.conn.lane.getLastStepVehicleNumber(l) for l in self.junction_incoming_lanes[n]) for n in self.neighbors[agent]]
            obs_dict[agent] = np.array([v, w, h] + n_v, dtype=np.float32)
        return obs_dict

    def _get_reward(self):
        rewards = {}
        for agent in self.agents:
            lanes = self.junction_incoming_lanes[agent]
            w_time = sum(self.conn.lane.getWaitingTime(lane) for lane in lanes)
            h_count = sum(self.conn.lane.getLastStepHaltingNumber(lane) for lane in lanes)
            avg_speed = np.mean([self.conn.lane.getLastStepMeanSpeed(lane) for lane in lanes]) if lanes else 0
            co2_emission = sum(self.conn.lane.getCO2Emission(lane) for lane in lanes)
            
            # Green Wave + Emission Focus Reward
            reward = -(w_time * 0.01 + h_count * 0.5) + (avg_speed * 0.1) - (co2_emission * 0.0001)
            rewards[agent] = float(np.nan_to_num(reward, nan=0.0))
        return rewards

    def reset(self, seed=None, options=None):
        try:
            self.conn.close()
        except:
            pass
        self._start_sumo()
        
        try:
            self.conn = traci.getConnection(self.connection_label)
        except AttributeError:
            self.conn = traci
            
        self.current_step = 0
        self.yellow_timers = {agent: 0 for agent in self.tls_agents}
        self.pending_phases = {agent: None for agent in self.tls_agents}
        self.current_phases = {agent: self.conn.trafficlight.getPhase(agent) for agent in self.tls_agents}
        return self._get_obs(), {agent: {} for agent in self.agents}

    def step(self, actions):
        # 1. Hiyerarşik VSL
        for zid, lanes in self.vsl_zones.items():
            for l_data in lanes:
                l_id, orig_v, target_tls = l_data["id"], l_data["orig_speed"], l_data["target_tls"]
                v_count = self.conn.lane.getLastStepVehicleNumber(l_id)
                density_factor = 0.5 if v_count > 10 else (0.8 if v_count > 5 else 1.0)
                tls_factor = 0.6 if target_tls and 'r' in self.conn.trafficlight.getRedYellowGreenState(target_tls).lower() else 1.0
                self.conn.lane.setMaxSpeed(l_id, orig_v * density_factor * tls_factor)

        # 2. TLS Agents
        if actions:
            for aid, action in actions.items():
                if self.yellow_timers[aid] > 0:
                    self.yellow_timers[aid] -= 1
                    if self.yellow_timers[aid] == 0:
                        phase_to_set = int(self.pending_phases[aid])
                        self.conn.trafficlight.setPhase(aid, phase_to_set)
                        self.current_phases[aid] = phase_to_set
                elif action != self.current_phases[aid]:
                    self.yellow_timers[aid] = self.yellow_time
                    self.pending_phases[aid] = int(action)
                    curr = self.conn.trafficlight.getPhase(aid)
                    yellow_phase = int((curr + 1) % self.action_spaces[aid].n)
                    self.conn.trafficlight.setPhase(aid, yellow_phase)

        self.conn.simulationStep()
        self.current_step += 1
        
        # En az 100 adım veya haritada araç varken devam et
        sim_bitti = self.conn.simulation.getMinExpectedNumber() <= 0
        if self.current_step < 100: sim_bitti = False
        
        done = self.current_step >= self.max_steps or sim_bitti
        return self._get_obs(), self._get_reward(), {a: done for a in self.agents}, {a: False for a in self.agents}, {a: {} for a in self.agents}

    def close(self):
        try:
            self.conn.close()
        except:
            pass
