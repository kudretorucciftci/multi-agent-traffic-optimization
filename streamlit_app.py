import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from PIL import Image

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="Multi-Agent Trafik Optimizasyonu",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Özel CSS ile Premium Görünüm
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stHeader {
        color: #00d4ff;
    }
    div[data-testid="stSidebarNav"] {
        padding-top: 20px;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: 600;
    }
    .highlight {
        color: #00d4ff;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Veri Yükleme Fonksiyonları
@st.cache_data
def load_data():
    baseline = pd.read_csv("baseline_5000_metrics.csv")
    ai_model = pd.read_csv("mega_v4_eval_metrics_5000.csv")
    # Sütun isimlerini normalize et
    ai_model = ai_model.rename(columns={
        "total_waiting_time": "waiting_time",
        "total_halting_vehicles": "halting",
        "mean_speed": "speed"
    })
    return baseline, ai_model

# Sidebar / Navigasyon
with st.sidebar:
    if os.path.exists("assets/tls_icon.png"):
        st.image("assets/tls_icon.png", width=100)
    st.title("Trafik AI Kontrol Paneli")
    st.markdown("---")
    menu = st.radio(
        "Gezinti",
        ["🏠 Ana Sayfa", "📊 Performans Analizi", "🎬 Simülasyon Galerisi", "🧠 Teknik Detaylar"]
    )
    st.markdown("---")
    st.info("Bu proje Çoklu-Ajanlı Takviyeli Öğrenme (MARL) ve GNN kullanılarak geliştirilmiştir.")

# --- ANA SAYFA ---
if menu == "🏠 Ana Sayfa":
    if os.path.exists("assets/project_banner.png"):
        st.image("assets/project_banner.png", use_container_width=True)
    
    st.title("🚦 Akıllı Trafik Yönetim Sistemi")
    st.markdown("""
    ### Geleceğin Şehirleri İçin Yapay Zeka
    Bu proje, İstanbul'un Maltepe bölgesindeki trafik akışını optimize etmek için **Çoklu-Ajanlı Takviyeli Öğrenme (Multi-Agent RL)** 
    ve **Graf Sinir Ağları (GNN)** teknolojilerini birleştirir.
    
    #### 🚀 Temel Özellikler:
    - **Dinamik Trafik Işıkları (TLS):** Trafik yoğunluğuna göre anlık faz değişimi.
    - **Değişken Hız Sınırları (VSL):** Darboğazları önlemek için akıllı hız yönetimi.
    - **GNN Entegrasyonu:** Kavşaklar arası mekansal ilişkileri anlayan mimari.
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ajan Sayısı", "149", "TLS + VSL")
    with col2:
        st.metric("İyileştirme Oranı", "~%30", "Bekleme Süresi")
    with col3:
        st.metric("Simülasyon Motoru", "SUMO", "Real-time")

# --- PERFORMANS ANALİZİ ---
elif menu == "📊 Performans Analizi":
    st.header("📈 Model Performans Karşılaştırması")
    
    try:
        baseline, ai_model = load_data()
        
        # Filtreleme (Adım aralığı)
        step_range = st.slider("Simülasyon Adımı Aralığı", 0, 3000, (0, 1000))
        df_b = baseline[(baseline['step'] >= step_range[0]) & (baseline['step'] <= step_range[1])]
        df_a = ai_model[(ai_model['step'] >= step_range[0]) & (ai_model['step'] <= step_range[1])]

        tab1, tab2, tab3 = st.tabs(["⏳ Bekleme Süresi", "🚗 Ortalama Hız", "🛑 Duraklayan Araçlar"])

        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_b['step'], y=df_b['waiting_time'], name="Geleneksel (Baseline)", line=dict(color='gray', dash='dash')))
            fig.add_trace(go.Scatter(x=df_a['step'], y=df_a['waiting_time'], name="Mega v4 (AI)", line=dict(color='#00d4ff', width=3)))
            fig.update_layout(title="Kümülatif Bekleme Süresi Karşılaştırması", template="plotly_dark", xaxis_title="Adım", yaxis_title="Saniye")
            st.plotly_chart(fig, use_container_width=True)
            st.write("**Not:** AI modelimiz bekleme sürelerini belirgin şekilde stabilize etmektedir.")

        with tab2:
            fig = px.line(title="Ortalama Hız Değişimi", template="plotly_dark")
            fig.add_scatter(x=df_b['step'], y=df_b['speed'], name="Baseline", line=dict(color='gray'))
            fig.add_scatter(x=df_a['step'], y=df_a['speed'], name="Mega v4", line=dict(color='#00ff88'))
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            fig = px.bar(template="plotly_dark", barmode='group')
            # Histogram/Bar gösterimi için veriyi küçültelim
            df_comp = pd.DataFrame({
                "Model": ["Baseline", "AI"],
                "Ort. Bekleme": [df_b['waiting_time'].mean(), df_a['waiting_time'].mean()],
                "Maks. Halting": [df_b['halting'].max(), df_a['halting'].max()]
            })
            st.table(df_comp)

    except Exception as e:
        st.error(f"Veri yüklenirken hata oluştu: {e}")
        st.info("Lütfen CSV dosyalarının ana dizinde olduğundan emin olun.")

# --- SİMÜLASYON GALERİSİ ---
elif menu == "🎬 Simülasyon Galerisi":
    st.header("📽️ Simülasyon Çıktıları")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Bölgesel Trafik Akışı")
        if os.path.exists("assets/simulation.gif"):
            st.image("assets/simulation.gif", caption="AI Kontrollü Maltepe Ağı")
        else:
            st.warning("simulation.gif bulunamadı.")
            
    with col2:
        st.subheader("Hız Sınırı (VSL) Uygulaması")
        if os.path.exists("assets/vsl_sign.png"):
            st.image("assets/vsl_sign.png", width=200)
        st.write("""
        Sistem, sadece trafik ışıklarını değil, araçların maksimum hızlarını da 
        telsiz (VSL) üzerinden kontrol ederek şok dalgalarını önler.
        """)

    st.markdown("---")
    st.subheader("Tam Bölge Analizi")
    if os.path.exists("assets/ai_vs_baseline_comparison.png"):
        st.image("assets/ai_vs_baseline_comparison.png", caption="Baseline vs AI Kapsamlı Rapor")

# --- TEKNİK DETAYLAR ---
elif menu == "🧠 Teknik Detaylar":
    st.header("🧬 Sistemin Arkasındaki Teknoloji")
    
    with st.expander("🤖 RL Ajan Yapısı"):
        st.write("""
        - **Gözlem (Observation):** Kavşaktaki araç sayıları, ortalama hızlar ve komşu kavşakların durumu.
        - **Aksiyon (Action):** Yeşil ışık süresi artırma/azaltma veya faz değiştirme.
        - **Ödül (Reward):** Toplam bekleme süresindeki azalma ve dur-kalk trafiğin minimize edilmesi.
        """)
        
    with st.expander("🕸️ Graf Sinir Ağları (GNN)"):
        st.write("""
        Trafik doğası gereği bir graf yapısına sahiptir. GNN mimarimiz:
        - Kavşakları **düğüm (node)**, yolları **kenar (edge)** olarak temsil eder.
        - Mesaj iletimi (Message Passing) ile bir kavşaktaki yoğunluğun diğerlerini nasıl etkilediğini öğrenir.
        """)
        
    st.image("assets/tls_icon.png" if os.path.exists("assets/tls_icon.png") else "", width=100)
    st.latex(r"R = - \sum (waiting\_time + \alpha \cdot halting\_vehicles)")

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Trafik AI Projesi | SUMO & RLlib")
