# Proje Süreci ve Teknik Günlük

## 1. Proje Amacı ve Kapsamı
Bu proje, Maltepe bölgesindeki kritik 6 kavşağın (trafik ışıkları) koordineli yönetimini amaçlar. Çoklu ajanlı derin takviyeli öğrenme (MAPPO/PPO) kullanılarak araç bekleme sürelerinin minimize edilmesi hedeflenmektedir.

## 2. Teknik Kilometre Taşları ve Yaşanan Sorunlar

### Aşama 1: Ortam Kurulumu ve Entegrasyon
- **Kullanılan Araçlar:** SUMO (Simülatör), PettingZoo (Multi-agent API), RLlib (Eğitim Kütüphanesi).
- **İlk Durum:** SUMO simülasyonu ile PettingZoo arayüzü başarıyla bağlandı.

### Aşama 2: Gözlem Uzayı (Observation Space) Darboğazı
- **Sorun:** RLlib, `Dict` yapısındaki gözlem uzaylarını (her ajan için ayrı sözlük) varsayılan model mimarisi ile işlemede hata verdi (`ValueError: No default encoder config`).
- **Analiz:** RLlib'in yeni API'leri, karmaşık sözlük yapılarını otomatik olarak vektörleştirmekte sorun yaşıyordu.
- **Çözüm:** `multi_agent_env.py` içinde `observation_space` yapısı basitleştirildi. Ajanların gözlemleri tek bir `Box` vektöründe (6 kavşak için 6 birimlik vektör) birleştirildi. Bu sayede teknik uyumsuzluk aşıldı ve eğitim başlatılabildi.

### Aşama 3: Ödül (Reward) Mekanizması ve Eğitim Kararlılığı
- **Sorun:** Eğitim sırasında ödüllerin toplanması ve ajanlara dağıtılmasında tutarsızlıklar (0.0 ödül sorunu) görüldü.
- **Çözüm:** `ParallelPettingZooEnv` sarmalayıcısı optimize edildi. Bekleme süresine dayalı global ödül mekanizması, `step` fonksiyonu içinde doğrudan adım bazlı döndürülecek şekilde güncellendi.

## 3. Güncel Durum ve Sonraki Adımlar
- **Mevcut Yapı:** 6 ajanlı, paylaşılan politikaya sahip, vektörel gözlem uzayı kullanan stabil bir model mimarisi.
- **Odak Noktası:** Ödül fonksiyonunun daha hassas hale getirilmesi ve ajanların bireysel katkılarının (lokal ödüller) modele daha iyi yansıtılması.
