from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader, PdfWriter
import io
import os

def create_overlay():
    packet = io.BytesIO()
    # Create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFont("Helvetica", 8)
    
    # Starting coordinates (Estimates for standard A4 centered table)
    # X coordinates for centers of columns
    x_date = 145    # 1st column (Date)
    x_hours = 310   # 2nd column (Hours)
    x_topics = 365  # 3rd column (Topics) - start of text
    
    y_start = 693   # First line of the table (y-coordinate from bottom)
    row_height = 15.35 # Height of each row
    
    dates = [
        "12.01.2026", "13.01.2026", "14.01.2026", "15.01.2026", "16.01.2026",
        "19.01.2026", "20.01.2026", "21.01.2026", "22.01.2026", "23.01.2026",
        "26.01.2026", "27.01.2026", "28.01.2026", "29.01.2026", "30.01.2026",
        "02.02.2026", "03.02.2026", "04.02.2026", "05.02.2026", "06.02.2026",
        "09.02.2026", "10.02.2026", "11.02.2026", "12.02.2026", "13.02.2026",
        "16.02.2026", "17.02.2026", "18.02.2026", "19.02.2026", "20.02.2026"
    ]
    
    # Replacing special Turkish characters with base ones to avoid PDF font encoding issues
    topics = [
        "Deep RL temelleri ve trafik optimizasyonu teorisi uzerine calisma. (Ref: Mnih, 2013)",
        "Knowledge Graph ve GNN'lerin trafik topolojisindeki etkilerinin analizi.",
        "SUMO simulasyon motoru ve TraCI API kullanimi uzerine teknik inceleme.",
        "Maltepe yol aginin SUMO formatina aktarilmasi ve kavsak konfigurasyonu.",
        "Cok ajanli sistemlerde ajan mimarisi ve politika kavramlarinin tasarimi.",
        "PettingZoo uyumlu ozel simulasyon ortaminin (multi_agent_env.py) kodlanmasi.",
        "Ajanlar icin Cok Amacli Odul Fonksiyonu (Reward) mekanizmasinin tasarimi.",
        "Gozlem Uzayi Muhendisligi: Kavsak verilerinin normalizasyonu ve matris formati.",
        "Model Gelistirme-I: MLP mimarisi ile temel PPO egitim dongusunun kurulmasi.",
        "MLP tabanli model performans analizi ve Grafik yapisina gecis karari.",
        "Knowledge Graph Modelleme-I: Trafik aginin semantik graf topolojisine donusturulmesi.",
        "Knowledge Graph Modelleme-II: Adjacency Matrix yapisinin sisteme entegrasyonu.",
        "Model Gelistirme-II (GNN): GAT katmanlarinin (gnn_model.py) PyTorch ile kodlanmasi.",
        "Hibrit Kontrol Yapisi: Trafik isigi (RL) ve VSL ajanlarinin koordinasyon tasarimi.",
        "Sistem Entegrasyonu: GNN tabanli hibrit simulasyonun kararlilik testleri.",
        "Hata Analizi: Egitimdeki sayisal kararsizlik (NaN) hatalarinin tespiti ve cozumu.",
        "Bulut Gecisi: Projenin Kaggle GPU altyapisina tasinmasi ve altyapi ayarlari.",
        "Base Training Cycle: 149 ajanli modelin Kaggle'da baslangic ogrenme sureci.",
        "Hiperparametre Optimizasyonu: LR ve entropy katsayilarinin analizi ve ayari.",
        "Sayisal Iyilestirmeler: Gradyan kirpma ile model ogrenme kararliliginin artirilmasi.",
        "Fine-Tuning Sureci-I: 1000 aractan 2000 araca gecis icin ince ayar asamasi.",
        "Stress Test Senaryolari: Dinamik rota dokumanlari uretilmesi ve test havuzu.",
        "Fine-Tuning Sureci-II (Mega v4): 5.000 araclik ekstrem senaryoda rafine egitim.",
        "Hibrit Akis Optimizasyonu: VSL ve RL ajanlari arasindaki koordinasyonun iyilestirilmesi.",
        "Checkpoint Degerlendirme: En iyi performansli model agirliklarinin secilmesi.",
        "Digital Twin Gorsellestirme: Modelin SUMO-GUI uzerinde Maltepe aginda testi.",
        "Degerlendirme (Full Drain): 5000 araclik senaryoda teknik basari verisi toplama.",
        "Karsilastirmali Analiz: RL sistemin statik sinyalizasyonla hiz/bekleme kiyaslamasi.",
        "Raporlama ve Emisyon Analizi: CO2 dususu hesaplanmasi ve rapor uretimi.",
        "Final Dokumentasyonu: Kod temizligi ve staj dokumanlarinin teknik kontrolu."
    ]
    
    for i in range(len(dates)):
        y = y_start - (i * row_height)
        can.drawString(x_date - 20, y, dates[i])
        can.drawString(x_hours, y, "9")
        can.drawString(x_topics, y, topics[i])
        
    # Bottom Summary
    can.drawString(185, 87, "30")   # Toplam Is Günü
    can.drawString(305, 87, "270")  # Toplam Saat
    
    can.save()
    packet.seek(0)
    return packet

def main():
    try:
        input_filename = "günlere göre dağılım.pdf"
        output_filename = "günlere_göre_dağılım_dolu.pdf"
        
        if not os.path.exists(input_filename):
            print(f"Hata: {input_filename} bulunamadi.")
            return

        reader = PdfReader(input_filename)
        writer = PdfWriter()
        
        overlay_packet = create_overlay()
        overlay_reader = PdfReader(overlay_packet)
        
        # Assume one page PDF
        page = reader.pages[0]
        overlay_page = overlay_reader.pages[0]
        
        page.merge_page(overlay_page)
        writer.add_page(page)
        
        with open(output_filename, "wb") as output_stream:
            writer.write(output_stream)
        
        print(f"Basarili: {output_filename} olusturuldu.")
    except Exception as e:
        print(f"Sistem Hatasi: {e}")

if __name__ == "__main__":
    main()
