# Ar-Ge Süreci ve Teknik Gelişim Günlüğü

Bu çalışma, basit bir trafik ışığı kontrolünden, şehir ölçeğinde bir **Digital Twin** yapısına evrilen karmaşık bir mühendislik sürecidir. Sadece kodlama değil, bulut tabanlı yüksek başarımlı hesaplama (Kaggle) ve hibrit yapay zeka mimarilerinin harmanlandığı bir süreçtir.

## 1. Geliştirme Ortamı: Kaggle Cloud Computing

Büyük ölçekli (149 Ajanlı) bir sistemin eğitimi, yerel kaynakların (CPU/RAM) sınırlarını zorladığı için eğitim süreci bütünüyle buluta taşınmıştır.
- **Parametre Optimizasyonu:** **Kaggle** ortamında yüksek paralel işlem gücü kullanılarak agent'ların gözlem uzayları ve ödül katsayıları optimize edilmiştir.
- **Scalability:** Kaggle altyapısı sayesinde, ajan sayısının artırılması (6'dan 149'a) ve eğitim döngülerinin 700+ iterasyona çıkarılması mümkün olmuştur.

## 2. Mimari Dönüşüm: MLP'den Knowledge Graph'e

Projenin ilk aşamalarında kullanılan standart **MLP (Multi-Layer Perceptron)** tabanlı yapıda, her kavşağın (Agent) izole bir şekilde karar verdiği gözlemlendi.
- **Çözüm:** **Knowledge Graph** topolojisine geçilerek agent'lara komşu farkındalığı (**Spatial Awareness**) kazandırıldı. Agent'lar artık "Common Knowledge" paylaşımı yaparak trafiği ortak bir stratejiyle yönetmeye başladı.

## 3. Karşılaşılan Teknik "Challenges" ve Çözümleri

### Gözlem Uzayı (Observation Space) Uyumsuzluğu
- **Sorun:** RLlib kütüphanesinin karmaşık `Dict` yapılarını işlerken ortaya çıkardığı kısıtlamalar, eğitimin başlamasını engelledi.
- **Çözüm:** Observation verileri normalize edilip `Box` vektörlerine dönüştürülerek model stabilitesi artırıldı.

### NaN (Not a Number) ve Sayısal Dalgalanmalar
- **Sorun:** Ödül fonksiyonundaki (Reward Function) kümülatif beklemelerin devasa boyutlara ulaşması matematiksel taşmalara neden oldu.
- **Çözüm:** `np.nan_to_num` kullanımı ve ödül skalasının **Normalization** işlemine tabi tutulmasıyla eğitim kararlı hale getirildi.

## 4. Fine-tuning ve Hibrit Optimizasyon

Temel eğitim (Base Training) tamamlandıktan sonra, sistemin gerçek dünya şartlarına uyumu için özel bir **Fine-tuning** fazına geçilmiştir:
- 143 adet **Variable Speed Limit (VSL)** tabanlı kural-tabanlı ajan, Learning Agent'lar için trafik akışını "düzgünleştiren" bir tampon bölge oluşturdu.
- Bu hibrit yapı kurulduktan sonra yapılan 200 iterasyonluk ekstra fine-tuning süreci, sistemin kilitlenme (Gridlock) riskini %2'nin altına düşürmesini sağlamıştır.

## 5. Final Vizyonu: Digital Twin ve SUMO

Süreç sonunda elde edilen model, **SUMO (Simulation of Urban MObility)** ortamında Maltepe ağının bir yansıması olarak çalışmaktadır. Kaggle'da edinilen "zeka", SUMO'da "aksiyona" dönüştürülerek Maltepe trafiğinde seyahat süreleri minimize edilmiştir.
