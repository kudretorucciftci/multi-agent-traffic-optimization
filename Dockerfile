# Python ve Ubuntu tabanlı ana imaj
FROM python:3.12-slim

# Root yetkisiyle sistem bağımlılıklarını ve SUMO'yu kur
USER root
RUN apt-get update && apt-get install -y \
    sumo \
    sumo-tools \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# SUMO ortam değişkenlerini ayarla
ENV SUMO_HOME=/usr/share/sumo

# Hugging Face için kullanıcı oluştur (user id 1000)
RUN useradd -m -u 1000 user
WORKDIR /app

# Dosyaları kopyala ve yetkileri düzenle
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

# Kullanıcıya geçiş yap
USER user

# Streamlit'i Hugging Face'in standart portu olan 7860'a ayarla
EXPOSE 7860

# Uygulamayı başlat (Portu 7860 yaparak)
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=7860", "--server.address=0.0.0.0"]
