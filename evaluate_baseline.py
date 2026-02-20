import os
import sys
import traci
import pandas as pd
import time
import numpy as np

def run_baseline_evaluation():
    print("🚀 Yapay Zekasız (Statik) Baseline Simülasyonu Başlatılıyor...")
    print("ℹ️ Bu modda trafik ışıkları SUMO'nun varsayılan statik sürelerini kullanacaktır.")

    sumo_binary = "sumo-gui" # Görsel görmek için gui, hız için sumo seçilebilir
    sumo_cmd = [sumo_binary, "-c", "maltepe.sumocfg", "--start", "--quit-on-end", "--no-warnings"]

    traci.start(sumo_cmd)
    
    metrics_list = []
    step_count = 0
    start_time = time.time()

    # Işıklı kavşakları ve yollarını belirle (Metrik tutarlılığı için)
    tls_ids = traci.trafficlight.getIDList()

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            
            active_vehicles = traci.simulation.getMinExpectedNumber()
            
            # evaluate_full_drain.py ile aynı metrik toplama mantığı
            total_waiting_time = sum(traci.vehicle.getWaitingTime(v) for v in traci.vehicle.getIDList())
            total_halting_vehicles = sum(1 for v in traci.vehicle.getIDList() if traci.vehicle.getSpeed(v) < 0.1)
            
            speeds = [traci.vehicle.getSpeed(v) for v in traci.vehicle.getIDList()]
            mean_speed = np.mean(speeds) if speeds else 0
            
            metrics_list.append({
                "step": step_count,
                "active_vehicles": active_vehicles,
                "waiting_time": total_waiting_time,
                "halting": total_halting_vehicles,
                "speed": mean_speed
            })
            
            step_count += 1
            if step_count % 100 == 0:
                print(f"B-Adım: {step_count} | Kalan Araç: {active_vehicles} | Toplam Bekleme: {total_waiting_time:.1f}")
            
            # Güvenlik sınırı (Statik sistem kilitlenirse çok uzayabilir)
            if step_count >= 20000:
                print("\n⚠️ 20.000 adıma ulaşıldı. Statik sistem muhtemelen kilitlendi (Gridlock).")
                break
                
    except Exception as e:
        print(f"\n🛑 Hata: {e}")
    finally:
        if metrics_list:
            df = pd.DataFrame(metrics_list)
            df.to_csv("baseline_5000_metrics.csv", index=False)
            print(f"\n✅ BASELINE VERİLERİ KAYDEDİLDİ: 'baseline_5000_metrics.csv'")
            print(f"Toplam Simülasyon Süresi: {step_count} saniye")
            
        traci.close()

if __name__ == "__main__":
    run_baseline_evaluation()
