import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import ndimage
from stable_baselines3 import PPO

# SUMO yolu ayarlama
os.environ["SUMO_HOME"] = r"C:\Program Files (x86)\Eclipse\Sumo"
tools = os.path.join(os.environ["SUMO_HOME"], "tools")
sys.path.append(tools)

# Trafik ortamını içe aktar
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'train'))
from trafik_isiklari_drl import TrafikIsigiOrtami, SUMO_AVAILABLE

def create_traffic_visualization(bekleme_sureleri, arac_sayilari, oduller):
    """Modern trafik görselleştirmesi oluşturur"""
    plt.close('all')
    fig = plt.figure(figsize=(16, 12), facecolor='#0D1117')
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.2)
    # Renk paleti
    colors = {'red': '#FF3366', 'green': '#00FF88', 'blue': '#00D9FF'}
    x = np.arange(len(bekleme_sureleri))
    # 1. Bekleme Süresi Grafiği
    ax1 = fig.add_subplot(gs[0, :])
    ax1.set_facecolor('#161B22')
    y = np.array(bekleme_sureleri)
    y_smooth = ndimage.gaussian_filter1d(y, sigma=2)

    ax1.plot(x, y_smooth, color=colors['red'], linewidth=3, alpha=0.8)
    ax1.fill_between(x, 0, y_smooth, alpha=0.3, color=colors['red'])
    
    ax1.set_title('ORTALAMA BEKLEME SÜRESİ', fontsize=16, fontweight='bold', color='#FF3366')
    ax1.set_ylabel('Süre (saniye)', fontsize=12, color='white')
    ax1.grid(True, alpha=0.3, color='gray')
    # İstatistik kutusu
    stats_text = f'Min: {np.min(y):.1f}s\nMax: {np.max(y):.1f}s\nOrt: {np.mean(y):.1f}s'
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
            color='white')
    
    # 2. Araç Sayısı Grafiği
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor('#161B22')
    y2 = np.array(arac_sayilari)
    y2_smooth = ndimage.gaussian_filter1d(y2, sigma=2)
    ax2.plot(x, y2_smooth, color=colors['green'], linewidth=3)
    ax2.fill_between(x, 0, y2_smooth, alpha=0.3, color=colors['green'])
    ax2.set_title('ARAÇ SAYISI', fontsize=14, color=colors['green'])
    ax2.set_ylabel('Araç Adedi', color='white')
    ax2.grid(True, alpha=0.3, color='gray')
    # 3. Ödül Grafiği
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.set_facecolor('#161B22')
    
    y3 = np.array(oduller)
    y3_smooth = ndimage.gaussian_filter1d(y3, sigma=2)
    
    ax3.plot(x, y3_smooth, color=colors['blue'], linewidth=3)
    ax3.fill_between(x, 0, y3_smooth, alpha=0.3, color=colors['blue'])
    ax3.set_title('ÖDÜL', fontsize=14, color=colors['blue'])
    ax3.set_ylabel('Ödül Değeri', color='white')
    ax3.grid(True, alpha=0.3, color='gray')
    
    # 4. Performans Özeti
    ax4 = fig.add_subplot(gs[2, :])
    ax4.set_facecolor('#161B22')
    ax4.axis('off')
    # Performans metrikleri
    avg_wait = np.mean(bekleme_sureleri)
    avg_cars = np.mean(arac_sayilari)
    total_reward = np.sum(oduller)
    summary_text = f"""
    📊 PERFORMANS ÖZETİ
    🕐 Ortalama Bekleme: {avg_wait:.2f} saniye
    🚗 Ortalama Araç: {avg_cars:.1f} adet
    🎯 Toplam Ödül: {total_reward:.2f}
    📈 Ortalama Ödül: {np.mean(oduller):.4f}
    """
    ax4.text(0.5, 0.5, summary_text, transform=ax4.transAxes, 
            fontsize=14, ha='center', va='center', color='white',
            bbox=dict(boxstyle='round', facecolor='#21262D', alpha=0.8))
    
    plt.tight_layout()
    return fig

def update_progress(i, total, bekleme, arac_sayisi, odul):
    """İlerleme göstergesi günceller"""
    if i % 100 == 0:
        progress = (i + 1) / total * 100
        bar_length = 40
        filled = int(bar_length * (i + 1) / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r🔄 [{bar}] {progress:.1f}% | "
              f"Araç: {arac_sayisi:3.0f} | "
              f"Bekleme: {bekleme:6.2f}s | "
              f"Ödül: {odul:8.2f}", end="")
        
def main():
    """Ana test fonksiyonu"""
    
    # Test parametreleri
    test_adimlari = 10000
    model_dosyasi = os.path.join(os.path.dirname(__file__), "mode_trafik_isigi")
    
    print("\n" + "="*60)
    print("🚦 TRAFİK IŞIĞI KONTROL MODELİ TEST EDİLİYOR 🚦")
    print("="*60)
    
    # Model yükleme
    try:
        model = PPO.load(model_dosyasi)
        print(f"✅ Model başarıyla yüklendi: {model_dosyasi}")
    except Exception as e:
        print(f"❌ Model yüklenirken hata: {e}")
        return
    
    # Test ortamı oluşturma
    test_env = TrafikIsigiOrtami(gui=True, max_adim=test_adimlari)
    obs, _ = test_env.reset()
    
    # SUMO-GUI ayarları
    if SUMO_AVAILABLE and 'traci' in sys.modules:
        import traci
        try:
            traci.gui.setSchema("View #0", "real world")
            traci.gui.setZoom("View #0", 1000)
        except:
            pass
    
    print("🚀 SUMO-GUI ile test başlıyor...")
    print("\n🔄 Test Başlıyor...")
    
    # Veri toplama listeleri
    bekleme_sureleri = []
    arac_sayilari = []
    oduller = []
    # Test döngüsü
    try:
        for i in range(test_adimlari):
            # Model tahminı
            action, _ = model.predict(obs, deterministic=True)
            
            # Adım uygulama
            obs, reward, done, truncated, info = test_env.step(action)
            
            # Veri kaydetme
            bekleme_sureleri.append(obs[1])
            arac_sayilari.append(info.get("arac_sayisi", obs[0]))
            oduller.append(reward)
            
            # İlerleme göstergesi
            update_progress(i, test_adimlari, obs[1], obs[0], reward)
            
            if done:
                break
                
    except Exception as e:
        print(f"\nTest sırasında hata: {e}")
        print("Mevcut verilerle devam ediliyor...")
    
    test_env.close()
    
    print(f"\n\n✅ Test tamamlandı! Toplam {len(bekleme_sureleri)} adım işlendi.")
    print("="*60)
    
    # Performans özeti
    print("\n📊 PERFORMANS ÖZETİ:")
    print("-" * 30)
    print(f"🕐 Ortalama Bekleme: {np.mean(bekleme_sureleri):.2f} saniye")
    print(f"🚗 Ortalama Araç Sayısı: {np.mean(arac_sayilari):.1f}")
    print(f"🎯 Toplam Ödül: {np.sum(oduller):.2f}")
    print(f"📈 Ortalama Ödül: {np.mean(oduller):.4f}")
    print(f"📉 En Düşük Bekleme: {np.min(bekleme_sureleri):.2f} saniye")
    print(f"📈 En Yüksek Bekleme: {np.max(bekleme_sureleri):.2f} saniye")
    
    # Görselleştirme oluşturma
    print("\n📊 Görselleştirme oluşturuluyor...")
    try:
        fig = create_traffic_visualization(bekleme_sureleri, arac_sayilari, oduller)
        
        # Grafik kaydetme
        grafik_dosyasi = os.path.join(os.path.dirname(__file__), "trafik_analiz.png")
        fig.savefig(grafik_dosyasi, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"✅ Görselleştirme kaydedildi: {grafik_dosyasi}")
            
    except Exception as e:
        print(f"❌ Görselleştirme hatası: {e}")
    
    print("\n🏁 Program tamamlandı!")

if __name__ == "__main__":
    main()