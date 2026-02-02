import os
import sys
import ray
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
import csv # csv modülünü import et

# Proje kök dizinini Python yoluna ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import sys
from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv # UPDATED IMPORT
from train.multi_agent_env import raw_env as multi_agent_traffic_raw_env # Import raw_env directly

# Ortamı rllib'e kaydet
def env_creator(env_config):
    # Proje kök dizinini bul
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # sumo.cfg dosyasının tam yolunu oluştur
    sumo_cfg_path = os.path.join(project_root, "maltepe.sumocfg")
    
    # PettingZoo raw_env'i oluştur
    pettingzoo_env = multi_agent_traffic_raw_env(sumo_cfg_path=sumo_cfg_path, **env_config)
    
    # PettingZoo ortamını RLlib uyumlu hale getir
    return ParallelPettingZooEnv(pettingzoo_env) # UPDATED CLASS

register_env("multi_agent_traffic_env", env_creator)

# Ray'i başlat
ray.shutdown() # Önceki Ray oturumlarını kapat
ray.init(ignore_reinit_error=True)

# PPO algoritmasını yapılandır
config = (
    PPOConfig()
    .environment(
        "multi_agent_traffic_env", 
        env_config={"use_gui": False, "max_steps": 5000} # max_steps 5000 olarak güncellendi
    )
    .env_runners(num_env_runners=1, rollout_fragment_length=5000)
    .training(
        gamma=0.99,
        lr=5e-5,
        train_batch_size=5000,
        model={"fcnet_hiddens": [256, 256]},
        use_gae=True,
        lambda_=0.95,
        vf_loss_coeff=0.5,
        entropy_coeff=0.01,
    )
    .multi_agent(
        policies={"shared_policy"},
        policy_mapping_fn=(lambda agent_id, episode, **kwargs: "shared_policy"),
    )
    .resources(num_gpus=0)  # CPU kullanarak eğitim
)


# Algoritmayı oluştur
algo = config.build()

# Metrikleri kaydetmek için CSV dosyasını hazırla
metrics_file_path = "training_metrics.csv"
with open(metrics_file_path, 'w', newline='') as csvfile:
    metric_writer = csv.writer(csvfile)
    metric_writer.writerow(["Iterasyon", "Egitim Ort. Odul", "Degerlendirme Ort. Odul", "Toplam Adim"])

# Modeli eğit
print(f"Çoklu ajan modeli eğitimi başlıyor. Metrikler '{metrics_file_path}' dosyasına kaydedilecek...")
for i in range(150):  # 150 iterasyon için eğit
    result = algo.train()
    # Metrikleri doğru yollardan al
    train_metrics = result.get("env_runners", {})
    eval_metrics = result.get("evaluation", {})
    
    train_reward = train_metrics.get('episode_return_mean', 'N/A')
    eval_reward = eval_metrics.get('episode_return_mean', 'N/A')
    total_steps = result.get('timesteps_total', 'N/A')
    
    # Metrikleri CSV dosyasına yaz
    with open(metrics_file_path, 'a', newline='') as csvfile:
        metric_writer = csv.writer(csvfile)
        metric_writer.writerow([i+1, train_reward, eval_reward, total_steps])

# Eğitilmiş modeli kaydet
checkpoint_path = os.path.abspath(os.path.join("run", "multi_agent_model"))
checkpoint_dir = algo.save(checkpoint_path)
print(f"Model kaydedildi: {checkpoint_dir}")

# Ray'i kapat
ray.shutdown()
print("Eğitim tamamlandı.")
