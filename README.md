# 🚦 Maltepe Digital Twin: Hybrid Multi-Agent Traffic Control

![Simulation Output](assets/simulation.gif)

Bu proje, İstanbul Maltepe bölgesinin trafik akışını **Hybrid Multi-Agent Systems (MAS)** ve **Knowledge Graph** topolojisi kullanarak optimize eden ileri seviye bir **Deep Reinforcement Learning** çözümüdür.

## 🚀 Başarı Metrikleri (Benchmark Analizi)

Sistemimiz evrimsel olarak 3 aşamada test edilmiş ve her aşamada zekasını katlamıştır:

| Performans Metriği | **Statik (Zekasız)** | **6 Ajanlı (MLP)** | **Hibrit GNN (149 Ajan)** | **İyileşme Oranı** |
| :--- | :--- | :--- | :--- | :--- |
| **Sistem Başarı Skoru (Reward)** | -245.000 | -182.014 | **-24.769** | **%86.4 Artış** |
| **Ortalama Bekleme Süresi** | 240+ sn | 158 sn | **32 sn** | **4.9 Kat Daha Hızlı** |
| **Trafik Tahliye Süresi** (1.000 Araç) | 120+ Dakika | 75 Dakika | **46 Dakika** | **%61 Verimlilik** |
| **Kilitlenme Riski** | %95 | %40 | **<%2** | **Sıfır Tıkanıklık** |

## 🧠 Geliştirme ve Simülasyon Ortamı

Projenin geliştirme ve test süreçleri iki ana fazda yürütülmüştür:

### 1. Training & Fine-tuning Environment (Kaggle)
Modelin eğitimi ve parametre optimizasyonu için yüksek işlem gücü gerektiren **Kaggle** bulut altyapısı kullanılmıştır. Özellikle 149 ajanın eş zamanlı eğitildiği GNN tabanlı yapılarda Kaggle üzerindeki GPU/TPU desteğiyle model stabilizasyonu sağlanmıştır. Toplamda 700+ iterasyonluk eğitim süreci burada tamamlanmıştır.

### 2. Simulation & Production Environment (SUMO)
Eğitilen modeller, Maltepe bölgesinin birebir dijital haritasının (Digital Twin) bulunduğu **SUMO (Simulation of Urban MObility)** ortamında test edilmiştir. Bu ortamda hibrit ajanların (Learning & Rule-based) dinamik trafikteki tepkileri saniye saniye izlenmiş ve verify edilmiştir.

## ⚙️ Hybrid MAS Architecture

Sistem, şehir ölçeğinde bir koordinasyon sağlamak için iki farklı **Agent** tipini birleştirir:

-   **Learning Agents (6 RL Agents):** Ana arterlerdeki trafik ışıklarını (TLS) kontrol eden ana zekalar.
-   **Supportive Agents (143 Rule-based Agents):** **Knowledge Graph** üzerinden gelen verilerle **Variable Speed Limit (VSL)** kuralları uygulayan yardımcı ajanlar.
-   **Knowledge Graph Topology:** Agent'lar sadece kendi bölgelerini değil, grafik yapısı üzerinden tanımlanan komşuluk ilişkileri sayesinde **Spatial Awareness** ile hareket eder.

## 🛠️ Kullanım Komutları

1.  **Gereksinimleri Yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Simülasyonu Başlatın (Görsel):**
    ```bash
    python run/run_simulation.py
    ```
3.  **Eğitimi Takip Edin (Tensorboard):**
    ```bash
    tensorboard --logdir ppo_trafik_isigi_tensorboard
    ```

---
*Multi-Agent Traffic Control Framework*
