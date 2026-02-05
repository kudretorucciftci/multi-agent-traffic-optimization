import os
import sys
import ray
import torch
import csv
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
from ray.rllib.models import ModelCatalog

# Proje kök dizini
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv
from train.multi_agent_env import raw_env as multi_agent_traffic_raw_env
from train.gnn_model import GNNTrafficModel

# 1. Model Kaydı
ModelCatalog.register_custom_model("gnn_traffic_model", GNNTrafficModel)

# 2. Ortam Kaydı
def env_creator(env_config):
    sumo_cfg_path = os.path.join(project_root, "maltepe.sumocfg")
    pettingzoo_env = multi_agent_traffic_raw_env(sumo_cfg_path=sumo_cfg_path, **env_config)
    return ParallelPettingZooEnv(pettingzoo_env)

register_env("multi_agent_traffic_env", env_creator)

# 3. Ray Başlatma
ray.shutdown()
ray.init(ignore_reinit_error=True)

# 4. PPO Konfigürasyonu (Hibrit V4: GNN + Yeşil Dalga + Emisyon)
config = (
    PPOConfig()
    .environment("multi_agent_traffic_env", env_config={"use_gui": False, "max_steps": 5000})
    .framework("torch")
    .env_runners(num_env_runners=1, rollout_fragment_length=2000)
    .training(
        gamma=0.99,
        lr=2e-5, # İnce ayar için daha düşük öğrenme oranı
        train_batch_size=4000,
        model={"custom_model": "gnn_traffic_model"},
        use_gae=True,
        lambda_=0.95,
        vf_loss_coeff=0.5,
        entropy_coeff=0.03,
    )
    .multi_agent(
        policies={"shared_policy"},
        policy_mapping_fn=(lambda aid, *args, **kwargs: "shared_policy"),
    )
    .evaluation(
        evaluation_num_workers=1,
        evaluation_interval=10,
        evaluation_duration=1,
        evaluation_config={"explore": False}
    )
    .api_stack(enable_rl_module_and_learner=False, enable_env_runner_and_connector_v2=False)
    .resources(num_gpus=0)
)

algo = config.build()

# 5. TECRÜBE YÜKLEME VE DEVAM ETME
# Kaggle'dan gelen en güncel modelin yolu
resume_checkpoint = os.path.abspath(os.path.join(project_root, "run", "gnn_hybrid_v4"))

start_iter = 0
metrics_file = "gnn_hybrid_metrics.csv"

# Eğer eski metrikler varsa son iterasyonu bul
if os.path.exists(metrics_file):
    with open(metrics_file, 'r') as f:
        lines = f.readlines()
        if len(lines) > 1:
            try:
                start_iter = int(lines[-1].split(",")[0])
                print(f"Eski veriler bulundu. Egitim {start_iter}. iterasyondan devam edecek.")
            except: pass

if os.path.exists(resume_checkpoint):
    print(f"Egitim {resume_checkpoint} konumundan yukleniyor...")
    try:
        algo.restore(resume_checkpoint)
        print("✅ Tecrube aktarimi basarili! Model kaldigi yerden ogrenmeye devam ediyor.")
    except Exception as e:
        print(f"⚠️ Direkt yukleme yapılamadı (Sürüm farkı olabilir), agirliklar aktarılmaya calisiliyor. Hata: {e}")
else:
    print("❌ Resume checkpoint bulunamadı, egitim sifirdan basliyor.")

# 6. EGITIM DONGUSU
if not os.path.exists(metrics_file):
    with open(metrics_file, 'w', newline='') as f:
        csv.writer(f).writerow(["Iterasyon", "Reward", "Eval_Reward", "Steps"])

print(f"FINE-TUNING DEVAM EDIYOR: Hedef 500 Iterasyon (Baslangic: {start_iter})")
try:
    for i in range(start_iter, 500):
        result = algo.train()
        reward = result.get("env_runners", {}).get("episode_return_mean", 0) or 0
        eval_reward = result.get("evaluation", {}).get("episode_return_mean", 0) or 0
        steps = result.get("timesteps_total", 0)
        
        print(f"Iterasyon {i+1}: Odul={reward:.2f}, Test={eval_reward:.2f}, Toplam Adim={steps}")
        
        with open(metrics_file, 'a', newline='') as f:
            csv.writer(f).writerow([i+1, reward, eval_reward, steps])
            
        if (i+1) % 50 == 0:
            save_path = algo.save(resume_checkpoint)
            print(f"Periyodik kayit: {save_path}")

except KeyboardInterrupt:
    print("\nKullanici durdurdu.")

final_path = algo.save(resume_checkpoint)
print(f"Egitim tamamlandi. Nihai GNN Hibrit Model: {final_path}")
ray.shutdown()
