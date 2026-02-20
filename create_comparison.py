import pandas as pd
import matplotlib.pyplot as plt
import os

def create_comparison_report():
    print("📊 AI vs Baseline Karşılaştırma Raporu Oluşturuluyor...")
    
    # Dosya yolları
    ai_file = "mega_v4_full_drain_5000.csv"
    baseline_file = "baseline_5000_metrics.csv"
    
    if not os.path.exists(ai_file) or not os.path.exists(baseline_file):
        print("❌ Hata: Gerekli CSV dosyaları bulunamadı!")
        return

    # Verileri yükle
    df_ai = pd.read_csv(ai_file)
    df_base = pd.read_csv(baseline_file)

    # Grafik oluşturma
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
    plt.subplots_adjust(hspace=0.3)

    # 1. Grafik: Bekleme Süresi Karşılaştırması
    ax1.plot(df_ai['step'], df_ai['waiting_time'], label='Mega v4 (AI)', color='green', linewidth=2)
    ax1.plot(df_base['step'], df_base['waiting_time'], label='Baseline (Zekasız)', color='red', alpha=0.6)
    ax1.set_title('Bekleme Süresi Karşılaştırması (Zeka Farkı)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Simülasyon Saniyesi (Step)')
    ax1.set_ylabel('Anlık Toplam Bekleme Süresi')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.7)

    # 2. Grafik: Haritadaki Araç Sayısı (Boşaltma Hızı)
    ax2.plot(df_ai['step'], df_ai['active_vehicles'], label='Mega v4 (AI)', color='blue', linewidth=2)
    ax2.plot(df_base['step'], df_base['active_vehicles'], label='Baseline (Zekasız)', color='orange', alpha=0.6)
    ax2.set_title('Harita Tahliye Hızı (Kalan Araç Sayısı)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Simülasyon Saniyesi (Step)')
    ax2.set_ylabel('Aktif Araç Sayısı')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.7)

    # Raporu kaydet
    report_name = "ai_vs_baseline_comparison.png"
    plt.savefig(report_name, dpi=300, bbox_inches='tight')
    print(f"✅ Rapor başarıyla oluşturuldu: {report_name}")

    # Özet İstatistikler
    print("\n--- NİHAİ ANALİZ ÖZETİ (5000 ARAÇ) ---")
    print(f"Mega v4 (AI) Bitiş Süresi: {df_ai['step'].max()} saniye")
    print(f"Zekasız (Baseline) Bitiş Süresi: {df_base['step'].max()} saniye")
    print(f"AI Zaman Kazancı: {df_base['step'].max() - df_ai['step'].max()} saniye")
    
    avg_wait_ai = df_ai['waiting_time'].mean()
    avg_wait_base = df_base['waiting_time'].mean()
    print(f"Mega v4 Ort. Bekleme: {avg_wait_ai:.2f}")
    print(f"Baseline Ort. Bekleme: {avg_wait_base:.2f}")
    print(f"Bekleme Süresindeki İyileşme: %{((avg_wait_base - avg_wait_ai) / avg_wait_base * 100):.2f}")

if __name__ == "__main__":
    create_comparison_report()
