import os
import sys
import torch
import numpy as np
import pickle
import pandas as pd
import time
from train.multi_agent_env import raw_env
from train.gnn_model import GNNTrafficModel
from gymnasium import spaces

# Proje dizini
sys.path.append(os.getcwd())

def run_evaluation_until_empty():
    print("🚀 Mega Fine-tune Ağırlıkları Yükleniyor (Sınırsız Süre - Tüm Araçlar Bitene Kadar)...")
    
    # 1. Ortamı Hazırla
    # max_steps'i çok büyük yapıyoruz (veya mantıksal olarak sonsuz)
    # Ama asıl kontrolü döngü içinde 'active_vehicles' ile yapacağız
    env = raw_env(
        sumo_cfg_path="maltepe.sumocfg",
        use_gui=True,
        max_steps=10000, 
        label="eval_until_empty"
    )
    
    # 2. Modeli Oluştur ve Ağırlıkları Yükle
    first_agent = env.agents[0]
    model = GNNTrafficModel(
        obs_space=env.observation_space(first_agent),
        action_space=env.action_space(first_agent),
        num_outputs=env.action_space(first_agent).n,
        model_config={},
        name="gnn_eval"
    )
    
    weights_path = "mega_v4_checkpoints/policies/shared_policy/policy_state.pkl"
    with open(weights_path, "rb") as f:
        state = pickle.load(f)
        weights = state["weights"]
        
    state_dict = {k: torch.tensor(v) if not isinstance(v, torch.Tensor) else v for k, v in weights.items()}
    model.load_state_dict(state_dict)
    model.eval()
    print("✅ Model Hazır. Tüm 5000 araç bitene kadar simülasyon akacak.")

    # 3. Metrik Toplama
    metrics_list = []
    
    # 4. Simülasyon Döngüsü
    obs_dict, _ = env.reset()
    step_count = 0
    start_time = time.time()
    
    try:
        while True:
            actions = {}
            for agent_id, obs in obs_dict.items():
                with torch.no_grad():
                    input_dict = {"obs": torch.tensor(obs).unsqueeze(0)}
                    logits, _ = model.forward(input_dict, None, None)
                    actions[agent_id] = torch.argmax(logits, dim=1).item()
            
            obs_dict, rewards, terminations, truncations, infos = env.step(actions)
            
            # Verileri al
            active_vehicles = env.conn.simulation.getMinExpectedNumber()
            total_waiting_time = sum(env.conn.lane.getWaitingTime(l) for a in env.tls_agents for l in env.junction_incoming_lanes[a])
            total_halting_vehicles = sum(env.conn.lane.getLastStepHaltingNumber(l) for a in env.tls_agents for l in env.junction_incoming_lanes[a])
            mean_speed = np.mean([env.conn.lane.getLastStepMeanSpeed(l) for a in env.tls_agents for l in env.junction_incoming_lanes[a]])
            
            metrics_list.append({
                "step": step_count,
                "active_vehicles": active_vehicles,
                "waiting_time": total_waiting_time,
                "halting": total_halting_vehicles,
                "speed": mean_speed,
                "reward": sum(rewards.values())
            })
            
            step_count += 1
            if step_count % 100 == 0:
                print(f"Adım: {step_count} | Kalan Araç: {active_vehicles} | Bekleme: {total_waiting_time:.1f}")
            
            # KRİTİK KONTROL: Eğer haritada araç kalmadıysa ve yeni araç girmeyecekse BİTİR
            if active_vehicles <= 0 and step_count > 100:
                print("\n🏁 Haritadaki tüm araçlar hedefine ulaştı!")
                break
                
            if step_count >= 10000: # Güvenlik sınırı
                print("\n⚠️ 10000 adıma ulaşıldı, güvenlik için durduruluyor.")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Kullanıcı durdurdu.")
    finally:
        if metrics_list:
            df = pd.DataFrame(metrics_list)
            df.to_csv("mega_v4_full_drain_5000.csv", index=False)
            print(f"✅ TÜM VERİLER KAYDEDİLDİ: 'mega_v4_full_drain_5000.csv'")
            
            # ANALİZ
            total_sim_time = time.time() - start_time
            print("\n--- NİHAİ ANALİZ (5000 Araç Tam Tahliye) ---")
            print(f"Toplam Simülasyon Süresi: {step_count} saniye (simülasyon zamanı)")
            print(f"Gerçek Bekleme Süresi Ortalama: {df['waiting_time'].mean():.2f}")
            print(f"Araç Başına Ortalama Bekleme (Tahmini): {(df['waiting_time'].sum() / 5000):.2f} saniye")
        
        env.close()

if __name__ == "__main__":
    run_evaluation_until_empty()
