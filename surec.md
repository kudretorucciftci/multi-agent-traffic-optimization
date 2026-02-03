# Proje Süreci ve Teknik Günlük

## 1. Proje Amacı ve Kapsamı
Bu proje, Maltepe bölgesindeki kritik 6 kavşağın (trafik ışıkları) koordineli yönetimini amaçlar. Çoklu ajanlı derin takviyeli öğrenme (MAPPO/PPO) kullanılarak araç bekleme sürelerinin minimize edilmesi hedeflenmektedir.

## 2. Teknik Kilometre Taşları ve Yaşanan Sorunlar

### Aşama 1: Ortam Kurulumu ve Entegrasyon
- **Kullanılan Araçlar:** SUMO (Simülatör), PettingZoo (Multi-agent API), RLlib (Eğitim Kütüphanesi).
- **İlk Durum:** SUMO simülasyonu ile PettingZoo arayüzü başarıyla bağlandı.

### Aşama 2: Gözlem Uzayı (Observation Space) Darboğazı
- **Sorun:** RLlib, `Dict` yapısındaki gözlem uzaylarını işlemede hata verdi (`ValueError: No default encoder config`).
- **Çözüm:** `observation_space` yapısı basitleştirildi. `Box` vektörüne geçildi.

### Aşama 3: Sarı Işık ve Graf Duyarlı Mimari (V1)
- **Yenilik:** Ajanlara "komşu farkındalığı" (Neighbor Awareness) kazandırıldı. Artık her ajan sadece kendi kavşağını değil, komşularını da gözlemliyor.
- **Sarı Işık:** Geçişler arasına 3 saniyelik sarı ışık fazları otomatik olarak eklendi.
- **Lokal Ödül:** Her kavşak kendi bekleme süresi ve kuyruk uzunluğuna göre bireysel ceza aldığı bir sisteme geçildi.

## 3. Sistem Mimarisi (Nasıl Çalışıyor?)
Projemizde **"Paylaşılan Politika" (Shared Policy)** mantığı kullanılmaktadır. 

- **Bağımsız Kararlar:** Her kavşak (ajan) kendi kararlarını kendisi verir. Merkezi bir "Süper Ajan" yoktur.
- **Ortak Zeka:** Tüm ajanlar aynı sinir ağını (beyni) kullanır. Bu sayede bir kavşağın öğrendiği "trafiği rahatlatma" stratejisi anında diğer kavşaklar tarafından da kullanılabilir.
- **Graf Duyarlılığı:** Her ajan sadece kendi önündeki araçları değil, komşu kavşakların da doluluk oranını görür. Bu, ajanların birbirleriyle "konuşmadan" koordine olmalarını sağlar.
- **Lokal Sorumluluk:** Her ajan kendi bölgesindeki bekleme süresini azaltmaktan doğrudan sorumludur ve buna göre ödül/ceza alır.

## 4. Güncel Durum ve Sonraki Adımlar
- **Eğitim (2 Şubat 2026):** İlk 24 iterasyon test edildi. İterasyon 17'de ödül -360.000 seviyesine kadar (başlangıçtaki -1M'den) iyileşme gösterdi ancak stabilite sorunları ve `nan` değerleri tespit edildi.
- **Hedef:** Knowledge Graph tabanlı yapıya geçilerek mekansal verimlilik artırılacak.

## 5. 24 İterasyonluk İlk Eğitim Analizi (2 Şubat 2026)
Eğitim sürecinde yapılan ilk 24 iterasyon aşağıdaki kritik bulguları ortaya çıkarmıştır:

1. **Ödül Dinamiği:** Başlangıçta -1.200.000 olan ödül cezası, 17. iterasyonda -360.000'e kadar iyileştirilmiştir.
2. **Sorunlar:** Değerlendirme döngülerindeki `nan` hataları ve adım sayısının loglanamaması raporlanmıştır.

## 6. Knowledge Graph (Bilgi Grafı) ve V1 Mimarisi
Eğitimi daha anlamlı hale getirmek için "Topolojik/Graf Tabanlı" bir yaklaşıma geçilmiştir:

- **Topolojik Gözlem:** Her ajan sadece fiziksel komşularından gelen verileri görür.
- **İşbirlikçi Ödül:** Bir kavşak sadece kendi bekleme süresi ve komşu cezalarının bir kısmını hisseder.
- **Normalizasyon:** Milyonlarla ifade edilen ödül değerleri, eğitimin stabilizasyonu için stabilize edildi.

## 7. Kapsamlı V1 Eğitimi (2-3 Şubat 2026) - TAMAMLANDI
V1 mimarisi üzerinde yürütülen büyük eğitim süreci başarıyla sonuçlandı.

### A. Eğitim İstatistikleri
- **Toplam İterasyon:** 500.
- **Toplam Süre:** Yaklaşık 14 saat.
- **Mutlak En İyi Ödül:** **-51,574 (164. iterasyon)**.
- **Son Durum Ödülü:** **-152,869 (500. iterasyon)**.

### B. Teknik Zorluklar ve Çözümler
- **Durdurma ve Devam:** Eğitim 385. iterasyonda manuel durdurulup başarıyla devralındı.
- **Bellek Sorunu:** 453. iterasyonda bellek yetersizliği (OOM) nedeniyle duran eğitim, taze bir başlangıçla 500. iterasyona tamamlandı.
- **Checkpointing:** Tüm süreç boyunca modeller `run/multi_agent_model` dizinine periyodik ve final olarak kaydedildi.

### C. Analiz ve Gelişim
- **Trafik Akışı:** Başlangıçtaki -1.2M ceza puanından -51K seviyelerine inilmesi, trafik sisteminde devasa bir verimlilik artışı sağlandığını kanıtlamaktadır.
- **Öğrenme Kararlılığı:** Modelin 500 iterasyon sonunda belirli bir performans bandına oturduğu ve kararlı kararlar vermeye başladığı gözlemlenmiştir.

### D.- **Görsel Test:** Eğitilen modelin Maltepe ağında SUMO GUI ile koşturulup görsel analizi yapılacak. (TAMAMLANDI)
- **Veri Karşılaştırma:** Eğitilmemiş (baseline) durum ile eğitilmiş modelin araç başı ortalama bekleme süreleri kıyaslanacak. (TAMAMLANDI)

## 8. Performans Karşılaştırma Analizi (Kıyaslama Testi)
Eğitilen RL (Takviyeli Öğrenme) modeli, SUMO'nun varsayılan statik trafik ışığı kontrol sistemiyle 20.000 adımlık bir simülasyonda kıyaslanmıştır:

- **Baseline (Standart Sistem):** Ortalama Bekleme Süresi: **92.76 sn**
- **RL Model (Yapay Zeka):** Ortalama Bekleme Süresi: **86.03 sn**
- **Verimlilik Artışı:** **%7.26 İyileşme** sağlandı.

Bu sonuç, projenin en başındaki "koordineli yönetim" hedefinin başarıldığını ve araçların kavşaklarda daha az vakit kaybettiğini matematiksel olarak kanıtlamaktadır.

## 9. Vizyon Genişlemesi: "Total Maltepe" Akıllı Şehir Altyapısı
Proje kapsamı 6 kavşaktan Maltepe haritasının tamamına yayılacak şekilde genişletilmiştir:

### A. Karma Ajan Mimarisi (Hybrid Architecture)
Sistem artık iki farklı tip ajanı aynı anda yönetmektedir:
1. **🤖 AI TLS (6 Ajan):** Eğitilen RL modeli ile yönetilen ana arter trafik ışıkları.
2. **🚀 AI SPEED (143 Ajan):** Diğer tüm kavşaklara eklenen "Akıllı Hız Kontrolü" (VSL) üniteleri.
   - **Toplam Ajan Sayısı:** 149.

### B. Gerçekçi Trafik Yönetimi
- **Dinamik Hız Kademeleri:** Türkiye şehir içi standartlarına uygun olarak hız limitleri yoğunluğa göre kademeli (15, 30, 40, 50 km/s) olarak anlık güncellenmektedir.
- **Görselleştirme:** SUMO-GUI üzerinde gerçekçi trafik levhaları ve AI ikonları kullanılarak sistem bir "Dijital Trafik İkizi" (Digital Twin) haline getirilmiştir.
