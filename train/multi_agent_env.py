import os
import sys
import numpy as np
from gymnasium import spaces
import pettingzoo
from pettingzoo.utils import agent_selector, wrappers
import sumolib
import traci

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("SUMO_HOME'u ayarlayın")

def env(sumo_cfg_path, **kwargs):
    internal_env = raw_env(sumo_cfg_path=sumo_cfg_path, **kwargs)
    return internal_env

class raw_env(pettingzoo.ParallelEnv):
    metadata = {"name": "multi_agent_traffic_v1"}

    def __init__(self, sumo_cfg_path, use_gui=False, max_steps=5000, label="default"):
        super().__init__()
        self.sumo_cfg = sumo_cfg_path
        self.use_gui = use_gui
        self.max_steps = max_steps
        self.current_step = 0
        self.label = label

        self._start_sumo()
        
        # Ajan Tiplerini Belirle
        self.tls_agents = list(traci.trafficlight.getIDList())
        self.vsl_agents = [] # Boş bırakıyoruz (RLlib uyumluluğu için)
        self.agents = self.tls_agents + self.vsl_agents
        
        # Kavşak bağlantılarını ve şeritleri önbelleğe al
        self.junction_incoming_lanes = {}
        self.vsl_lane_speeds = {} # VSL ajanları için orijinal hızları sakla
        
        net = sumolib.net.readNet(sumo_cfg_path.replace(".sumocfg", ".net.xml"))
        
        for agent in self.agents:
            if agent in self.tls_agents:
                lanes = set(traci.trafficlight.getControlledLanes(agent))
            else:
                # Işıksız kavşaklar için gelen tüm şeritleri bul
                lanes = set()
                node = net.getNode(agent)
                incoming_edges = [e.getID() for e in node.getIncoming()]
                for edge_id in incoming_edges:
                    for i in range(traci.edge.getLaneNumber(edge_id)):
                        lane_id = f"{edge_id}_{i}"
                        lanes.add(lane_id)
                        self.vsl_lane_speeds[lane_id] = traci.lane.getMaxSpeed(lane_id)
            
            self.junction_incoming_lanes[agent] = lanes
        
        # Her kavşağın komşu kavşaklarını bul
        self.neighbors = {}
        for agent in self.agents:
            pos = traci.junction.getPosition(agent)
            distances = []
            for other in self.agents:
                if agent != other:
                    other_pos = traci.junction.getPosition(other)
                    dist = np.sqrt((pos[0]-other_pos[0])**2 + (pos[1]-other_pos[1])**2)
                    distances.append((other, dist))
            distances.sort(key=lambda x: x[1])
            self.neighbors[agent] = [d[0] for d in distances[:2]]
        
        # Aksiyon Uzayları
        self.action_spaces = {}
        for agent in self.agents:
            if agent in self.tls_agents:
                n_phases = len(traci.trafficlight.getCompleteRedYellowGreenDefinition(agent)[0].phases)
                self.action_spaces[agent] = spaces.Discrete(n_phases)
            else:
                # VSL için 4 hız seviyesi: 0:%100, 1:%70, 2:%40, 3:%10
                self.action_spaces[agent] = spaces.Discrete(4)
        
        self.obs_dim = 3 + 2 
        self.observation_space_shared = spaces.Box(low=0, high=500, shape=(self.obs_dim,), dtype=np.float32)

        # Sarı ışık yönetimi için değişkenler
        self.yellow_time = 3
        self.yellow_timers = {agent: 0 for agent in self.tls_agents}
        self.pending_phases = {agent: None for agent in self.tls_agents}
        self.current_phases = {}
        for agent in self.agents:
            if agent in self.tls_agents:
                self.current_phases[agent] = traci.trafficlight.getPhase(agent)
            else:
                self.current_phases[agent] = 0

    def observation_space(self, agent: str):
        return self.observation_space_shared

    def action_space(self, agent: str):
        return self.action_spaces[agent]
        
    def _start_sumo(self):
        sumo_binary = sumolib.checkBinary("sumo-gui" if self.use_gui else "sumo")
        sumo_cmd = [sumo_binary, "-c", self.sumo_cfg, "--no-warnings", "--no-step-log"]
        if self.use_gui:
            sumo_cmd.extend(["--start", "--quit-on-end"])
        traci.start(sumo_cmd, label=self.label)

    def _get_obs(self):
        all_stats = {}
        for agent in self.agents:
            lanes = self.junction_incoming_lanes[agent]
            v_count = sum(traci.lane.getLastStepVehicleNumber(lane) for lane in lanes)
            w_time = sum(traci.lane.getWaitingTime(lane) for lane in lanes)
            h_count = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in lanes)
            all_stats[agent] = {"v": v_count, "w": w_time, "h": h_count}

        obs_dict = {}
        for agent in self.agents:
            kendi = all_stats[agent]
            # Komşuların araç sayılarını ekle
            comp_data = []
            for n in self.neighbors[agent]:
                comp_data.append(all_stats[n]["v"])
            
            full_obs = np.array([kendi["v"], kendi["w"], kendi["h"]] + comp_data, dtype=np.float32)
            obs_dict[agent] = full_obs
            
        return obs_dict

    def _get_reward(self):
        local_rewards = {}
        for agent in self.agents:
            lanes = self.junction_incoming_lanes[agent]
            w_time = sum(traci.lane.getWaitingTime(lane) for lane in lanes)
            h_count = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in lanes)
            # Normalize edilmiş lokal ceza
            local_rewards[agent] = -(w_time * 0.01 + h_count * 0.1)

        rewards = {}
        for agent in self.agents:
            # İşbirlikçi ödül: Kendi_Ödül + 0.5 * (Komşuların_Ödülleri)
            neighbor_contrib = sum(local_rewards[n] for n in self.neighbors[agent])
            rewards[agent] = local_rewards[agent] + 0.5 * neighbor_contrib
            
        return rewards

    def reset(self, seed=None, options=None):
        traci.close()
        self._start_sumo()
        self.current_step = 0
        
        # Sadece TLS ajanları için faz/zamanlayıcı yönetimi
        self.yellow_timers = {agent: 0 for agent in self.tls_agents}
        self.pending_phases = {agent: None for agent in self.tls_agents}
        self.current_phases = {}
        
        for agent in self.agents:
            if agent in self.tls_agents:
                self.current_phases[agent] = traci.trafficlight.getPhase(agent)
            else:
                self.current_phases[agent] = 0 # VSL başlangıç durumu (%100 hız)
        
        return self._get_obs(), {agent: {} for agent in self.agents}

    def step(self, actions):
        if actions:
            for agent_id, action in actions.items():
                if agent_id in self.tls_agents:
                    # TRAFİK IŞIĞI MANTIĞI
                    target_phase = action
                    if self.yellow_timers[agent_id] > 0:
                        self.yellow_timers[agent_id] -= 1
                        if self.yellow_timers[agent_id] == 0:
                            traci.trafficlight.setPhase(agent_id, self.pending_phases[agent_id])
                            self.current_phases[agent_id] = self.pending_phases[agent_id]
                    else:
                        if target_phase != self.current_phases[agent_id]:
                            self.yellow_timers[agent_id] = self.yellow_time
                            self.pending_phases[agent_id] = target_phase
                            current = traci.trafficlight.getPhase(agent_id)
                            traci.trafficlight.setPhase(agent_id, (current + 1) % self.action_spaces[agent_id].n)
                else:
                    # VSL (HIZ KONTROL) MANTIĞI
                    # action -> 0: %100, 1: %70, 2: %40, 3: %10 hız
                    speed_factors = [1.0, 0.7, 0.4, 0.1]
                    factor = speed_factors[action]
                    for lane in self.junction_incoming_lanes[agent_id]:
                        orig_speed = self.vsl_lane_speeds[lane]
                        traci.lane.setMaxSpeed(lane, orig_speed * factor)

        traci.simulationStep()
        self.current_step += 1

        observations = self._get_obs()
        step_rewards = self._get_reward()
        
        sim_bitti = traci.simulation.getMinExpectedNumber() <= 0
        terminated = self.current_step >= self.max_steps or sim_bitti
        
        terminations = {agent: terminated for agent in self.agents}
        truncations = {agent: False for agent in self.agents}
        
        return observations, step_rewards, terminations, truncations, {agent: {} for agent in self.agents}

    def close(self):
        traci.close()

