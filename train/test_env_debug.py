import os
import sys
import traci

# Proje kök dizinini Python yoluna ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from train.multi_agent_env import raw_env

def test_env():
    sumo_cfg_path = os.path.join(project_root, "maltepe.sumocfg")
    try:
        env = raw_env(sumo_cfg_path=sumo_cfg_path, use_gui=False)
        obs, infos = env.reset()
        print("Env Reset Success!")
        print("Agents:", env.agents)
        
        actions = {agent: 0 for agent in env.agents}
        obs, rewards, terminations, truncations, infos = env.step(actions)
        print("Env Step Success!")
        print("Rewards:", rewards)
        
        env.close()
        print("Env Test Passed!")
    except Exception as e:
        print(f"Env Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_env()
