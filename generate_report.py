import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_report():
    file_path = "mega_v4_full_drain_5000.csv"
    if not os.path.exists(file_path):
        print(f"Hata: {file_path} bulunamadı.")
        return

    df = pd.read_csv(file_path)
    
    # Grafik oluşturma
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Mega v4 Model: 5000 Araç Tam Tahliye Analizi", fontsize=16)

    # 1. Kalan Araç Sayısı
    axes[0, 0].plot(df['step'], df['active_vehicles'], color='blue')
    axes[0, 0].set_title("Haritadaki Aktif Araç Sayısı")
    axes[0, 0].set_xlabel("Adım (Saniye)")
    axes[0, 0].set_ylabel("Araç Sayısı")
    axes[0, 0].grid(True)

    # 2. Bekleme Süresi
    axes[0, 1].plot(df['step'], df['waiting_time'], color='red')
    axes[0, 1].set_title("Toplam Bekleme Süresi")
    axes[0, 1].set_xlabel("Adım (Saniye)")
    axes[0, 1].set_ylabel("Saniye")
    axes[0, 1].grid(True)

    # 3. Ortalama Hız
    axes[1, 0].plot(df['step'], df['speed'], color='green')
    axes[1, 0].set_title("Sistem Genel Ortalama Hız")
    axes[1, 0].set_xlabel("Adım (Saniye)")
    axes[1, 0].set_ylabel("m/s")
    axes[1, 0].grid(True)

    # 4. Toplam Ödül (Reward)
    axes[1, 1].plot(df['step'], df['reward'], color='purple')
    axes[1, 1].set_title("Anlık Toplam Ödül (Reward)")
    axes[1, 1].set_xlabel("Adım (Saniye)")
    axes[1, 1].set_ylabel("Puan")
    axes[1, 1].grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    report_image = "mega_v4_report.png"
    plt.savefig(report_image)
    print(f"✅ Rapor grafiği oluşturuldu: {report_image}")

    # Özet Veriler
    total_steps = df['step'].max()
    avg_waiting = df['waiting_time'].mean()
    vehicle_per_wait = (df['waiting_time'].sum() / 5000)
    max_queue = df['halting'].max()
    avg_speed_kph = df['speed'].mean() * 3.6

    print("\n" + "="*40)
    print("🚦 NİHAİ SİMÜLASYON RAPORU (5000 Araç)")
    print("="*40)
    print(f"🔹 Toplam Tahliye Süresi: {total_steps} saniye (~{total_steps/60:.2f} dakika)")
    print(f"🔹 Araç Başına Ortalama Bekleme: {vehicle_per_wait:.2f} saniye")
    print(f"🔹 Ortalama Sistem Hızı: {avg_speed_kph:.2f} km/h")
    print(f"🔹 Maksimum Anlık Kuyruk: {max_queue} araç")
    print(f"🔹 Toplam Toplanan Ödül: {df['reward'].sum():.0f} puan")
    print("="*40)

if __name__ == "__main__":
    generate_report()
