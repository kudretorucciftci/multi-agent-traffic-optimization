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

1. **Ödül Dinamiği:** Başlangıçta -1.200.000 olan ödül cezası, 17. iterasyonda -360.000'e kadar iyileşmiştir. Bu, modelin temel trafik kurallarını öğrenmeye başladığının kanıtıdır.
2. **Nan Hatası:** Değerlendirme (Evaluation) adımlarından hemen sonra (her 5 iterasyonda bir) ödüllerin `nan` değerine düşmesi, değerlendirme konfigürasyonunda veya simülasyonun yeniden başlatılma sürecinde bir çakışma olduğunu göstermektedir.
3. **Metrik Sorunu:** "Toplam Adım" sayısının 0 olarak kaydedilmesi, RLlib'in adımları düzgün loglayamadığını işaret etmektedir.

## 6. Knowledge Graph (Bilgi Grafı) ve Gelecek Planı
Eğitimi daha anlamlı ve ölçeklenebilir hale getirmek için "Topolojik/Graf Tabanlı" bir yaklaşıma geçilmesine karar verilmiştir:

### A. Topolojik Gözlem (Topology-Aware Observation)
- **Mevcut:** Her ajan tüm haritadaki tüm ajanların verisini görüyordu (Gürültülü veri).
- **Yeni:** Her ajan sadece **fiziksel komşularından** gelen verileri görecek. Bu, Knowledge Graph yapısının temelini oluşturur. Ajanlar gereksiz veriden kurtulup sadece kendilerini etkileyen trafiğe odaklanacak.

### B. İşbirlikçi Ödül (Cooperative Reward)
- **Mantık:** Bir kavşak sadece kendi bekleme süresini değil, kendisine araç gönderen komşularının zor durumlarını da "hissedecek".
- **Hedef:** Bencil kavşak yönetiminden, koridor bazlı koordineli yönetime geçiş.

### C. Teknik İyileştirmeler
- **Hata Giderme:** `nan` değerlerine sebep olan değerlendirme döngüsü optimize edilecek.
- **Normalizasyon:** Milyonlarla ifade edilen ödül değerleri, eğitimin daha hızlı yakınsaması için normalize edilecek.
