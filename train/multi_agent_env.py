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
    """
    PettingZoo ParallelEnv API'sini takip eden bir ortam oluşturur.
    """
    internal_env = raw_env(sumo_cfg_path=sumo_cfg_path, **kwargs)
    # AEC'ye özel sarmalayıcıları ParallelEnv ortamlarından kaldırın
    return internal_env

class raw_env(pettingzoo.ParallelEnv):
    metadata = {
        "name": "multi_agent_traffic_v0",
    }

    def __init__(self, sumo_cfg_path, use_gui=False, max_steps=5000):
        super().__init__()
        self.sumo_cfg = sumo_cfg_path
        self.use_gui = use_gui
        self.max_steps = max_steps
        self.current_step = 0

        # SUMO'yu başlat
        self._start_sumo()
        
        # Ajanları (trafik ışıklarını) ve ilgili verileri al
        self.agents = traci.trafficlight.getIDList()
        self.agent_name_mapping = dict(zip(self.agents, list(range(len(self.agents)))))
        
        self.junction_incoming_lanes = {
            ts: set(traci.trafficlight.getControlledLanes(ts)) for ts in self.agents
        }
        
        # Her ajan için aksiyon ve gözlem uzaylarını tanımla
        # Aksiyon: Fazı değiştir veya değiştirme
        self.action_spaces = {
            agent: spaces.Discrete(len(traci.trafficlight.getCompleteRedYellowGreenDefinition(agent)[0].phases)) 
            for agent in self.agents
        }
        
        # Gözlem uzayını, tüm ajanların gözlemlerini içeren tek bir vektör olarak tanımla
        num_observations = len(self.agents)
        self.observation_space_shared = spaces.Box(low=0, high=200, shape=(num_observations,), dtype=np.float32)

        self.truncations = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}
        
    def observation_space(self, agent: str):
        # Tüm ajanlar aynı gözlem uzayını paylaşır
        return self.observation_space_shared

    def action_space(self, agent: str):
        return self.action_spaces[agent]
        
    def _start_sumo(self):
        """SUMO simülasyonunu başlatır."""
        sumo_binary = sumolib.checkBinary("sumo-gui" if self.use_gui else "sumo")
        sumo_cmd = [sumo_binary, "-c", self.sumo_cfg, "--no-warnings", "--no-step-log"]
        if self.use_gui:
            sumo_cmd.extend(["--start", "--quit-on-end"])
            
        traci.start(sumo_cmd)

    def _get_obs(self):
        """Tüm sistem için tek bir gözlem vektörü oluşturur."""
        obs_vector = []
        for agent in self.agents: # self.agents sıralı bir liste olduğu için sıralama tutarlıdır
            incoming_lanes = self.junction_incoming_lanes[agent]
            vehicle_count = sum(traci.lane.getLastStepVehicleNumber(lane) for lane in incoming_lanes)
            obs_vector.append(vehicle_count)
        
        # Tüm ajanlar aynı birleşik gözlemi alır
        shared_observation = np.array(obs_vector, dtype=np.float32)
        return {agent: shared_observation for agent in self.agents}

    def _get_reward(self):
        """Tüm sistem için global bir ödül hesaplar."""
        lane_waiting_times = {}
        for junction_lanes in self.junction_incoming_lanes.values():
            for lane in junction_lanes:
                waiting_time = traci.lane.getWaitingTime(lane)
                lane_waiting_times[lane] = waiting_time
        
        total_waiting_time = sum(lane_waiting_times.values())
        
        # Bekleme süresini negatif ödül olarak kullan
        reward = -total_waiting_time
        return {agent: reward for agent in self.agents}


    def reset(self, seed=None, options=None):
        """Ortamı sıfırlar."""
        traci.close()
        self._start_sumo()
        self.current_step = 0
        
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}

        observations = self._get_obs()
        return observations, self.infos

    def step(self, actions):
        """Ortamda bir adım ilerler."""
        if not actions:
            # Aksiyon yoksa bir adım ilerle
            traci.simulationStep()
            self.current_step += 1
        else:
            for agent_id, action in actions.items():
                current_phase = traci.trafficlight.getPhase(agent_id)
                if current_phase != action:
                    traci.trafficlight.setPhase(agent_id, action)

            traci.simulationStep()
            self.current_step += 1

        # Gözlemleri, ödülleri ve bitiş durumlarını al
        observations = self._get_obs()
        step_rewards = self._get_reward()
        
        # Sonlandırma koşulları
        sim_bitti = traci.simulation.getMinExpectedNumber() <= 0
        if self.current_step >= self.max_steps or sim_bitti:
            # Episode sona erdiğinde terminations'ı True yap
            self.terminations = {agent: True for agent in self.agents}
            self.truncations = {agent: False for agent in self.agents} # Bu durumda truncation değil termination
        else:
            self.terminations = {agent: False for agent in self.agents}
            self.truncations = {agent: False for agent in self.agents}

        
        return observations, step_rewards, self.terminations, self.truncations, self.infos

    def render(self):
        """SUMO-GUI'yi render eder (zaten açıksa)."""
        pass

    def close(self):
        """Ortamı kapatır."""
        traci.close()
