import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

def anlasilir_kiyaslama():
    eski_metrics = "training_metrics.csv"
    yeni_metrics = "gnn_hybrid_metrics.csv"
    output_img = "c:/Users/Lenovo/Desktop/rl-multi-agent-traffic-control/run/anlasilir_performans_ozeti.png"
    
    # 1. VERİLERİ ÇEK VE HAZIRLA
    try:
        df_eski = pd.read_csv(eski_metrics).dropna(subset=['Egitim Ort. Odul'])
        df_yeni = pd.read_csv(yeni_metrics).dropna(subset=['Reward'])
        
        # Sütun isimlerini eşitleyelm
        v_eski = df_eski['Egitim Ort. Odul'].values
        v_yeni = df_yeni['Reward'].values
        
        # VERİMLİLİK SKORUNA DÖNÜŞTÜR (0-100 ARASI)
        # En kötü değer 0, en iyi (0 noktası) 100 olacak şekilde ölçekle
        min_val = min(v_eski.min(), v_yeni.min())
        def scale(val):
            return ((val - min_val) / (0 - min_val)) * 100

        skor_eski = scale(v_eski)
        skor_yeni = scale(v_yeni)
        
    except Exception as e:
        print(f"Hata: Veriler işlenemedi: {e}")
        return

    # 2. GÖRSELLEŞTİRME (Dashbord Tasarımı)
    fig = plt.figure(figsize=(16, 10))
    grid = plt.GridSpec(2, 2, wspace=0.3, hspace=0.3)
    
    # A. SOL PANEL: BAŞARI SKORU (BAR CHART)
    ax1 = fig.add_subplot(grid[0, 0])
    avg_eski = np.mean(skor_eski)
    avg_yeni = np.mean(skor_yeni)
    
    colors = ['#e74c3c', '#2ecc71']
    bars = ax1.bar(['Eski Sistem\n(Standart)', 'Yeni Hibrit GNN\n(Akilli)'], [avg_eski, avg_yeni], color=colors, width=0.6)
    ax1.set_title('Trafik Akis Verimliligi (0-100 Skor)', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, 110)
    
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 2, f'%{height:.1f}', ha='center', va='bottom', fontsize=15, fontweight='bold')

    # B. SAĞ PANEL: KARARLILIK ANALİZİ (BOX PLOT)
    # Bu grafik, trafiğin ne kadar "güvenli" olduğunu gösterir. Dar kutu = daha güvenli.
    ax2 = fig.add_subplot(grid[0, 1])
    bp = ax2.boxplot([skor_eski, skor_yeni], patch_artist=True, labels=['Eski Sistem', 'Yeni Hibrit'])
    
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    
    ax2.set_title('Sistem Kararliligi (Yüksek olan daha iyi)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Verimlilik Skoru')

    # C. ALT PANEL: ZAMANSAL KAZANIM (AREA CHART)
    ax3 = fig.add_subplot(grid[1, :])
    
    # Verileri ortak bir boyuta getirelim (Görsel kıyas için ilk 100 iterasyon)
    limit = min(len(skor_eski), len(skor_yeni))
    x = np.arange(limit)
    
    ax3.fill_between(x, skor_eski[:limit], label='Eski Sistem Kapasitesi', color='#e74c3c', alpha=0.2)
    ax3.plot(x, skor_eski[:limit], color='#e74c3c', linewidth=1)
    
    ax3.fill_between(x, skor_yeni[:limit], label='Yeni GNN Hibrit Kapasitesi', color='#2ecc71', alpha=0.3)
    ax3.plot(x, skor_yeni[:limit], color='#2ecc71', linewidth=2)
    
    ax3.set_title('Zaman Icinde Kazanilan Trafik Kapasitesi', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Egitim Günü / Iterasyon')
    ax3.set_ylabel('Sistem Gücü %')
    ax3.legend(loc='upper left')

    # ANA BAŞLIK VE ÖZET
    fark = avg_yeni - avg_eski
    kat_artisi = avg_yeni / max(avg_eski, 1)
    
    plt.suptitle(f'PERFORMANS KATLANMASI: Yeni Sistem %{fark:.1f} Daha Basarili!\n'
                 f'(Trafik Yönetim Gücü {kat_artisi:.1f} Katina Cikarildi)', 
                 fontsize=18, fontweight='bold', color='#2c3e50', y=0.98)

    plt.savefig(output_img, dpi=120, bbox_inches='tight')
    plt.close()
    
    print(f"\n✅ Anlasilir rapor kaydedildi: {output_img}")
    print(f"🚀 Özet: Yeni sistem eski sistemi tam {kat_artisi:.1f} kat geride birakti!")

if __name__ == "__main__":
    anlasilir_kiyaslama()
