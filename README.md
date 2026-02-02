# SUMO ve Derin Pekiştirmeli Öğrenme ile Trafik Işığı Kontrolü

Bu proje, SUMO trafik simülasyonu ve Derin Pekiştirmeli Öğrenme (Deep Reinforcement Learning) kullanarak trafik ışıklarını otomatik olarak kontrol eden bir yapay zeka ajanı içermektedir.

## Projenin Amacı

Bu projenin amacı, trafik ışıklarını optimize ederek araçların ortalama bekleme süresini azaltmak ve trafik akışını iyileştirmektir. Proximal Policy Optimization (PPO) algoritması kullanılarak eğitilen bir yapay zeka ajanı, trafik ışıklarının zamanlamasını dinamik olarak ayarlar.

## Klasör Yapısı

```
├── README.md                   # Proje açıklaması ve kullanım talimatları
├── network.net.xml             # SUMO ağ dosyası (kavşak yapısı)
├── routes.rou.xml              # SUMO trafik akış dosyası
├── sumo.sumocfg                # SUMO konfigürasyon dosyası
├── train/                      # Eğitim ile ilgili dosyalar
│   └── trafik_isiklari_drl.py  # Eğitim kodu ve ortam tanımı
└── run/                        # Çalıştırma ile ilgili dosyalar
    ├── run_trained_model.py    # Eğitilmiş modeli çalıştırma kodu
    └── trafik_isigi_ppo_model.zip # Eğitilmiş model dosyası
```

## Kurulum Talimatları

### 1. SUMO Kurulumu

- SUMO'yu [resmi web sitesinden](https://www.eclipse.org/sumo/) indirin ve kurun
- Kurulum sırasında 'Add SUMO to PATH' seçeneğini işaretleyin
- Kurulumu doğrulamak için komut satırında `sumo --version` komutunu çalıştırın

### 2. Python Kütüphanelerinin Kurulumu

```bash
pip install gymnasium numpy matplotlib stable-baselines3 sumolib traci
```

## Kullanım

### Modeli Eğitme

1. `train` klasöründeki `trafik_isiklari_drl.py` dosyasını çalıştırın:

```bash
python train/trafik_isiklari_drl.py
```

2. Eğitim tamamlandığında, model `train/trafik_isigi_ppo_model.zip` olarak kaydedilecektir.

### Eğitilmiş Modeli Çalıştırma

1. `run` klasöründeki `run_trained_model.py` dosyasını çalıştırın:

```bash
python run/run_trained_model.py
```

2. SUMO-GUI otomatik olarak başlayacak ve eğitilmiş model trafik ışıklarını kontrol edecektir.
3. Simülasyon tamamlandığında, sonuçlar grafikler halinde gösterilecektir.

## Geliştirici Notları

### SUMO-GUI Ayarları ve 2D Görünüm İyileştirmeleri

SUMO-GUI başlatıldığında aşağıdaki iyileştirmeler otomatik olarak uygulanır:

- Pencere maksimum boyuta ayarlanır
- Araç renkleri daha belirgin hale getirilir
- Trafik ışıklarının adları gösterilir
- Araçların anlık hızları gösterilir

Simülasyon sırasında konsolda aşağıdaki bilgiler gerçek zamanlı olarak gösterilir:

- Simülasyon adımı
- Toplam araç sayısı
- Ortalama bekleme süresi

### SUMO Yolu Ayarı

Eğer SUMO farklı bir konuma kurulmuşsa, `train/trafik_isiklari_drl.py` ve `run/run_trained_model.py` dosyalarındaki aşağıdaki satırı değiştirin:

```python
os.environ["SUMO_HOME"] = r"C:\Program Files (x86)\Eclipse\Sumo"
```

