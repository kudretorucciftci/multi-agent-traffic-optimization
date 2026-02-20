import sys, os, ray, torch, numpy as np, glob
sys.path.append("/kaggle/working")
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.models import ModelCatalog
from ray.tune.registry import register_env
from train.multi_agent_env import raw_env
from train.gnn_model import GNNTrafficModel
from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv

# 1. Kayıt İşlemleri
ModelCatalog.register_custom_model("gnn_traffic_model", GNNTrafficModel)

def env_creator(config):
    return ParallelPettingZooEnv(raw_env(
        sumo_cfg_path="/kaggle/working/maltepe.sumocfg",
        max_steps=10000, 
        label="kaggle_mega_hybrid_v4"
    ))

register_env("multi_agent_traffic_v4", lambda config: env_creator(config))

# 2. Ray Başlatma
ray.shutdown()
ray.init(ignore_reinit_error=True, num_cpus=4)

# 3. PPO Konfigürasyonu
config = (
    PPOConfig()
    .environment("multi_agent_traffic_v4")
    .framework("torch")
    .api_stack(enable_rl_module_and_learner=False, enable_env_runner_and_connector_v2=False)
    .resources(num_gpus=1)
    .env_runners(num_env_runners=1) 
    .training(
        model={"custom_model": "gnn_traffic_model"},
        train_batch_size=4000,
        lr=5e-5,
        gamma=0.99
    )
    .multi_agent(
        policies={"default_policy"},
        policy_mapping_fn=lambda agent_id, *args, **kwargs: "default_policy"
    )
)

print("🚦 Maltepe Digital Twin: Akıllı Kayıt Sistemli Mega Fine-tune Başlatılıyor...")
algo = config.build()

# 4. AKILLI RESUME (Kaldığı Yerden Devam) MANTIĞI
checkpoint_dir = "/kaggle/working/mega_v4_checkpoints"
os.makedirs(checkpoint_dir, exist_ok=True)

# Önce çalışma alanındaki en güncel checkpoint'e bak
local_checkpoints = sorted(glob.glob(os.path.join(checkpoint_dir, "checkpoint_*")), reverse=True)
base_ckpt = "/kaggle/input/gnn-hybrid-v4-new/checkpoint_000300"

if local_checkpoints:
    latest_local = local_checkpoints[0]
    print(f"♻️ Çalışma alanından DEVAM EDİLİYOR: {latest_local}")
    algo.restore(latest_local)
elif os.path.exists(base_ckpt):
    print(f"📥 Başlangıç ağırlıkları yükleniyor (Fine-tune): {base_ckpt}")
    algo.restore(base_ckpt)
else:
    print("⚠️ UYARI: Hiçbir checkpoint bulunamadı, sıfırdan eğitim başlıyor!")

# 5. EĞİTİM DÖNGÜSÜ
print("🔥 Eğitim Ateşlendi. Her 5 iterasyonda bir ve durdurulduğunda otomatik kayıt yapılacak.")

try:
    for i in range(1, 201): # Toplam 200 iterasyon hedefi
        print(f"🟡 İterasyon {i} başlatıldı (Simülasyon akıyor... Lütfen bekleyin)")
        result = algo.train()
        
        reward = result.get('episode_reward_mean')
        reward_str = f"{reward:.2f}" if reward is not None else "Veri toplanıyor..."
        print(f"📈 [Kaggle Mega] İterasyon {i} | Ortalama Başarı (Reward): {reward_str}")
        
        # Her 5 iterasyonda bir otomatik kayıt
        if i % 5 == 0:
            save_path = algo.save(checkpoint_dir=checkpoint_dir)
            print(f"💾 OTOMATİK KAYIT TAMAMLANDI: {save_path}")

except KeyboardInterrupt:
    print("\n🛑 Eğitim kullanıcı tarafından durduruldu! Son durum kaydediliyor...")
except Exception as e:
    print(f"⚠️ Kritik bir hata oluştu: {e}")
finally:
    # Her durumda en son hali kaydet
    final_save = algo.save(checkpoint_dir=checkpoint_dir)
    print(f"✅ NİHAİ GÜVENLİK KAYDI ALINDI: {final_save}")
    ray.shutdown()
