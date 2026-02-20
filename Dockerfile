# 1. Python ve Ubuntu tabanlı ana imaj
FROM python:3.12-slim

# 2. Sistem bağımlılıklarını ve SUMO'yu kur
RUN apt-get update && apt-get install -y \
    sumo \
    sumo-tools \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. SUMO ortam değişkenlerini ayarla
ENV SUMO_HOME=/usr/share/sumo

# 4. Çalışma dizinini oluştur
WORKDIR /app

# 5. Gerekli dosyaları kopyala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Tüm proje dosyalarını kopyala
COPY . .

# 7. Streamlit'i dış dünyaya aç
EXPOSE 8501

# 8. Uygulamayı başlat
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
