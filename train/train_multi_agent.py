import os
import sys
import ray
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
import csv

# Proje kök dizinini Python yoluna ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv
from train.multi_agent_env import raw_env as multi_agent_traffic_raw_env

# Ortamı rllib'e kaydet
def env_creator(env_config):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sumo_cfg_path = os.path.join(project_root, "maltepe.sumocfg")
    pettingzoo_env = multi_agent_traffic_raw_env(sumo_cfg_path=sumo_cfg_path, **env_config)
    return ParallelPettingZooEnv(pettingzoo_env)

register_env("multi_agent_traffic_env", env_creator)

# Ray'i başlat
ray.shutdown()
ray.init(ignore_reinit_error=True)

# PPO algoritmasını yapılandır (Yeni V1 Mimariye Göre Optimize Edildi)
config = (
    PPOConfig()
    .environment(
        "multi_agent_traffic_env", 
        env_config={"use_gui": False, "max_steps": 5000}
    )
    .env_runners(
        num_env_runners=1, 
        rollout_fragment_length=2000 # Daha sık güncelleme için ayarlandı
    )
    .training(
        gamma=0.99,
        lr=5e-5,
        train_batch_size=4000,
        model={
            "fcnet_hiddens": [256, 256, 256], # Daha derin ağ ile graf verisini işleme
            "fcnet_activation": "relu",
        },
        use_gae=True,
        lambda_=0.95,
        vf_loss_coeff=0.5,
        entropy_coeff=0.05, # Keşif (exploration) için artırıldı
    )
    .multi_agent(
        policies={"shared_policy"},
        policy_mapping_fn=(lambda agent_id, episode, **kwargs: "shared_policy"),
    )
    .evaluation(
        evaluation_num_env_runners=1,
        evaluation_interval=5, # Her 5 iterasyonda bir test et
        evaluation_duration=1,
        evaluation_config={"explore": False}
    )
    .resources(num_gpus=0)
)

# Algoritmayı oluştur
algo = config.build()

metrics_file_path = "training_metrics.csv"
with open(metrics_file_path, 'w', newline='') as csvfile:
    metric_writer = csv.writer(csvfile)
    metric_writer.writerow(["Iterasyon", "Egitim Ort. Odul", "Degerlendirme Ort. Odul", "Toplam Adim"])

print("🚀 Yeni V1 Mimarisi ile kapsamlı eğitim başlıyor...")

try:
    for i in range(200): # 200 iterasyon için eğit
        result = algo.train()
        
        train_reward = result.get("env_runners", {}).get('episode_return_mean', 0)
        eval_reward = result.get("evaluation", {}).get('episode_return_mean', 0)
        total_steps = result.get('timesteps_total', 0)
        
        print(f"İterasyon {i+1}: Ödül={train_reward:.2f}, Test Ödülü={eval_reward:.2f}, Toplam Adım={total_steps}")
        
        with open(metrics_file_path, 'a', newline='') as csvfile:
            metric_writer = csv.writer(csvfile)
            metric_writer.writerow([i+1, train_reward, eval_reward, total_steps])
except KeyboardInterrupt:
    print("\n🛑 Eğitim kullanıcı tarafından durduruldu.")

# Modeli kaydet (Nihai Model)
checkpoint_path = os.path.abspath(os.path.join("run", "multi_agent_model"))
algo.save(checkpoint_path)
print(f"✅ Nihai model kaydedildi: {checkpoint_path}")

ray.shutdown()
