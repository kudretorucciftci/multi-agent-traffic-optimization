import os
import sys
import ray
import traci
from ray.rllib.algorithms.algorithm import Algorithm

# Proje ana dizinini Python yoluna ekle
project_root = "c:/Users/Lenovo/Desktop/rl-multi-agent-traffic-control"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from train.multi_agent_env import raw_env
from ray.tune.registry import register_env

def nihai_gorsel_analiz():
    sumo_cfg = os.path.join(project_root, "maltepe.sumocfg")
    checkpoint_path = os.path.join(project_root, "run", "gnn_hybrid_v4")
    
    # 1. Ortam Kaydı (Hata almamak için şart)
    def env_creator(config):
        return raw_env(sumo_cfg_path=sumo_cfg, use_gui=True)
    register_env("multi_agent_traffic_hybrid_v4", env_creator)

    # 2. Model Yükleme (Hafıza ayarlı)
    print("🧠 Yapay Zeka Yükleniyor... Lütfen bekleyin.", flush=True)
    try:
        ray.init(ignore_reinit_error=True, object_store_memory=150 * 1024 * 1024)
        algo = Algorithm.from_checkpoint(checkpoint_path)
    except Exception as e:
        print(f"⚠️ Model yüklenirken hata oluştu, ham simülasyon başlatılıyor: {e}")
        algo = None

    # 3. Simülasyonu Başlat
    print("🚗 SUMO-GUI AÇILIYOR. Lütfen 'Play' tuşuna basın!", flush=True)
    env = raw_env(sumo_cfg_path=sumo_cfg, use_gui=True)
    obs, info = env.reset()
    
    edge_waiting_times = {}
    step = 0
    
    try:
        done = {"__all__": False}
        while not done["__all__"]:
            # Aksiyonları hesapla
            if algo:
                actions = {aid: algo.compute_single_action(o) for aid, o in obs.items()}
            else:
                actions = {} # Model yoksa standart akış
                
            obs, rewards, terminated, truncated, info = env.step(actions)
            done = terminated
            step += 1
            
            # Teknik veri toplama
            current_vehs = traci.vehicle.getIDList()
            for v_id in current_vehs:
                w = traci.vehicle.getWaitingTime(v_id)
                if w > 10: # 10 saniyeden fazla bekleyenler darboğazdır
                    rid = traci.vehicle.getRoadID(v_id)
                    edge_waiting_times[rid] = edge_waiting_times.get(rid, 0) + 1
            
            if step % 100 == 0:
                # En çok bekleme olan yeri anlık söyle
                if edge_waiting_times:
                    top_edge = max(edge_waiting_times, key=edge_waiting_times.get)
                    print(f"⏱️ Sn: {step} | Darboğaz Noktası: {top_edge} | Yoldaki Araç: {len(current_vehs)}", flush=True)

    except Exception as e:
        print(f"Simülasyon Sonu: {e}", flush=True)
    finally:
        env.close()
        ray.shutdown()

if __name__ == "__main__":
    nihai_gorsel_analiz()
