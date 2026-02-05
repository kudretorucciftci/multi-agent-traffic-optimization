import os
import sys
import torch
import numpy as np
from gymnasium import spaces

# Proje kök dizinini Python yoluna ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from train.multi_agent_env import raw_env
from train.gnn_model import GNNTrafficModel

def test_model_and_env():
    sumo_cfg_path = os.path.join(project_root, "maltepe.sumocfg")
    env = raw_env(sumo_cfg_path=sumo_cfg_path, use_gui=False)
    obs_dict, info = env.reset()
    
    # Model oluştur
    obs_space = env.observation_space_shared
    action_space = list(env.action_spaces.values())[0]
    num_outputs = action_space.n
    model = GNNTrafficModel(obs_space, action_space, num_outputs, {}, "test_model")
    
    # Tek bir adım testi
    agent_id = env.agents[0]
    obs = torch.from_numpy(obs_dict[agent_id]).unsqueeze(0) # [1, 5]
    
    try:
        logits, state = model({"obs": obs}, [], None)
        print("Model Forward Prediction Success!")
        print("Logits Shape:", logits.shape)
        
        value = model.value_function()
        print("Value Function Success:", value.item())
        
        # Env step
        actions = {a: 0 for a in env.agents}
        obs, rewards, terminations, truncations, infos = env.step(actions)
        print("Env Step Success!")
        print("Reward sample:", rewards[agent_id])
        
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        env.close()

if __name__ == "__main__":
    test_model_and_env()
