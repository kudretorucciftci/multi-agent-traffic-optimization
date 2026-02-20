import os, sumolib, random

def generate_2000_vehicles(net_file, output_file, total_vehicles=2000, initial_burst=500):
    print(f"Network yükleniyor: {net_file}...")
    net = sumolib.net.readNet(net_file)
    
    # Binek araç geçebilen tüm yollar
    all_edges = [e.getID() for e in net.getEdges() if e.allows("passenger")]
    
    # Trafik ışıklı kavşaklar (Ajanların olduğu yerler)
    central_edges = []
    for edge in net.getEdges():
        if edge.allows("passenger"):
            to_node = edge.getToNode()
            if to_node.getType() == "traffic_light" or edge.getLaneNumber() >= 2:
                central_edges.append(edge.getID())
    
    if not central_edges:
        central_edges = all_edges

    print(f"Senaryo Oluşturuluyor: Toplam={total_vehicles}, Başlangıç Yoğunluğu={initial_burst}")
    with open(output_file, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
        
        # Araç Tipi Tanımı
        f.write('    <vType id="car" accel="2.6" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="50" guiShape="passenger" color="1,1,0"/>\n')
        
        # 1. BAŞLANGIÇ PATLAMASI (Saniye 0)
        for i in range(initial_burst):
            v_id = f"veh_peak_{i}"
            depart = 0.00
            from_edge = random.choice(central_edges)
            to_edge = random.choice(all_edges)
            while to_edge == from_edge:
                to_edge = random.choice(all_edges)
            f.write(f'    <trip id="{v_id}" type="car" depart="{depart:.2f}" from="{from_edge}" to="{to_edge}"/>\n')
        
        # 2. SÜREKLİ AKIŞ: Geri kalan araçlar ilk 200 saniye içinde dağıtılsın
        for i in range(total_vehicles - initial_burst):
            v_id = f"veh_flow_{i}"
            depart = random.uniform(0.1, 200.0)
            from_edge = random.choice(all_edges)
            to_edge = random.choice(all_edges)
            while to_edge == from_edge:
                to_edge = random.choice(all_edges)
            f.write(f'    <trip id="{v_id}" type="car" depart="{depart:.2f}" from="{from_edge}" to="{to_edge}"/>\n')
        
        f.write('</routes>\n')
    print(f"✅ {output_file} başarıyla oluşturuldu: {total_vehicles} araç.")

if __name__ == "__main__":
    generate_2000_vehicles("maltepe.net.xml", "maltepe.rou.xml")
