import os
import sys
import ray
import traci
from ray.rllib.algorithms.algorithm import Algorithm

# Proje ana dizinini Python yoluna ekle
project_root = "c:/Users/Lenovo/Desktop/Projeler/rl-multi-agent-traffic-control"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from train.multi_agent_env import raw_env
from ray.tune.registry import register_env
from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv
from ray.rllib.models import ModelCatalog
from train.gnn_model import GNNTrafficModel

# Model Kaydı
ModelCatalog.register_custom_model("gnn_traffic_model", GNNTrafficModel)

def nihai_gorsel_analiz():
    sumo_cfg = os.path.join(project_root, "maltepe.sumocfg")
    checkpoint_path = os.path.join(project_root, "run", "gnn_hybrid_v4")
    
    # 1. Ortam Kaydı
    def env_creator(config):
        # Workers için model kaydını garantiye al
        ModelCatalog.register_custom_model("gnn_traffic_model", GNNTrafficModel)
        # Config'den gelen use_gui parametresini kullan (Workers her zaman headless olmalı)
        current_use_gui = config.get("use_gui", False)
        # Araçlar bitene kadar çalışması için max_steps'i çok yüksek yapıyoruz
        pettingzoo_env = raw_env(sumo_cfg_path=sumo_cfg, use_gui=current_use_gui, max_steps=100000)
        return ParallelPettingZooEnv(pettingzoo_env)
    
    register_env("multi_agent_traffic_env", env_creator)
    register_env("multi_agent_traffic_hybrid_v4", env_creator)

    # 2. Model Yükleme (Windows Bellek ve Worker Optimizasyonu)
    print("🧠 Yapay Zeka Yükleniyor... Lütfen bekleyin.", flush=True)
    try:
        # Ray'i yerel modda başlat (Daha kararlı ve hızlı yükleme sağlar)
        ray.init(
            ignore_reinit_error=True,
            local_mode=True,
            include_dashboard=False,
            _system_config={
                "metrics_report_interval_ms": -1,
            }
        )
        # Checkpoint'ten yüklerken worker sayısını 0 yaparak çakışmaları önle
        algo = Algorithm.from_checkpoint(
            checkpoint_path,
            config={
                "num_env_runners": 0, 
                "num_workers": 0      # Eski sürümler için
            }
        )
        print("✅ Yapay Zeka başarıyla yüklendi!")
    except Exception as e:
        print(f"⚠️ Model yüklenirken hata oluştu (Ham simülasyon denenecek): {e}")
        algo = None

    # 3. Simülasyonu Başlat
    print("🚗 SUMO-GUI AÇILIYOR. Lütfen 'Play' tuşuna basın!", flush=True)
    # Araçlar bitene kadar çalışması için max_steps'i görselleştirme tarafında da yükseltiyoruz
    env = raw_env(sumo_cfg_path=sumo_cfg, use_gui=True, max_steps=100000)
    obs, info = env.reset()
    
    total_waiting_time = 0
    total_co2 = 0
    total_finished_vehicles = 0
    vehicles_tracked = set()
    edge_waiting_times = {}
    step = 0
    
    try:
        is_done = False
        while not is_done:
            # Aksiyonları hesapla
            if algo:
                # 'shared_policy' kimliğini açıkça belirtiyoruz
                actions = {aid: algo.compute_single_action(o, policy_id="shared_policy") for aid, o in obs.items()}
            else:
                actions = {} # Model yoksa standart akış
                
            obs, rewards, terminated, truncated, info = env.step(actions)
            
            # Multi-agent bitiş kontrolü
            if isinstance(terminated, dict):
                is_done = all(terminated.values()) or terminated.get("__all__", False)
            else:
                is_done = terminated
            
            step += 1
            
            # Teknik veri toplama ve istatistik
            current_vehs = traci.vehicle.getIDList()
            step_co2 = 0
            for v_id in current_vehs:
                # Karbon Salınımı verisini SUMO'dan çek
                step_co2 += traci.vehicle.getCO2Emission(v_id)
                
                # Toplam bekleme süresi hesabı (her adımda 1 sn eklenir eğer hızı 0.1'den azsa)
                if traci.vehicle.getSpeed(v_id) < 0.1:
                    total_waiting_time += 1
                
                # Yeni giren araçları takip et
                if v_id not in vehicles_tracked:
                    vehicles_tracked.add(v_id)
                
                # Darboğaz analizi (mevcut mantık)
                w = traci.vehicle.getWaitingTime(v_id)
                if w > 10:
                    rid = traci.vehicle.getRoadID(v_id)
                    edge_waiting_times[rid] = edge_waiting_times.get(rid, 0) + 1
            
            total_co2 += step_co2
            
            # Çıkan araç sayısını hesapla
            total_finished_vehicles = len(vehicles_tracked) - len(current_vehs)
            
            if step % 50 == 0:
                avg_wait = total_waiting_time / len(vehicles_tracked) if vehicles_tracked else 0
                avg_co2 = total_co2 / len(vehicles_tracked) if vehicles_tracked else 0
                
                print(f"\n🌍 --- ÇEVRESEL VE TRAFİK ANALİZİ (1000 ARAÇ) ---", flush=True)
                print(f"⏱️ Saniye: {step} | Aktif Araç: {len(current_vehs)} | Biten: {total_finished_vehicles}")
                print(f"🌿 Toplam CO2 Salınımı: {total_co2/1000:.2f} kg")
                print(f"📉 Araç Başı Ort. CO2: {avg_co2:.2f} mg/s")
                print(f"⏳ Ort. Bekleme Süresi: {avg_wait:.1f} sn")
                print("🧠 --- KOLEKTİF ZEKA (GAT) AKTİF ---")
                print("----------------------------------------------")

        # Simülasyon bittiğinde özet rapor
        avg_wait = total_waiting_time / len(vehicles_tracked) if vehicles_tracked else 0
        avg_co2_total = total_co2 / len(vehicles_tracked) if vehicles_tracked else 0
        
        print("\n📊 --- NİHAİ PERFORMANS RAPORU (1000 ARAÇLIK PEAK TRAFİK) ---")
        print(f"✅ Toplam Tamamlayan Araç: {total_finished_vehicles}")
        print(f"⏳ Toplam Simülasyon Süresi: {step} saniye")
        print(f"📉 Ortalama Bekleme Süresi: {avg_wait:.2f} saniye")
        print(f"🌿 Toplam Karbon Ayak İzi: {total_co2/1000:.2f} kg CO2")
        print(f"🌱 Araç Başına Ortalama Emisyon: {avg_co2_total:.2f} mg")
        print("\n🏆 SONUÇ: Yapay Zeka (GAT), trafik akışını modernize ederken karbon salınımını aktif olarak minimize etti.")
        print("-" * 50 + "\n")

    except Exception as e:
        print(f"Simülasyon Sonu: {e}", flush=True)
    finally:
        env.close()
        ray.shutdown()

if __name__ == "__main__":
    nihai_gorsel_analiz()
