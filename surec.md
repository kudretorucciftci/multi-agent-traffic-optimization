# Ar-Ge Süreci ve Teknik Gelişim Günlüğü

Bu proje, basit bir trafik ışığı kontrolünden, şehir ölçeğinde bir **Digital Twin** yapısına evrilen karmaşık bir mühendislik sürecidir. İşte bu süreçte karşılaşılan teknik engeller ve uygulanan mimari çözümler:

## 1. Mimari Dönüşüm: MLP'den Knowledge Graph'e

Projenin ilk aşamalarında kullanılan standart **MLP (Multi-Layer Perceptron)** tabanlı yapıda, her kavşağın (Agent) izole bir şekilde karar verdiği gözlemlendi. Bu durum, kavşakların birbirini beklemesine ve simülasyonun kilitlenmesine neden oluyordu.

- **Çözüm:** **Knowledge Graph** topolojisine geçilerek agent'lara komşu farkındalığı (**Spatial Awareness**) kazandırıldı. Agent'lar artık "Common Knowledge" paylaşımı yaparak trafiği ortak bir stratejiyle yönetmeye başladı.

## 2. Karşılaşılan Teknik "Challenges" ve Çözümleri

### Gözlem Uzayı (Observation Space) Uyumsuzluğu
- **Sorun:** RLlib kütüphanesinin karmaşık `Dict` yapılarını işlerken ortaya çıkardığı kısıtlamalar, eğitimin başlamasını engelledi.
- **Çözüm:** Observation verileri normalize edilip `Box` vektörlerine dönüştürülerek model stabilitesi artırıldı.

### NaN (Not a Number) ve Sayısal Dalgalanmalar
- **Sorun:** Ödül fonksiyonundaki (Reward Function) kümülatif beklemelerin devasa boyutlara ulaşması matematiksel taşmalara ve modelin öğrenememesine neden oldu.
- **Çözüm:** `np.nan_to_num` kullanımı ve ödül skalasının **Normalization** işlemine tabi tutulmasıyla eğitim kararlı hale getirildi.

### Sistem Kaynakları ve OOM (Out Of Memory) Hataları
- **Sorun:** Büyük harita (Maltepe) ve 149 ajanın aynı anda işlenmesi sırasında CPU/RAM üzerinde darboğazlar yaşandı, eğitimler kesildi.
- **Çözüm:** Aşamalı **Checkpointing** sistemine geçildi ve Ray konfigürasyonundaki `object_store_memory` limitleri optimize edilerek eğitimin kaldığı yerden devam etmesi sağlandı.

## 3. Hibrit V4 ve Fine-tuning Stratejisi

- Sadece trafik ışıklarını eğitmenin yetersiz kaldığı "Pik Yoğunluk" senaryolarında, 143 adet **Variable Speed Limit (VSL)** tabanlı kural-tabanlı ajan sisteme entegre edildi.
- **Hybrid MAS** yapısı kurulduktan sonra, sistem 500 iterasyonluk temel eğitimin üzerine 200 iterasyonluk bir **Fine-tuning** sürecine sokuldu.
- Bu strateji, Learning Agent'lar için "gürültüsüz" (Noise-free) bir trafik akışı yaratarak sistem başarısını en üst seviyeye çıkardı.

## 4. Final Vizyonu

Süreç sonunda elde edilen model, sadece teknik bir başarı değil, gerçek şehir trafiğinin bir **Digital Twin** yansıması olarak başarıyla çalışmaktadır. GNN-Hybrid yaklaşımı, Maltepe ağındaki seyahat sürelerini minimize ederken karbon emisyonunu da dolaylı olarak azaltmayı başarmıştır.
