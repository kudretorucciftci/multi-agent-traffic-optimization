import os
import sys
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.env_util import make_vec_env
import xml.etree.ElementTree as ET
import subprocess
import time
import warnings
from typing import Dict, Any, Tuple, List, Optional

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    warnings.warn("SUMO_HOME environment variable not set. Attempting to find SUMO installation.")
    # Fallback for common SUMO installation paths on Windows/Linux
    if sys.platform == "win32":
        sumo_path_candidates = [
            r"C:\Program Files (x86)\Eclipse\Sumo",
            r"C:\Program Files\Eclipse\Sumo"
        ]
    else:
        sumo_path_candidates = [
            "/usr/share/sumo",
            "/usr/local/share/sumo",
            "/opt/sumo"
        ]
    found_sumo = False
    for path in sumo_path_candidates:
        if os.path.exists(path):
            os.environ["SUMO_HOME"] = path
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
            print(f"SUMO_HOME set to: {path}")
            found_sumo = True
            break
    
    if not found_sumo:
        warnings.warn("Could not find SUMO installation. Virtual simulation will be used.")

SUMO_AVAILABLE = False
try:
    if 'SUMO_HOME' in os.environ:
        import traci
        import sumolib
        SUMO_AVAILABLE = True
    else:
        warnings.warn("SUMO_HOME environment variable is still not defined. Virtual simulation will be used.")
except ImportError:
    warnings.warn("SUMO packages (traci, sumolib) could not be loaded. Virtual simulation will be used.")

def sumo_dosyalarini_olustur():
    """
    SUMO simülasyonu için gerekli dosyaları kontrol eder ve kullanır.
    """
    print("SUMO dosyaları kontrol ediliyor...")
    
    # Dosya yollarını belirle
    import os
    sumo_files_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sumo_files")
    network_file = os.path.join(sumo_files_dir, "network.net.xml")
    routes_file = os.path.join(sumo_files_dir, "routes.rou.xml")
    config_file = os.path.join(sumo_files_dir, "sumo.sumocfg")
    
    # Dosyaların varlığını kontrol et
    if os.path.exists(network_file) and os.path.exists(routes_file) and os.path.exists(config_file):
        print("SUMO dosyaları mevcut, mevcut dosyalar kullanılacak.")
        return
    else:
        print("UYARI: SUMO dosyaları bulunamadı! Lütfen sumo_files klasöründe gerekli dosyaların varlığını kontrol edin.")
        print(f"Gerekli dosyalar: {network_file}, {routes_file}, {config_file}")
        return

# Trafik ışığı kontrolü için Gym ortamı
class TrafikIsigiOrtami(gym.Env):
    """
    Trafik ışığı kontrolü için OpenAI Gym uyumlu ortam.
    Bu ortam, SUMO trafik simülasyonunu kullanarak trafik ışıklarını kontrol etmeyi öğrenir.
    SUMO mevcut değilse, basit bir sanal simülasyon kullanır.
    """
    metadata = {"render_modes": ["human"]}
    
    def __init__(self, gui=False, max_adim=3600, render_mode=None):
        super(TrafikIsigiOrtami, self).__init__()
        
        self.max_adim = max_adim  # Maksimum simülasyon adımı
        self.gui = gui  # GUI modunu etkinleştir/devre dışı bırak
        self.kavsaklar = ["13370398382"]  # Kontrol edilecek kavşak ID'leri
        self.faz_suresi = 10  # Her fazın minimum süresi (saniye)
        self.mevcut_adim = 0  # Mevcut simülasyon adımı
        self.sumo_baglantisi = None  # SUMO bağlantısı
        self.render_mode = render_mode
        self.use_virtual_sim = not SUMO_AVAILABLE
        
        # Sanal simülasyon için değişkenler
        self.virtual_vehicles = 0
        self.virtual_waiting_time = 0
        self.virtual_phase = 0
        self.virtual_phase_time = 0
        
        # Aksiyon uzayı: Her kavşak için faz değiştir (0) veya değiştirme (1)
        self.action_space = spaces.Discrete(2)
        
        # Gözlem uzayı: [araç_sayısı, ortalama_bekleme_süresi, mevcut_faz, faz_süresi]
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0]), 
            high=np.array([100, 1000, 2, 100]),
            dtype=np.float32
        )
        
        # İstatistikler
        self.istatistikler = {
            "toplam_bekleme_suresi": [],
            "ortalama_bekleme_suresi": [],
            "toplam_arac_sayisi": []
        }
        
        # SUMO'yu başlat veya sanal simülasyonu hazırla
        self._sumo_baslat()
    def _sumo_baslat(self):
        """
        SUMO simülasyonunu başlatır ve bağlantı kurar veya sanal simülasyonu hazırlar.
        """
        if self.use_virtual_sim:
            print("Sanal trafik simülasyonu başlatılıyor...")
            self._virtual_sim_reset()
            return
            
        try:
            # SUMO dosyalarının bulunduğu dizini belirle
            import os
            
            # The .sumocfg file is now expected in the project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_file_path = os.path.join(project_root, "maltepe.sumocfg") # Use the new config file
            
            if self.gui:
                sumo_binary = "sumo-gui"
                sumo_cmd = [sumo_binary, "-c", config_file_path, "--start", "--quit-on-end"]
            else:
                sumo_binary = "sumo"
                sumo_cmd = [sumo_binary, "-c", config_file_path, "--no-step-log", "--no-warnings"]
            
            traci.start(sumo_cmd)
            print("SUMO bağlantısı kuruldu.")
            
        except Exception as e:
            warnings.warn(f"SUMO başlatılırken hata oluştu: {e}. Sanal simülasyon kullanılacak.")
            self.use_virtual_sim = True
            self._virtual_sim_reset()

    def _virtual_sim_reset(self):
        """
        Sanal simülasyonu sıfırlar.
        """
        self.virtual_vehicles = 0
        self.virtual_waiting_time = 0
        self.virtual_phase = 0
        self.virtual_phase_time = 0
    def _virtual_sim_step(self, action):
        """
        Sanal simülasyonun bir adımını ilerletir.
        """
        # Basit bir sanal simülasyon mantığı
        # Araç sayısı ve bekleme süresi rastgele değişir
        self.virtual_vehicles = max(0, self.virtual_vehicles + np.random.randint(-2, 3))
        self.virtual_waiting_time = max(0, self.virtual_waiting_time + np.random.uniform(-1, 1))
        # Faz değişimi
        if action == 1: # Fazı değiştir
            self.virtual_phase = (self.virtual_phase + 1) % 4 # 4 faz olduğunu varsayalım
            self.virtual_phase_time = 0
        else:
            self.virtual_phase_time += 1
            
        # Gözlem: [araç_sayısı, ortalama_bekleme_süresi, mevcut_faz, faz_süresi]
        return np.array([
            self.virtual_vehicles,
            self.virtual_waiting_time,
            self.virtual_phase,
            self.virtual_phase_time
        ], dtype=np.float32)

    def _gozlem_al(self) -> np.ndarray:
        """
        Simülasyondan gözlem alır (araç sayısı, bekleme süresi, mevcut faz).
        """
        if self.use_virtual_sim:
            return np.array([
                self.virtual_vehicles,
                self.virtual_waiting_time,
                self.virtual_phase,
                self.virtual_phase_time
            ], dtype=np.float32)

        # Toplam araç sayısı ve bekleme süresi
        toplam_arac_sayisi = traci.vehicle.getIDCount()
        toplam_bekleme_suresi = 0
        for arac_id in traci.vehicle.getIDList():
            toplam_bekleme_suresi += traci.vehicle.getAccumulatedWaitingTime(arac_id)
        
        ortalama_bekleme_suresi = 0
        if toplam_arac_sayisi > 0:
            ortalama_bekleme_suresi = toplam_bekleme_suresi / toplam_arac_sayisi
            
        # Mevcut trafik ışığı fazı
        mevcut_faz = traci.trafficlight.getPhase(self.kavsaklar[0]) # Sadece J1 kavşağı için
        faz_suresi = traci.trafficlight.getPhaseDuration(self.kavsaklar[0])
        
        return np.array([
            toplam_arac_sayisi,
            ortalama_bekleme_suresi,
            mevcut_faz,
            faz_suresi
        ], dtype=np.float32)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Ortamda bir adım ilerler.
        """
        if self.use_virtual_sim:
            gozlem = self._virtual_sim_step(action)
            reward = 0.1 # Sanal simülasyonda basit bir ödül
            done = self.mevcut_adim >= self.max_adim
            self.mevcut_adim += 1
            return gozlem, reward, done, False, {}

        # Önceki gözlemi kaydet
        onceki_gozlem = self._gozlem_al()
        
        # Aksiyonu uygula
        if action == 1:  # Fazı değiştir
            traci.trafficlight.setPhase(self.kavsaklar[0], (traci.trafficlight.getPhase(self.kavsaklar[0]) + 1) % 3) # 3 faz olduğunu varsayalım
            # Faz değişiminden sonra belirli bir süre bekle (sarı ışık süresi gibi)
            for _ in range(self.faz_suresi):
                traci.simulationStep()
                self.mevcut_adim += 1
        else:  # Fazı değiştirmeden devam et
            traci.simulationStep()
            self.mevcut_adim += 1
            
        # Yeni gözlemi al
        gozlem = self._gozlem_al()
        
        # Ödülü hesapla (bekleme süresinin azalması ödüllendirilir, kuyruk uzunluğu cezalandırılır)
        onceki_bekleme = onceki_gozlem[1]  # Önceki ortalama bekleme süresi
        mevcut_bekleme = gozlem[1]  # Mevcut ortalama bekleme süresi
        
        # Temel ödül: bekleme süresinin azalması
        reward = onceki_bekleme - mevcut_bekleme
        
        # Ek ödül: kuyruk uzunluğunu azaltma (araç sayısı)
        current_queue_length = gozlem[0] # araç sayısı
        if current_queue_length > 5: # 5'ten fazla araç varsa ceza ver
            reward -= (current_queue_length * 0.01) # küçük ceza değeri

        # Çok yüksek bekleme süresi için ek ceza
        if mevcut_bekleme > 100:
            reward -= 1.0
        odul = reward
        # Simülasyonun bitip bitmediğini kontrol et
        bitti = self.mevcut_adim >= self.max_adim
        
        # Bilgi sözlüğü (isteğe bağlı)
        bilgi = {}
        
        # İstatistikleri güncelle
        if not self.use_virtual_sim:
            toplam_bekleme_suresi = sum(traci.vehicle.getAccumulatedWaitingTime(arac_id) for arac_id in traci.vehicle.getIDList())
            toplam_arac_sayisi = traci.vehicle.getIDCount()
            ortalama_bekleme_suresi = toplam_bekleme_suresi / max(1, toplam_arac_sayisi)
            self.istatistikler["toplam_bekleme_suresi"].append(toplam_bekleme_suresi)
            self.istatistikler["ortalama_bekleme_suresi"].append(ortalama_bekleme_suresi)
            self.istatistikler["toplam_arac_sayisi"].append(toplam_arac_sayisi)
        
        return gozlem, odul, bitti, False, bilgi

    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Ortamı sıfırlar.
        """
        super().reset(seed=seed)
        self.mevcut_adim = 0
        
        # İstatistikleri sıfırla
        self.istatistikler = {
            "toplam_bekleme_suresi": [],
            "ortalama_bekleme_suresi": [],
            "toplam_arac_sayisi": []
        }
        if not self.use_virtual_sim:
            # SUMO simülasyonunu yeniden başlat
            try:
                if 'traci' in globals() and hasattr(traci, 'close'):
                    traci.close()
            except Exception as e:
                print(f"SUMO bağlantısı kapatılırken hata: {e}")
            self._sumo_baslat()
            # Başlangıç gözlemini al
            gozlem = self._gozlem_al()
        else:
            self._virtual_sim_reset()
            gozlem = self._gozlem_al()
            
        bilgi = {}
        return gozlem, bilgi

    def render(self):
        """
        Ortamı görselleştirir (SUMO GUI).
        """
        # SUMO GUI zaten açıksa bir şey yapma
        pass

    def close(self):
        """
        Ortamı kapatır.
        """
        if not self.use_virtual_sim and hasattr(traci, 'close'):
            try:
                traci.close()
                if self.sumo_baglantisi:
                    self.sumo_baglantisi.terminate()
                    self.sumo_baglantisi.wait() # Sürecin tamamen kapanmasını bekle
                    print("SUMO simülasyonu kapatıldı.")
            except Exception as e:
                print(f"SUMO kapatılırken hata oluştu: {e}")

# Eğitim ve test fonksiyonları
def modeli_egit(model_adi="trafik_isigi_ppo_model", toplam_adim=10000):
    # تأكد من أن المسار موجود
    import os
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run")
    os.makedirs(model_dir, exist_ok=True)
    """
    PPO modelini eğitir.
    """
    print(f"\n{toplam_adim} adımlık PPO modeli eğitimi başlatılıyor...")

    # Ortamı oluştur
    env = make_vec_env(TrafikIsigiOrtami, n_envs=1, env_kwargs={"gui": False, "max_adim": 1000})
    
    # PPO modelini tanımla
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./ppo_trafik_isigi_tensorboard/")
    
    # Modeli eğit
    model.learn(total_timesteps=toplam_adim)
    
    # Modeli kaydet
    model_save_path = os.path.join(model_dir, model_adi)
    model.save(model_save_path)
    print(f"Model '{model_save_path}' olarak kaydedildi.")

def modeli_test_et(model_adi="trafik_isigi_ppo_model"):
    # تأكد من أن المسار موجود
    import os
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run")
    model_path = os.path.join(model_dir, model_adi)
    """
    Eğitilmiş PPO modelini test eder ve sonuçları görselleştirir.
    """
    print("\nEğitilmiş model test ediliyor...")
    
    # Eğitilmiş modeli yükle
    model = PPO.load(model_path)
    
    # Test ortamını oluştur (GUI açık)
    test_env = TrafikIsigiOrtami(gui=True, max_adim=3600) # Daha uzun bir simülasyon süresi
    
    # Gözlem ve istatistik listeleri
    gozlem, _ = test_env.reset()
    bekleme_sureleri = []
    arac_sayilari = []
    oduller = []
    # Simülasyonu çalıştır
    while test_env.mevcut_adim < test_env.max_adim:
        aksiyon, _states = model.predict(gozlem, deterministic=True)
        gozlem, odul, bitti, _, _ = test_env.step(aksiyon)
        
        # İstatistikleri kaydet
        if test_env.istatistikler["ortalama_bekleme_suresi"]:
            bekleme_sureleri.append(test_env.istatistikler["ortalama_bekleme_suresi"][-1])
        if test_env.istatistikler["toplam_arac_sayisi"]:
            arac_sayilari.append(test_env.istatistikler["toplam_arac_sayisi"][-1])
        oduller.append(odul)
        
        if bitti:
            break
            
    # Test ortamını kapat
    test_env.close()
    
    
    
    print("\nTest tamamlandı.")

# Ana çalıştırma bloğu
if __name__ == "__main__":
    # SUMO dosyalarını oluştur
    sumo_dosyalarini_olustur()
    
    # Modeli eğit
    modeli_egit(toplam_adim=10000) # Daha uzun eğitim süresi
    
    # Eğitilmiş modeli test et
    modeli_test_et()

