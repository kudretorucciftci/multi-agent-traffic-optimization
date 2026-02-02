import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# SUMO_HOME kontrolü
if "SUMO_HOME" not in os.environ:
    print("WARNING: SUMO_HOME not set in environment!")

from train.multi_agent_env import raw_env as multi_agent_traffic_raw_env
from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv

def test_env():
    try:
        sumo_cfg_path = os.path.join(project_root, "maltepe.sumocfg")
        print(f"SUMO config path: {sumo_cfg_path}")
        
        # PettingZoo raw_env'i oluştur
        pettingzoo_env = multi_agent_traffic_raw_env(sumo_cfg_path=sumo_cfg_path, use_gui=False, max_steps=100)
        print("PettingZoo env created.")
        
        # RLlib sarmalayıcısını test et
        rllib_env = ParallelPettingZooEnv(pettingzoo_env)
        print("RLlib ParallelPettingZooEnv created successfully.")
        
        obs, info = rllib_env.reset()
        print(f"Reset successful. Observation keys: {obs.keys()}")
        
        # Tek bir adım atalım
        actions = {agent: 0 for agent in rllib_env.agents}
        obs, rewards, terminations, truncations, infos = rllib_env.step(actions)
        print("Step successful.")
        
        rllib_env.close()
        print("Env closed.")
        
    except Exception as e:
        print(f"Error during env test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_env()
