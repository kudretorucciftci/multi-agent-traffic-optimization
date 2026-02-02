import os
import sys
import numpy as np
import ray
from ray.rllib.algorithms.ppo import PPOConfig, PPO
from ray.tune.registry import register_env
import traci

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
    pettingzoo_env = multi_agent_traffic_raw_env(sumo_cfg_path=sumo_cfg_path, **env_config)
    from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv
    return ParallelPettingZooEnv(pettingzoo_env)

register_env("multi_agent_traffic_env", env_creator)

def main():
    # Ray'i sınırlı kaynaklarla başlat
    try:
        # Windows'ta Ray bellek sorunu için spesifik ayarlar
        ray.init(
            num_cpus=1, 
            memory=512 * 1024 * 1024,        # 512 MB
            object_store_memory=128 * 1024 * 1024, # 128 MB
            ignore_reinit_error=True,
            include_dashboard=False,
            _system_config={"num_gpus": 0}
        )
        print("✅ Ray başarıyla başlatıldı.")
    except Exception as e:
        print(f"⚠️ Ray başlatılırken hata oluştu (ancak devam ediliyor): {e}")

    # En Son Kontrol Noktasını Bul
    checkpoint_dir = os.path.abspath(os.path.join(project_root, "run", "multi_agent_model"))
    
    print(f"Checkpoint yükleniyor: {checkpoint_dir}")
    
    # Algoritmayı yapılandır (hata almamak için eğitimdeki modele sadık kalıyoruz)
    config = (
        PPOConfig()
        .environment("multi_agent_traffic_env")
        .env_runners(num_env_runners=0) # Yerel işlemci kullanımı
        .training(model={"fcnet_hiddens": [256, 256]})
        .multi_agent(
            policies={"shared_policy"},
            policy_mapping_fn=(lambda agent_id, episode, **kwargs: "shared_policy"),
        )
    )
    
    # Modeli yükle
    algo = config.build()
    try:
        algo.restore(checkpoint_dir)
        print("✅ Model başarıyla geri yüklendi.")
    except Exception as e:
        print(f"❌ Model yükleme hatası: {e}")
        return

    # Ortamı manuel olarak başlat
    print("🚀 SUMO-GUI başlatılıyor...")
    env = env_creator({"use_gui": True, "max_steps": 500})
    obs, info = env.reset()

    try:
        traci.gui.setSchema("View #0", "real world")
        traci.gui.setZoom("View #0", 1000)
    except:
        pass

    total_reward = 0
    step_count = 0
    
    print("\n" + "="*70)
    print(f"{'Adım':<8} | {'Ort. Araç Kuyruğu':<18} | {'Adım Ödülü':<12} | {'Toplam Ödül':<15}")
    print("-" * 70)

    try:
        done = False
        while not done and step_count < 500:
            actions = {}
            
            # RLModule üzerinden aksiyonları hesapla
            rl_module = algo.get_module("shared_policy")
            
            # Gözlemleri topla ve tensor'a çevir
            # Tüm ajanlar aynı gözlemi (Box vektörü) aldığı için ilkini kullanıyoruz
            sample_agent = list(obs.keys())[0]
            obs_tensor = torch.tensor(obs[sample_agent]).unsqueeze(0)
            
            import torch
            with torch.no_grad():
                action_dist_inputs = rl_module.forward_inference({"obs": obs_tensor})
                from ray.rllib.models.torch.torch_action_dist import TorchCategorical
                action_dist = TorchCategorical(action_dist_inputs, rl_module)
                all_actions = action_dist.sample().squeeze(0).cpu().numpy()

            # Aksiyonları ajanlara dağıt
            for agent_id in obs.keys():
                actions[agent_id] = all_actions.item() # Şu anki basitleştirilmiş yapıda tek aksiyon

            # Adım ilerle
            obs, rewards, terminations, truncations, infos = env.step(actions)
            
            # Analiz verileri
            step_reward = sum(rewards.values())
            total_reward += step_reward
            avg_queue = np.mean(obs[sample_agent])
            
            if step_count % 5 == 0:
                print(f"{step_count:<8} | {avg_queue:<18.2f} | {step_reward:<12.2f} | {total_reward:<15.2f}")
            
            done = all(terminations.values()) or all(truncations.values())
            step_count += 1

    except Exception as e:
        print(f"\n⚠️ Simülasyon sırasında hata: {e}")
    finally:
        print("\n" + "="*70)
        print(f"🏁 Simülasyon Bitti. Toplam Adım: {step_count}, Toplam Ödül: {total_reward:.2f}")
        env.close()
        ray.shutdown()

if __name__ == "__main__":
    main()
