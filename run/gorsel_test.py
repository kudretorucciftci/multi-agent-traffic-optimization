import os
import sys
import numpy as np
import ray
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
import traci
import time
import torch
import sumolib

# Proje kök dizini
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# SUMO_HOME kontrolü
if "SUMO_HOME" not in os.environ:
    os.environ["SUMO_HOME"] = r"C:\Program Files (x86)\Eclipse\Sumo"

# Çoklu ajan ortamını içe aktar
from train.multi_agent_env import raw_env as multi_agent_traffic_raw_env

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

def run_total_smart_simulation(algo, max_steps=20000):
    print(f"\n🌍 TÜM HARİTA AKILLI HALE GETİRİLİYOR (TOTAL OPTIMIZATION)...")
    
    env_config = {"use_gui": True, "max_steps": max_steps, "label": "total_city_test"}
    env = env_creator(env_config)
    obs, info = env.reset()

    # --- TÜM KAVŞAKLARI TARA VE SINIFLANDIR ---
    net = sumolib.net.readNet(os.path.join(project_root, "maltepe.net.xml"))
    tls_agents = list(obs.keys())
    
    vsl_agents = []
    vsl_lane_data = {}
    
    # Haritadaki tüm düğümleri tara (Işık olmayan ama gerçek kavşak olanlar)
    for node in net.getNodes():
        n_id = node.getID()
        # Eğer bu bir trafik ışığı DEĞİLSE ve en az 2 giriş yolu varsa (gerçek kavşaksa)
        if n_id not in tls_agents and len(node.getIncoming()) >= 2:
            vsl_agents.append(n_id)
            lanes = []
            for edge in node.getIncoming():
                e_id = edge.getID()
                for i in range(traci.edge.getLaneNumber(e_id)):
                    l_id = f"{e_id}_{i}"
                    lanes.append((l_id, traci.lane.getMaxSpeed(l_id)))
            vsl_lane_data[n_id] = lanes

    print(f"📊 Toplam Akıllı Sistem: {len(tls_agents)} RL Işık + {len(vsl_agents)} Akıllı Tabela = {len(tls_agents)+len(vsl_agents)} Ajan")

    # --- GÖRSEL ŞÖLEN: GERÇEKÇİ İKONLARLA HARİTAYI İŞARETLE ---
    assets_dir = os.path.join(project_root, "assets")
    tls_icon_path = os.path.join(assets_dir, "tls_icon.png")
    vsl_icon_path = os.path.join(assets_dir, "vsl_sign.png")

    try:
        # RL Işıklar (AI İkonu)
        for aid in tls_agents:
            pos = traci.junction.getPosition(aid)
            # Krem rengi daireyi kaldırdık, yerine şık bir ikon koyuyoruz
            traci.poi.add(f"p_{aid}", pos[0], pos[1], (255,255,255,255), poiType="RL_TLS", layer=101, 
                          imgFile=tls_icon_path, width=12, height=12)
            
        # Akıllı Tabelalar (Hız Tabelası İkonu)
        for aid in vsl_agents:
            pos = traci.junction.getPosition(aid)
            traci.poi.add(f"p_{aid}", pos[0], pos[1], (255,255,255,255), poiType="VSL_SIGN", layer=101, 
                          imgFile=vsl_icon_path, width=10, height=10)

        # Başlangıç Zoom
        traci.gui.setZoom("View #0", 1500)
    except Exception as e:
        print(f"🎨 Görselleştirme yüklenirken hata: {e}")

    step_count = 0
    module = algo.get_module("shared_policy")
    
    try:
        while step_count < max_steps:
            # 1. RL AJANLARI (Trafik Işıkları)
            obs_batch = {"obs": torch.from_numpy(np.stack([obs[aid] for aid in tls_agents])).float()}
            model_out = module.forward_inference(obs_batch)
            action_indices = np.argmax(model_out["action_dist_inputs"].detach().numpy(), axis=1)
            
            actions = {}
            for i, aid in enumerate(tls_agents):
                m_act = env.par_env.action_spaces[aid].n - 1
                actions[aid] = min(int(action_indices[i]), m_act)

            # 2. VSL AJANLARI (Tüm Diğer Kavşaklar - Kural Bazlı Gerçekçi Hız Kontrolü)
            if step_count % 5 == 0:
                for aid in vsl_agents:
                    v_count = sum(traci.lane.getLastStepVehicleNumber(l[0]) for l in vsl_lane_data[aid])
                    
                    # Gerçekçi Hız Kademeleri (Hız Limitine % Bazlı Müdahale)
                    if v_count > 15:   factor = 0.3  # Aşırı Yoğun (Örn: 50 -> 15 km/s)
                    elif v_count > 8:  factor = 0.6  # Yoğun (Örn: 50 -> 30 km/s)
                    elif v_count > 3:  factor = 0.8  # Hafif Yoğun (Örn: 50 -> 40 km/s)
                    else:              factor = 1.0  # Serbest (Yasal Limit)
                    
                    current_kmh = 0
                    for l_id, orig_v in vsl_lane_data[aid]:
                        new_speed = orig_v * factor
                        traci.lane.setMaxSpeed(l_id, new_speed)
                        current_kmh = int(new_speed * 3.6) # Görsel için km/s çevir
                    
                    # GUI Üzerinde Hızı Güncelle
                    try:
                        # İkonun hemen altında/üstünde hızı göster
                        traci.poi.setText(f"p_{aid}", f"{current_kmh} km/h")
                        
                        # Hıza göre renk değiştir (Metin rengi)
                        if factor < 0.5: traci.poi.setColor(f"p_{aid}", (255, 50, 50, 255))
                        elif factor < 0.9: traci.poi.setColor(f"p_{aid}", (255, 255, 0, 255))
                        else: traci.poi.setColor(f"p_{aid}", (100, 255, 100, 255))
                    except: pass

            obs, r, t, tr, i = env.step(actions)
            step_count += 1
            if step_count % 100 == 0:
                print(f"📍 Adım: {step_count} | Sistem %100 Aktif (Maltepe Geneli)")
            
            if all(t.values()) or all(tr.values()): break

    except Exception as e: print(f"⚠️ Hata: {e}")
    finally:
        print("⌛ İnceleme için 60 saniye bekletiliyor...")
        time.sleep(60)
        env.close()

def main():
    ray.init(ignore_reinit_error=True, object_store_memory=150*1024*1024)
    checkpoint_dir = os.path.abspath(os.path.join(project_root, "run", "multi_agent_model"))
    
    config = (
        PPOConfig()
        .environment("multi_agent_traffic_env", env_config={"label": "total_init"})
        .env_runners(num_env_runners=0)
        .training(model={"fcnet_hiddens": [256, 256]})
        .multi_agent(
            policies={"shared_policy"},
            policy_mapping_fn=(lambda aid, *args, **kwargs: "shared_policy")
        )
    )
    
    try:
        algo = config.build()
        algo.restore(checkpoint_dir)
        run_total_smart_simulation(algo)
    except Exception as e: print(f"❌ Hata: {e}"); import traceback; traceback.print_exc()
    finally: ray.shutdown()

if __name__ == "__main__":
    main()
