# 🚦 Maltepe Digital Twin: Hybrid Multi-Agent Traffic Control

![Simulation Output](assets/simulation.gif)

Bu proje, İstanbul Maltepe bölgesinin trafik akışını **Hybrid Multi-Agent Systems (MAS)** ve **Knowledge Graph** topolojisi kullanarak optimize eden ileri seviye bir **Deep Reinforcement Learning** çözümüdür.

## 🧠 System Architecture & Hybrid MAS

Sistem, şehir ölçeğinde bir koordinasyon sağlamak için iki farklı **Agent** tipini birleştiren hibrit bir mimari kullanır:

1.  **Learning Agents (6 RL Agents):** Ana arterlerdeki trafik ışıklarını (TLS) kontrol eden, **MAPPO (Multi-Agent PPO)** algoritması ile eğitilmiş zekalar.
2.  **Supportive Agents (143 Rule-based Agents):** Kavşak girişlerinde konumlandırılan ve **Variable Speed Limit (VSL)** kurallarıyla trafik akışını Learning Agent'lar için stabilize eden yardımcı birimler.
3.  **Knowledge Graph Topology:** Agent'lar sadece kendi bölgelerini değil, Knowledge Graph üzerinden tanımlanan komşuluk ilişkileri sayesinde **Spatial Awareness** (mekansal farkındalık) ile hareket eder. Bir bölgedeki yoğunluk, grafik yapısı üzerinden diğer agent'lara veri olarak aktarılır.

## 🚀 Training & Fine-tuning Process

Modelin başarısı, aşamalı bir eğitim stratejisiyle (Curriculum Learning benzeri) elde edilmiştir:

-   **Base Training (500 Iterations):** 6 ana agent için temel trafik yönetim politikaları ve Knowledge Graph entegrasyonu sağlandı.
-   **Fine-tuning V4 (200 Iterations):** Hibrit yapının (149 Agents) devreye alınmasıyla, ödül fonksiyonu (Reward Function) kararlılığı üzerinde ince ayar (Fine-tuning) yapıldı.
-   **Toplam İlerleme:** Başlangıçta **-245.000** seviyesinde olan kümülatif **Reward**, Fine-tuning sonunda **-24.769** bandına çekilerek sistem doyuma (Plateau) ulaştırıldı.

## 📉 Benchmarking Results

Sistemin başarısı 3 farklı senaryoda sayısal olarak kanıtlanmıştır:

| Metrics | **Static (No AI)** | **6 RL Agents (MLP)** | **Final Hybrid (GNN/VSL)** |
| :--- | :--- | :--- | :--- |
| **System Reward Score** | -245.000 | -182.014 | **-24.769** |
| **Avg. Waiting Time** | 240+ sec | 158 sec | **32 sec** |
| **Throughput (Veh/Hr)** | 450 | 720 | **1.280** |
| **Gridlock Probability** | %95 | %40 | **<%2** |

## 🛠️ Commands & Usage

1.  **Install Requirements:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run Visual Simulation:**
    ```bash
    python run/run_simulation.py
    ```
3.  **Monitor with Tensorboard:**
    ```bash
    tensorboard --logdir ppo_trafik_isigi_tensorboard
    ```

---
*Developed by: [Kudret Oruç Çiftçi / Multi-Agent Traffic Optimization]*
