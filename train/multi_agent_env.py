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

    def __init__(self, sumo_cfg_path, use_gui=False, max_steps=5000):
        super().__init__()
        self.sumo_cfg = sumo_cfg_path
        self.use_gui = use_gui
        self.max_steps = max_steps
        self.current_step = 0

        self._start_sumo()
        self.agents = traci.trafficlight.getIDList()
        
        # Kavşak bağlantılarını ve şeritleri önbelleğe al
        self.junction_incoming_lanes = {
            ts: set(traci.trafficlight.getControlledLanes(ts)) for ts in self.agents
        }
        
        # Her kavşağın komşu kavşaklarını bul (Basit mesafe tabanlı veya manuel tanımlı)
        # Şimdilik her ajanın gözlemine tüm ajanların bilgisini ekliyoruz (Global farkındalık)
        
        self.action_spaces = {
            agent: spaces.Discrete(len(traci.trafficlight.getCompleteRedYellowGreenDefinition(agent)[0].phases)) 
            for agent in self.agents
        }
        
        # Gözlem Uzayı: Her ajan için [Kendi_Araç_Sayısı, Kendi_Bekleme_Süresi, Kendi_Halt_Sayısı, *Diğer_Ajanların_Araç_Sayıları]
        # Örn: 6 ajan varsa, 3 (kendi) + 5 (diğerleri) = 8 birimlik gözlem
        num_agents = len(self.agents)
        self.obs_dim = 3 + (num_agents - 1)
        self.observation_space_shared = spaces.Box(low=0, high=500, shape=(self.obs_dim,), dtype=np.float32)

        # Sarı ışık yönetimi için değişkenler
        self.yellow_time = 3
        self.yellow_timers = {agent: 0 for agent in self.agents}
        self.pending_phases = {agent: None for agent in self.agents}
        self.current_phases = {agent: traci.trafficlight.getPhase(agent) for agent in self.agents}

    def observation_space(self, agent: str):
        return self.observation_space_shared

    def action_space(self, agent: str):
        return self.action_spaces[agent]
        
    def _start_sumo(self):
        sumo_binary = sumolib.checkBinary("sumo-gui" if self.use_gui else "sumo")
        sumo_cmd = [sumo_binary, "-c", self.sumo_cfg, "--no-warnings", "--no-step-log"]
        if self.use_gui:
            sumo_cmd.extend(["--start", "--quit-on-end"])
        traci.start(sumo_cmd)

    def _get_obs(self):
        all_counts = []
        all_stats = {}
        
        # Önce tüm ajanların temel verilerini topla
        for agent in self.agents:
            lanes = self.junction_incoming_lanes[agent]
            v_count = sum(traci.lane.getLastStepVehicleNumber(lane) for lane in lanes)
            w_time = sum(traci.lane.getWaitingTime(lane) for lane in lanes)
            h_count = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in lanes)
            all_counts.append(v_count)
            all_stats[agent] = [v_count, w_time, h_count]

        obs_dict = {}
        for i, agent in enumerate(self.agents):
            kendi_verisi = all_stats[agent] # [v, w, h]
            digerleri = [all_counts[j] for j in range(len(self.agents)) if i != j]
            full_obs = np.array(kendi_verisi + digerleri, dtype=np.float32)
            obs_dict[agent] = full_obs
            
        return obs_dict

    def _get_reward(self):
        rewards = {}
        for agent in self.agents:
            lanes = self.junction_incoming_lanes[agent]
            # Ceza: Bekleme süresi + Kuyruk uzunluğu (Halt sayısı)
            w_time = sum(traci.lane.getWaitingTime(lane) for lane in lanes)
            h_count = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in lanes)
            
            # Lokal ödül (Her kavşak kendi trafiğinden sorumlu)
            rewards[agent] = -(w_time * 0.1 + h_count * 1.0)
            
        return rewards

    def reset(self, seed=None, options=None):
        traci.close()
        self._start_sumo()
        self.current_step = 0
        self.yellow_timers = {agent: 0 for agent in self.agents}
        self.pending_phases = {agent: None for agent in self.agents}
        self.current_phases = {agent: traci.trafficlight.getPhase(agent) for agent in self.agents}
        
        return self._get_obs(), {agent: {} for agent in self.agents}

    def step(self, actions):
        if actions:
            for agent_id, target_phase in actions.items():
                if self.yellow_timers[agent_id] > 0:
                    # Sarı ışıkta bekliyor
                    self.yellow_timers[agent_id] -= 1
                    if self.yellow_timers[agent_id] == 0:
                        # Sarı bitti, hedef faza geç
                        traci.trafficlight.setPhase(agent_id, self.pending_phases[agent_id])
                        self.current_phases[agent_id] = self.pending_phases[agent_id]
                else:
                    # Normal işleyiş
                    if target_phase != self.current_phases[agent_id]:
                        # Faz değişimi istendi, araya sarı ışık sok (Simetrik yapıda sarı fazları genelde tek sayılardır)
                        # Not: Bu mantık SUMO net.xml'deki faz dizilimine bağlıdır. 
                        # Genelde 0: Yeşil, 1: Sarı, 2: Kırmızı şeklindedir.
                        # Şimdilik basitleştirilmiş: Eğer değişim varsa 3 adım bekle.
                        self.yellow_timers[agent_id] = self.yellow_time
                        self.pending_phases[agent_id] = target_phase
                        # traci.trafficlight.setPhase(agent_id, find_yellow_phase(target_phase)) 
                        # Basitlik için sadece mevcut fazda bekletiyoruz veya sarı faza zorluyoruz:
                        current = traci.trafficlight.getPhase(agent_id)
                        # SUMO'da sarı fazı bulmaya çalış (varsayılan +1 olabilir)
                        traci.trafficlight.setPhase(agent_id, (current + 1) % self.action_spaces[agent_id].n)

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

