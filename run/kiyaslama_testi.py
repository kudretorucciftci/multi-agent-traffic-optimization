import os
import sys
import numpy as np
import ray
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
import traci
import time

# Proje kök dizinini Python yoluna ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# SUMO_HOME kontrolü
if "SUMO_HOME" not in os.environ:
    os.environ["SUMO_HOME"] = r"C:\Program Files (x86)\Eclipse\Sumo"

# Çoklu ajan ortamını içe aktar
from train.multi_agent_env import raw_env as multi_agent_traffic_raw_env

# Ortamı rllib'e kaydet
def env_creator(env_config):
    sumo_cfg_path = os.path.join(project_root, "maltepe.sumocfg")
    label = env_config.get("label", "default")
    pettingzoo_env = multi_agent_traffic_raw_env(
        sumo_cfg_path=sumo_cfg_path, 
        label=label,
        **{k: v for k, v in env_config.items() if k != "label"}
    )
    from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv
    return ParallelPettingZooEnv(pettingzoo_env)

register_env("multi_agent_traffic_env", env_creator)

def run_simulation(algo=None, use_gui=False, label_tag="RL Model", traci_label="eval"):
    """
    Simülasyonu koşturur ve istatistikleri döndürür.
    algo: RL modeli (None ise baseline/sabit süreli çalışır)
    """
    print(f"\n🚀 {label_tag} başlatılıyor...")
    
    # max_steps'i 1000 yapalım ki fark belli olsun
    env_config = {"use_gui": use_gui, "max_steps": 1000, "label": traci_label}
    env = env_creator(env_config)
    obs, info = env.reset()

    total_waiting_time = 0
    step_count = 0
    waiting_times_history = []

    try:
        done = False
        while not done and step_count < 1000:
            actions = {}
            
            if algo:
                # RL Model Kararları - Ray 2.x RLModule Mimarisi (En Güncel Yöntem)
                try:
                    # Gözlemleri modelin anlayacağı toplu paket (batch) haline getir
                    from ray.rllib.utils.torch_utils import convert_to_torch_tensor
                    import torch
                    
                    # Tüm ajanların gözlemlerini tek seferde işle
                    obs_batch = {
                        "obs": torch.from_numpy(np.stack(list(obs.values()))).float()
                    }
                    
                    # Modelden (shared_policy) kararları al
                    # Ray 2.5+: get_module() -> forward_inference()
                    module = algo.get_module("shared_policy")
                    model_output = module.forward_inference(obs_batch)
                    
                    # Kararları çek ve ajanlarla eşleştir
                    raw_actions = model_output["action_dist_inputs"].detach().numpy()
                    # Eğer Discrete ise argmax alalım
                    action_indices = np.argmax(raw_actions, axis=1)
                    
                    for i, agent_id in enumerate(obs.keys()):
                        actions[agent_id] = int(action_indices[i])
                        
                except Exception as e:
                    if step_count == 0:
                        print(f"⚠️ Yeni mimari hatası, eski usul deneniyor... Hata: {e}")
                    try:
                        # Klasik yöntem (Fallback)
                        for agent_id, agent_obs in obs.items():
                            actions[agent_id] = algo.compute_single_action(
                                observation=agent_obs,
                                policy_id="shared_policy",
                                explore=False
                            )
                    except Exception as e2:
                        if step_count == 0:
                            print(f"⚠️ Tüm yöntemler başarısız: {e2}")
                        actions = {agent_id: 0 for agent_id in obs.keys()}
            else:
                # Baseline
                actions = {agent_id: 0 for agent_id in obs.keys()}

            obs, rewards, terminations, truncations, infos = env.step(actions)
            
            # İstatistikleri topla
            step_waiting = np.mean([o[1] for o in obs.values()])
            waiting_times_history.append(step_waiting)
            
            done = all(terminations.values()) or all(truncations.values())
            step_count += 1
            
            if step_count % 100 == 0:
                print(f"[{label_tag}] Adım: {step_count}, Anlık Ortalama Bekleme: {step_waiting:.2f} sn")

    except Exception as e:
        print(f"⚠️ Hata: {e}")
    finally:
        env.close()
        
    return {
        "avg_waiting": np.mean(waiting_times_history) if waiting_times_history else 0,
        "total_steps": step_count
    }

def main():
    # Ray bellek hatalarını önlemek için minimum 100MB object store veriyoruz
    ray.init(ignore_reinit_error=True, object_store_memory=100 * 1024 * 1024)
    
    # 1. RL MODELİNİ YÜKLE
    checkpoint_dir = os.path.abspath(os.path.join(project_root, "run", "multi_agent_model"))
    config = (
        PPOConfig()
        .environment("multi_agent_traffic_env", env_config={"label": "rllib_init"})
        .env_runners(num_env_runners=0)
        .training(model={"fcnet_hiddens": [256, 256]})
        .multi_agent(
            policies={"shared_policy"},
            policy_mapping_fn=(lambda agent_id, episode, **kwargs: "shared_policy"),
        )
    )
    algo = config.build()
    
    print("⏳ Model yükleniyor...")
    try:
        algo.restore(checkpoint_dir)
        print("✅ RL Modeli yüklendi.")
    except Exception as e:
        print(f"❌ Model yüklenemedi! Sadece Baseline testi yapılacak. Hata: {e}")
        algo = None

    # 2. KIYASLAMA TESTLERİNİ KOŞTUR
    print("\n" + "="*50)
    print("🔍 KIYASLAMA ANALİZİ BAŞLIYOR")
    print("="*50)

    # RL Model Testi
    rl_results = run_simulation(algo, use_gui=False, label_tag="YENİ RL MODELİ (V1)", traci_label="rl_test")
    
    # Baseline Testi
    baseline_results = run_simulation(None, use_gui=False, label_tag="BASELINE (SABİT SÜRELİ)", traci_label="baseline_test")

    # 3. SONUÇLARI GÖSTER
    print("\n" + "📊 FİNAL ANALİZ RAPORU")
    print("-" * 50)
    print(f"{'Metrik':<30} | {'Baseline':<12} | {'RL Model':<12}")
    print("-" * 50)
    print(f"{'Ort. Bekleme Süresi (sn)':<30} | {baseline_results['avg_waiting']:<12.2f} | {rl_results['avg_waiting']:<12.2f}")
    
    if baseline_results['avg_waiting'] > 0:
        improvement = ((baseline_results['avg_waiting'] - rl_results['avg_waiting']) / baseline_results['avg_waiting']) * 100
        print("-" * 50)
        print(f"🚀 İYİLEŞME ORANI: %{improvement:.2f}")
    print("="*50)

    ray.shutdown()

if __name__ == "__main__":
    main()
