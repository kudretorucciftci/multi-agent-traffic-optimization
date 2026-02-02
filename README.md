# 🚦 Multi-Agent Traffic Control with Reinforcement Learning

![AI Traffic Banner](project_banner.png)

## 📌 Proje Hakkında
Bu proje, Maltepe bölgesindeki kritik kavşakların (6+ trafik ışığı) koordineli yönetimini sağlamak amacıyla **SUMO (Simulation of Urban MObility)** ve **Ray RLlib / PettingZoo** altyapısını kullanır. Derin Pekiştirmeli Öğrenme (MAPPO/PPO) algoritmaları ile trafik akışı dinamik olarak optimize edilir.

### 🎬 Simülasyon Canlı Akışı
![SUMO Simulation Overview](simulation.gif)
*Sistem, araç yoğunluğunu gerçek zamanlı analiz ederek faz geçişlerini optimize eder.*

## 🚀 Öne Çıkan Özellikler
- **Knowledge Graph Duyarlılığı:** Ajanlar sadece kendi kavşaklarını değil, komşu kavşakların durumunu da gözlemleyerek koordineli kararlar alır.
- **Dinamik Ödül Mekanizması:** Bekleme süresi ve durma sayısını minimize eden gelişmiş ödül fonksiyonu.
- **Gerçekçi Simülasyon:** Maltepe bölgesinin gerçek OSM (OpenStreetMap) verileri üzerine kurulmuş trafik ağı.
- **Sarı Işık Yönetimi:** Gerçek dünya güvenliği için otomatik sarı ışık faz entegrasyonu.

## 📁 Klasör Yapısı
```
├── train/                  # Eğitim mantığı ve Ortam (Env) tanımları
│   ├── multi_agent_env.py  # PettingZoo tabanlı çoklu ajan ortamı
│   └── train_multi_agent.py # Ray RLlib eğitim scripti
├── run/                    # Test ve Görselleştirme
│   ├── run_trained_model.py # Eğitilmiş modeli çalıştırma
│   └── trafik_analiz.png    # Performans metrik grafikleri
├── sumo_files/             # SUMO ağ ve rota dosyaları
└── training_metrics.csv    # Eğitim süreci logları
```

## 🛠️ Kurulum ve Çalıştırma

### 1. Gereksinimler
- SUMO (v1.18.0 veya üzeri)
- Python 3.9+
- Ray [RLlib], PettingZoo, Gymnasium

### 2. Kurulum
```bash
pip install -r requirements.txt
```

### 3. Modeli Test Etme
Eğitilmiş modeli GUI ile izlemek için:
```bash
python run/run_trained_model.py
```

## 📊 Eğitim Analizi
Proje kapsamında yapılan denemelerde ödül fonksiyonu stabil bir iyileşme göstermektedir. Knowledge Graph yapısına geçişle birlikte %20'den fazla verimlilik artışı hedeflenmektedir.

---
*Bu proje, zeki ulaşım sistemleri (ITS) araştırmaları kapsamında geliştirilmektedir.*

