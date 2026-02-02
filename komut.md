# Temel Komutlar

## Çalışma Ortamı
```powershell
# Sanal ortamı aktive et
.\robot_env\Scripts\activate
```

## Eğitim (Training)
```powershell
# Çoklu ajan eğitimini başlat
python train/train_multi_agent.py
```

## Test ve Görselleştirme
```powershell
# Eğitilmiş modeli GUI ile çalıştır
python run/run_multi_agent_model.py
```

## Metrik İzleme
```powershell
# Tensorboard ile eğitim sürecini takip et
tensorboard --logdir ppo_trafik_isigi_tensorboard
```