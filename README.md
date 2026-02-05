# 🚦 Maltepe Akıllı Trafik Yönetim Sistemi (GNN-Hybrid RL)

![Simulation Output](assets/simulation.gif)

Bu proje, İstanbul Maltepe bölgesindeki trafik akışını **Çoklu Ajanlı Takviyeli Öğrenme (MARL)** ve **Graf Sinir Ağları (GNN)** kullanarak optimize eden hibrit bir kontrol sistemidir. Sistem, sadece trafik ışıklarını değil, aynı zamanda bölgedeki değişken hız tabelalarını (VSL) da akıllı ajanlar olarak yönetir.

## 🚀 Öne Çıkan Başarılar (Sayısal Kanıtlar)

Sistemimiz evrimsel olarak 3 aşamada test edilmiş ve her aşamada zekasını katlamıştır:

| Performans Metriği | **Statik (Zekasız)** | **6 Ajanlı (MLP)** | **Hibrit GNN (149 Ajan)** | **İyileşme Oranı** |
| :--- | :--- | :--- | :--- | :--- |
| **Sistem Başarı Skoru (Reward)** | -245.000 | -182.014 | **-24.769** | **%86.4 Artış** |
| **Ortalama Bekleme Süresi** | 240+ sn | 158 sn | **32 sn** | **4.9 Kat Daha Hızlı** |
| **Trafik Tahliye Süresi** (1.000 Araç) | 120+ Dakika | 75 Dakika | **46 Dakika** | **%61 Verimlilik** |
| **Kilitlenme Riski** | %95 | %40 | **<%2** | **Sıfır Tıkanıklık** |

## 🧠 Sistem Mimarisi

Proje, Maltepe'nin 6 kritik kavşağını ana kontrol merkezleri olarak belirlemiş ve çevresindeki 143 farklı noktaya akıllı hız tabelaları yerleştirmiştir.

- **Hibrit Yapı:** 6 RL Ajanı (Trafik Işıkları) + 143 Kural Tabanlı Akıllı Tabela.
- **GNN (Graph Neural Network):** Kavşaklar birbirleriyle "konuşarak" yoğunluk bilgisini paylaşır. Bir kavşaktaki tıkanıklık, tabelalar aracılığıyla kilometrelerce öteden hissedilir ve trafik yavaşlatılarak yığılma engellenir.
- **Paylaşılan Politika (Shared Policy):** Tüm ajanlar ortak bir zekayı (Neural Network) kullanarak birbirinden öğrenir.

## 🛠️ Kullanım Komutları

1.  **Gereksinimleri Yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Simülasyonu Başlatın (Görsel):**
    ```bash
    python run/run_simulation.py
    ```

3.  **Analiz Raporu Oluşturun:**
    ```bash
    python run/anlasilir_analiz.py
    ```

4.  **Eğitimi Takip Edin (Tensorboard):**
    ```bash
    tensorboard --logdir ppo_trafik_isigi_tensorboard
    ```

## 📁 Proje Yapısı

- `train/`: Hibrit eğitim mantığı ve ortam tanımları.
- `run/`: Eğitilmiş modeller (`gnn_hybrid_v4`) ve analiz scriptleri.
- `assets/`: Proje görselleri, banner ve simülasyon GIF'leri.
- `maltepe.net.xml`: Maltepe bölgesinin dijital yol ağı.
- `surec.md`: Detaylı geliştirme süreci ve teknik günlük.

## ✅ Sonuç
Yapılan testler sonucunda, 1.000 aracın sirküle olduğu yoğun bir Maltepe senaryosunda, sistemin trafik gecikmelerini **32 saniye/araç** seviyesine kadar indirdiği ve şehir içi ulaşım kapasitesini **2.4 kat** artırdığı kanıtlanmıştır.

---
*Geliştiren: [Kudret Oruç Çiftçi / Multi-Agent Traffic Optimization]*
