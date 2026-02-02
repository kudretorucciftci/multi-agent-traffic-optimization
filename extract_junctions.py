import xml.etree.ElementTree as ET
import sys

try:
    tree = ET.parse('maltepe.net.xml')
    root = tree.getroot()

    traffic_light_junction_ids = []
    for junction in root.findall('junction'):
        if junction.get('type') == 'traffic_light':
            traffic_light_junction_ids.append(junction.get('id'))

    for junction_id in traffic_light_junction_ids:
        print(junction_id)

except FileNotFoundError:
    print("Hata: maltepe.net.xml dosyası bulunamadı.")
except ET.ParseError as e:
    print(f"Hata: XML ayrıştırma hatası: {e}")
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
