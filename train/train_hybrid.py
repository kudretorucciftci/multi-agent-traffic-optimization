import os
import sys
import ray
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
import csv

# Proje kök dizini
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv
from train.multi_agent_env import raw_env as multi_agent_traffic_raw_env

def env_creator(env_config):
    sumo_cfg_path = os.path.join(project_root, "maltepe.sumocfg")
    pettingzoo_env = multi_agent_traffic_raw_env(sumo_cfg_path=sumo_cfg_path, **env_config)
    return ParallelPettingZooEnv(pettingzoo_env)

register_env("multi_agent_traffic_env", env_creator)

def train_professional_hybrid():
    ray.shutdown()
    ray.init(ignore_reinit_error=True)

    config = (
        PPOConfig()
        .environment(
            "multi_agent_traffic_env", 
            env_config={"use_gui": False, "max_steps": 1000}
        )
        .env_runners(num_env_runners=1, rollout_fragment_length=1000)
        .training(
            gamma=0.99,
            lr=5e-5,
            train_batch_size=4000,
            model={"fcnet_hiddens": [256, 256, 256]},
        )
        .multi_agent(
            policies={"shared_policy"},
            policy_mapping_fn=(lambda *args, **kwargs: "shared_policy"),
        )
    )

    algo = config.build()
    
    # Mevcut ilerlemeyi kontrol et
    metrics_file = "hybrid_final_metrics.csv"
    start_iter = 0
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, 'r', newline='') as f:
                reader = list(csv.reader(f))
                if len(reader) > 1:
                    last_line = reader[-1]
                    if last_line[0] != "Iter":
                        start_iter = int(last_line[0])
            print(f"📈 Mevcut ilerleme tespit edildi: {start_iter}. iterasyondan devam ediliyor...")
        except Exception as e:
            print(f"⚠️ Metrik dosyası okunurken hata: {e}")

    # Mevcut en iyi ağırlıkları yükle
    checkpoint_path = os.path.abspath(os.path.join(project_root, "run", "multi_agent_model"))
    if os.path.exists(checkpoint_path):
        print(f"♻️ Mevcut tecrübeler (weight) aktarılıyor...")
        try:
            algo.restore(checkpoint_path)
        except Exception as e:
            print(f"⚠️ Checkpoint yüklenemedi, sıfırdan başlanabilir veya yol hatalı: {e}")

    # CSV başlık ayarı
    if start_iter == 0:
        with open(metrics_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Iter", "Reward", "Steps"])

    total_target_iters = 400
    print(f"🔥 HİBRİT EĞİTİM (6 Işık + 143 Akıllı Tabela) {start_iter+1}'den {total_target_iters}'e KADAR BAŞLIYOR...")
    
    try:
        for i in range(start_iter, total_target_iters):
            result = algo.train()
            reward = result.get("env_runners", {}).get('episode_return_mean', 0)
            steps = result.get('timesteps_total', 0)
            
            # Nan kontrolü (Görsel temizlik için)
            reward_str = f"{reward:.2f}" if reward is not None else "Toplanıyor..."
            print(f"İterasyon {i+1}/{total_target_iters}: Ortalama Başarı Puanı: {reward_str}")
            
            with open(metrics_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([i+1, reward, steps])
            
            # Her 10 iterasyonda bir güvenlik kaydı (Sıklığı artırdık)
            if (i+1) % 10 == 0:
                algo.save(checkpoint_path)
                print(f"💾 Checkpoint kaydedildi: {i+1}. iterasyon")

    except KeyboardInterrupt:
        print("\n🛑 Kullanıcı tarafından durduruldu.")
    finally:
        algo.save(checkpoint_path)
        print("✅ Nihai model güncellendi.")
        ray.shutdown()

if __name__ == "__main__":
    train_professional_hybrid()
